# @Copyright: CEA-LIST/DIASI/SIALV/LVA (2023)
# @Author: CEA-LIST/DIASI/SIALV/LVA <pixano@cea.fr>
# @License: CECILL-C
#
# This software is a collaborative computer program whose purpose is to
# generate and explore labeled data for computer vision applications.
# This software is governed by the CeCILL-C license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-C
# license as circulated by CEA, CNRS and INRIA at the following URL
#
# http://www.cecill.info

from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from fastapi_pagination.api import create_page, resolve_params
from fastapi_pagination.bases import AbstractPage, AbstractParams
from pydantic import BaseModel

from pixano.core import (
    BBox,
    CompressedRLE,
    Image,
    ImageType,
    ObjectAnnotation,
    ObjectAnnotationType,
    convert_field,
    is_image_type,
    is_list_of_object_annotation_type,
    is_number,
)
from pixano.data import Dataset
from pixano.utils import format_bbox, natural_key


class ItemFeature(BaseModel):
    """Feature

    Attributes:
        name (str): Feature name
        dtype (str): Feature dtype
        value (Any): Feature value
    """

    name: str
    dtype: str
    value: Any


ItemFeatures = list[ItemFeature]


def _create_features(item: list, schema: pa.schema) -> list[ItemFeature]:
    """Create features based on field types

    Args:
        row (list): Dataset item
        schema (pa.schema): Dataset schema

    Returns:
        list[ItemFeature]: Item as list of features
    """

    features = []

    # Iterate on fields
    for field in schema:
        # Number fields
        if is_number(field.type):
            features.append(
                ItemFeature(name=field.name, dtype="number", value=item[field.name])
            )
        # Image fields
        elif is_image_type(field.type):
            thumbnail = item[field.name].preview_url
            features.append(
                ItemFeature(name=field.name, dtype="image", value=thumbnail)
            )
        # String fields
        elif pa.types.is_string(field.type):
            features.append(
                ItemFeature(name=field.name, dtype="text", value=item[field.name])
            )

    return features


def load_items(dataset: Dataset, params: AbstractParams = None) -> AbstractPage:
    """Get items

    Args:
        dataset (Dataset): Dataset
        params (AbstractParams, optional): FastAPI params for pagination. Defaults to None.

    Returns:
        AbstractPage: List of ItemFeatures for UI (DatasetExplorer)
    """

    # Load dataset
    pa_ds = dataset.load()

    # Get page parameters
    params = resolve_params(params)
    raw_params = params.to_raw_params()
    total = pa_ds.count_rows()

    # Get page items
    start = raw_params.offset
    stop = min(raw_params.offset + raw_params.limit, total)
    if start >= stop:
        return None
    items_table = pa_ds.take(range(start, stop))

    # Create items features
    items = [_create_features(item, pa_ds.schema) for item in items_table.to_pylist()]

    return create_page(items, total=total, params=params)


def load_item_details(
    dataset: Dataset,
    item_id: str,
    media_dir: Path,
    inf_datasets: list[Dataset] = [],
) -> dict:
    """Get item details

    Args:
        dataset (Dataset): Dataset
        item_id (str): Selected item ID
        media_dir (Path): Dataset media directory
        inf_datasets (list[Dataset], optional): List of inference datasets. Defaults to [].

    Returns:
        dict: ImageDetails features for UI
    """

    # Load dataset
    pa_ds = dataset.load()

    # Get item
    scanner = pa_ds.scanner(filter=ds.field("id").isin([item_id]))
    item = scanner.to_table().to_pylist()[0]
    objects = []
    for field in pa_ds.schema:
        if field.name == "objects" or is_list_of_object_annotation_type(field.type):
            objects.extend(item[field.name])

    # Get item inference objects
    for inf_ds in inf_datasets:
        pa_inf_ds = inf_ds.load()
        inf_scanner = pa_inf_ds.scanner(filter=ds.field("id").isin([item_id]))
        inf_item = inf_scanner.to_table().to_pylist()[0]
        if inf_item is not None:
            for field in pa_inf_ds.schema:
                if field.name == "objects" or is_list_of_object_annotation_type(
                    field.type
                ):
                    objects.extend(inf_item[field.name])

    # Create features
    item_details = {
        "itemData": {
            "id": item["id"],
            "views": [],
            "features": _create_features(item, pa_ds.schema),
        },
        "itemObjects": defaultdict(lambda: defaultdict(list)),
    }

    # Iterate on view
    for field in pa_ds.schema:
        if is_image_type(field.type):
            image = item[field.name]
            image.uri_prefix = media_dir.absolute().as_uri()
            item_details["itemData"]["views"].append(
                {"id": field.name, "url": image.url}
            )

            for obj in objects:
                # Support for previous ObjectAnnotation type
                if isinstance(obj, dict):
                    # Support for previous BBox type
                    if isinstance(obj["bbox"], list):
                        obj["bbox"] = {"coords": obj["bbox"], "format": "xywh"}
                    obj = ObjectAnnotation.from_dict(obj)
                # If object in view
                if obj.view_id == field.name:
                    # Object ID
                    id = obj.id
                    # Object mask
                    mask = obj.mask.to_urle() if obj.mask is not None else None
                    # Object bounding box
                    bbox = (
                        format_bbox(
                            obj.bbox.coords,
                            obj.bbox_confidence is not None,
                            obj.bbox_confidence,
                        )
                        if obj.bbox is not None
                        and obj.bbox.coords != [0.0, 0.0, 0.0, 0.0]
                        else None
                    )
                    # Object source
                    source = obj.mask_source or obj.bbox_source or "Ground truth"
                    # Object category
                    category = (
                        {"id": obj.category_id, "name": obj.category_name}
                        if obj.category_id is not None and obj.category_name is not None
                        else None
                    )
                    # Add object
                    item_details["itemObjects"][source][field.name].append(
                        {
                            "id": id,
                            "mask": mask,
                            "bbox": bbox,
                            "category": category,
                        }
                    )

    return item_details


