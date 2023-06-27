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

import pyarrow as pa

from .bbox import BBox, BBoxArray, BBoxType, is_bbox_type
from .compressedRLE import (
    CompressedRLE,
    CompressedRLEArray,
    CompressedRLEType,
    is_compressedRLE_type,
)
from .embedding import Embedding, EmbeddingArray, EmbeddingType, is_embedding_type
from .image import Image, ImageArray, ImageType, is_image_type
from .objectAnnotation import (
    ObjectAnnotation,
    ObjectAnnotationArray,
    ObjectAnnotationType,
    is_objectAnnotation_type,
)
from .pose import Pose, PoseArray, PoseType, is_pose_type
from .depth_image import DepthImage, DepthImageType

__all__ = [
    "BBox",
    "BBoxType",
    "BBoxArray",
    "is_bbox_type",
    "Embedding",
    "EmbeddingType",
    "EmbeddingArray",
    "is_embedding_type",
    "ObjectAnnotation",
    "ObjectAnnotationType",
    "ObjectAnnotationArray",
    "is_objectAnnotation_type",
    "CompressedRLE",
    "CompressedRLEType",
    "CompressedRLEArray",
    "is_compressedRLE_type",
    "Image",
    "ImageType",
    "ImageArray",
    "is_image_type",
    "Pose",
    "PoseType",
    "PoseArray",
    "is_pose_type",
    "DepthImage",
    "DepthImageType"
]


def convert_field(
    field_name: str, field_type: pa.DataType, field_data: list
) -> pa.Array:
    """Convert PyArrow ExtensionTypes properly

    Args:
        field_name (str): Name
        field_type (pa.DataType): Target PyArrow format
        field_data (list): Data in Python format

    Returns:
        pa.Array: Data in target PyArrow format
    """

    # If target format is an ExtensionType
    if isinstance(field_type, pa.ExtensionType):
        storage = pa.array(field_data, type=field_type.storage_type)
        return pa.ExtensionArray.from_storage(field_type, storage)

    # If target format is an extension of ListType
    elif pa.types.is_list(field_type):
        native_arr = pa.array(field_data)
        if isinstance(native_arr, pa.NullArray):
            return pa.nulls(len(native_arr), field_type)
        offsets = native_arr.offsets
        values = native_arr.values.to_numpy(zero_copy_only=False)
        return pa.ListArray.from_arrays(
            offsets,
            convert_field(f"{field_name}.elements", field_type.value_type, values),
        )

    # If target format is an extension of StructType
    elif pa.types.is_struct(field_type):
        native_arr = pa.array(field_data)
        if isinstance(native_arr, pa.NullArray):
            return pa.nulls(len(native_arr), field_type)
        arrays = []
        for subfield in field_type:
            sub_arr = native_arr.field(subfield.name)
            converted = convert_field(
                f"{field_name}.{subfield.name}",
                subfield.type,
                sub_arr.to_numpy(zero_copy_only=False),
            )
            arrays.append(converted)
        return pa.StructArray.from_arrays(arrays, fields=field_type)

    # For other target formats
    else:
        return pa.array(field_data, type=field_type)


def register_extension_types():
    """Register PyArrow ExtensionTypes"""

    pa_types = [
        BBoxType,
        PoseType,
        CompressedRLEType,
        EmbeddingType,
        ImageType,
        ObjectAnnotationType,
    ]

    for t in pa_types:
        # Register ExtensionType
        try:
            pa.register_extension_type(t())
        # If ExtensionType is already registered
        except pa.ArrowKeyError:
            pass


def is_number(t: pa.DataType) -> bool:
    """Check if DataType is a a number (integer or float)

    Args:
        t (pa.DataType): DataType to check

    Returns:
        bool: True if DataType is an integer or a float
    """

    return pa.types.is_integer(t) or pa.types.is_floating(t)


register_extension_types()
