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

from typing import Optional

import numpy as np
import pyarrow as pa
from pydantic import BaseModel

from pixano.core.pixano_type import PixanoType, create_pyarrow_type
from pixano.utils import (
    denormalize_coords,
    mask_to_bbox,
    normalize_coords,
    xywh_to_xyxy,
    xyxy_to_xywh,
)


class BBox(PixanoType, BaseModel):
    """Bounding box type using coordinates in xyxy or xywh format

    Attributes:
        coords (list[float]): List of coordinates in given format
        format (str): Coordinates format, 'xyxy' or 'xywh'
        is_normalized (bool, optional): True if coordinates are normalized to image size
        confidence (float, optional): Bounding box confidence if predicted
    """

    coords: list[float]
    format: str
    is_normalized: Optional[bool]
    confidence: Optional[float]

    def __init__(
        self,
        coords: list[float],
        format: str,
        is_normalized: bool = True,
        confidence: float = None,
    ):
        """Initialize Bounding box

        Args:
            coords (list[float]): List of coordinates in given format
            format (str): Coordinates format, 'xyxy' or 'xywh'
            is_normalized (bool, optional): True if coordinates are normalized to image size. Defaults to True.
            confidence (float, optional): Bounding box confidence if predicted. Defaults to None.
        """

        # Define public attributes through Pydantic BaseModel
        super().__init__(
            coords=coords,
            format=format,
            is_normalized=is_normalized,
            confidence=confidence,
        )

    @property
    def xyxy_coords(self) -> list[float]:
        """Get bounding box xyxy coordinates

        Returns:
            list[float]: Coordinates in xyxy format
        """

        return self.coords if self.format == "xyxy" else xywh_to_xyxy(self.coords)

    @property
    def xywh_coords(self) -> list[float]:
        """Get bounding box xywh coordinates

        Returns:
            list[float]: Coordinates in xywh format
        """

        return self.coords if self.format == "xywh" else xyxy_to_xywh(self.coords)

    @property
    def is_predicted(self) -> bool:
        """Return True if bounding box is predicted and has a confidence value

        Returns:
            bool: True if bounding box is predicted and has a confidence value
        """

        return self.confidence is not None

    def to_xyxy(self) -> "BBox":
        """Return bounding box in xyxy format

        Returns:
            BBox: Bounding box in xyxy format
        """

        return BBox(self.xyxy_coords, "xyxy", self.is_normalized)

    def to_xywh(self) -> "BBox":
        """Return bounding box in xywh format

        Returns:
            BBox: Bounding box in xyxy format
        """

        return BBox(self.xywh_coords, "xywh", self.is_normalized)

    def normalize(self, height: int, width: int) -> "BBox":
        """Return bounding box with coordinates normalized to image size

        Args:
            height (int): Image height
            width (int): Image width

        Returns:
            BBox: Bounding box with coordinates normalized to image size
        """

        return BBox(normalize_coords(self.coords, height, width), self.format, True)

    def denormalize(self, height: int, width: int) -> "BBox":
        """Return bounding box with coordinates denormalized from image size

        Args:
            height (int): Image height
            width (int): Image width

        Returns:
            BBox: Bounding box with coordinates denormalized from image size
        """

        return BBox(denormalize_coords(self.coords, height, width), self.format, False)

    @staticmethod
    def from_xyxy(xyxy: list[float]) -> "BBox":
        """Create bounding box using normalized xyxy coordinates

        Args:
            xyxy (list[float]): List of coordinates in xyxy format

        Returns:
            Bbox: Bounding box
        """

        return BBox(xyxy, "xyxy")

    @staticmethod
    def from_xywh(xywh: list[float]) -> "BBox":
        """Create bounding box using normalized xywh coordinates

        Args:
            xywh (list[float]): List of coordinates in xywh format

        Returns:
            Bbox: Bounding box
        """

        return BBox(xywh, "xywh")

    @staticmethod
    def from_mask(mask: np.ndarray) -> "BBox":
        """Create bounding box using a NumPy array mask

        Args:
            mask (np.ndarray): NumPy array mask

        Returns:
            Bbox: Bounding box
        """

        return BBox.from_xywh(mask_to_bbox(mask))

    @staticmethod
    def to_struct() -> pa.StructType:
        """Return BBox type as PyArrow Struct

        Returns:
            pa.StructType: Custom type corresponding PyArrow Struct
        """

        return pa.struct(
            [
                pa.field("coords", pa.list_(pa.float32(), list_size=4)),
                pa.field("is_normalized", pa.bool_()),
                pa.field("format", pa.string()),
            ]
        )


BBoxType = create_pyarrow_type(BBox.to_struct(), "Bbox", BBox)