def load_item_embedding(emb_ds: ds.Dataset, item_id: str, view: str) -> bytes:
    """Get item embedding for a view

    Args:
        emb_ds (ds.Dataset): Embedding dataset
        item_id (str): Item ID
        view (str): Item embedding view

    Returns:
        bytes: Embedding in base 64
    """

    # Load dataset
    pa_emb_ds = emb_ds.load()

    # Get item
    emb_scanner = pa_emb_ds.scanner(filter=ds.field("id").isin([item_id]))
    emb_item = emb_scanner.to_table().to_pylist()[0]
    return emb_item[f"{view}_embedding"]


def save_item_annotations(
    dataset_dir: Path,
    item_id: str,
    annotations: list[ObjectAnnotation],
):
    """Update dataset annotations

    Args:
        dataset_dir (Path): Dataset directory
        item_id (str): Item ID
        annotations (list[ObjectAnnotation]): Item annotations
    """

    # Convert URLE to RLE and add bounding box
    for ann in annotations:
        ann.mask = CompressedRLE.from_urle(ann.mask.to_dict())
        ann.bbox = (
            ann.bbox
            if ann.bbox.coords != [0.0, 0.0, 0.0, 0.0]
            else BBox.from_mask(ann.mask.to_mask())
        )
    # Dataset files
    files = (dataset_dir / "db").glob("**/*.parquet")
    files = sorted(files, key=lambda x: natural_key(x.name))

    # Iterate on dataset files
    for file in files:
        # Read table
        table = pq.read_table(file)
        schema = table.schema

        # Support for previous Image and ObjectAnnotation type
        fields_to_update = []
        for field in schema:
            if (
                str(field.type)
                == "list<item: struct<id: string, view_id: string, bbox: fixed_size_list<item: float>[4], bbox_source: string, bbox_confidence: float, is_group_of: bool, is_difficult: bool, is_truncated: bool, mask: struct<size: list<item: int32>, counts: binary>, mask_source: string, area: float, pose: struct<cam_R_m2c: fixed_size_list<item: double>[9], cam_t_m2c: fixed_size_list<item: double>[3]>, category_id: int32, category_name: string, identity: string>>"
            ):
                # Update schema with new type
                schema = schema.remove(schema.get_field_index("objects"))
                schema = schema.append(
                    pa.field(field.name, pa.list_(ObjectAnnotationType))
                )
                fields_to_update.append(field.name)
            if str(field.type) == "extension<Image<CustomExtensionType>>":
                # Update schema with new type
                schema = schema.remove(schema.get_field_index(field.name))
                schema = schema.append(pa.field(field.name, ImageType))
                fields_to_update.append(field.name)

        # Look for updated item
        filter = table.filter(pc.field("id").isin([item_id]))
        item = filter.to_pylist()

        # If item found
        if item != []:
            # Read table without item
            updated_table = table.filter(~pc.field("id").isin([item_id])).to_pydict()

            # Add item with updated annotations
            item[0]["objects"] = annotations
            for field in schema:
                updated_table[field.name].append(item[0][field.name])

            # Sort table fields according to IDs
            for field in schema:
                if field.name != "id":
                    updated_table[field.name] = [
                        x
                        for _, x in sorted(
                            zip(updated_table["id"], updated_table[field.name]),
                            key=lambda pair: natural_key(pair[0]),
                        )
                    ]
            # Sort table IDs
            updated_table["id"] = sorted(updated_table["id"], key=natural_key)

            # Support for previous Image and ObjectAnnotation type
            for field in schema:
                if is_image_type(field.type) and field.name in fields_to_update:
                    for i, item_image in enumerate(updated_table[field.name]):
                        new_image = Image.from_dict(item_image.to_dict())
                        updated_table[field.name][i] = new_image
                if (
                    is_list_of_object_annotation_type(field.type)
                    and field.name in fields_to_update
                ):
                    for i, item_objects in enumerate(updated_table[field.name]):
                        new_item_objects = []
                        for obj in item_objects:
                            if not isinstance(obj, dict):
                                obj = obj.to_dict()
                            # Support for previous BBox type
                            if isinstance(obj["bbox"], list):
                                obj["bbox"] = {
                                    "coords": obj["bbox"],
                                    "format": "xywh",
                                }
                            obj["mask_source"] = ""
                            obj["bbox_source"] = ""
                            obj = ObjectAnnotation.from_dict(obj)
                            new_item_objects.append(obj)
                        updated_table[field.name][i] = new_item_objects

            # Convert ExtensionTypes
            arrays = []
            for field in schema:
                if is_list_of_object_annotation_type(field.type):
                    arrays.append(
                        ObjectAnnotationType.Array.from_lists(updated_table[field.name])
                    )
                elif is_image_type(field.type):
                    arrays.append(ImageType.Array.from_list(updated_table[field.name]))
                else:
                    arrays.append(
                        convert_field(
                            field_name=field.name,
                            field_type=field.type,
                            field_data=updated_table[field.name],
                        )
                    )

            # Save updated table
            pq.write_table(
                pa.Table.from_arrays(arrays, schema=schema),
                file,
            )
