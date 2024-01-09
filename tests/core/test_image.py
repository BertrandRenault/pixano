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

import tempfile
import unittest
from io import BytesIO
from urllib.parse import urlparse
from urllib.request import urlopen

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from IPython.display import Image as IPyImage
from PIL import Image as PILImage

from pixano.core import Image, ImageType
from pixano.utils import binary_to_url


class ImageTestCase(unittest.TestCase):
    """Image test case"""

    def setUp(self):
        """Tests setup"""

        self.file_name = "6805092802_551636b55d_z.jpg"
        self.uri = "https://farm8.staticflickr.com/7051/6805092802_551636b55d_z.jpg"
        with urlopen(self.uri) as opened_file:
            self.bytes = opened_file.read()
        self.preview_bytes = b"preview bytes"

        self.image = Image(self.uri, self.bytes, self.preview_bytes)

    def test_image_bytes(self):
        """Test Image bytes property"""

        self.assertEqual(self.image.bytes, self.bytes)

    def test_image_preview_bytes(self):
        """Test Image preview_bytes property"""

        self.assertEqual(self.image.preview_bytes, self.preview_bytes)

    def test_image_url(self):
        """Test Image url property"""

        expected_url = binary_to_url(self.bytes)

        self.assertEqual(self.image.url, expected_url)

    def test_image_preview_url(self):
        """Test Image preview_url property"""

        expected_url = binary_to_url(self.preview_bytes)

        self.assertEqual(self.image.preview_url, expected_url)

    def test_image_uri_relative_with_prefix(self):
        """Test Image get_uri method, with uri_prefix"""

        uri_prefix = "http://example.com/images/"
        image = Image("relative_path.png", uri_prefix=uri_prefix)
        expected_uri = (
            urlparse(uri_prefix)._replace(path="/images/relative_path.png").geturl()
        )

        self.assertEqual(image.get_uri(), expected_uri)

    def test_image_uri_relative_without_prefix(self):
        """Test Image get_uri method, without uri_prefix"""

        image = Image("relative_path.png")

        with self.assertRaises(Exception):
            image.get_uri()

    def test_image_uri_absolute(self):
        """Test Image get_uri method, with absolute URI"""

        image = Image("http://example.com/image.png")
        expected_uri = "http://example.com/image.png"

        self.assertEqual(image.get_uri(), expected_uri)

    def test_image_size(self):
        """Test Image size property"""

        pillow_image = PILImage.open(BytesIO(self.bytes))
        expected_size = pillow_image.size

        self.assertEqual(self.image.size, expected_size)

    def test_image_open(self):
        """Test Image open method"""

        with self.image.open() as f:
            opened_bytes = f.read()

        self.assertEqual(opened_bytes, self.bytes)

    def test_image_as_pillow(self):
        """Test Image as_pillow method"""

        pillow_image = self.image.as_pillow()

        self.assertIsInstance(pillow_image, PILImage.Image)

    def test_image_as_cv2(self):
        """Test Image as_cv2 method"""

        cv2_image = self.image.as_cv2()

        self.assertIsInstance(cv2_image, np.ndarray)

    def test_image_display(self):
        """Test Image display method"""

        display_result = self.image.display()

        self.assertIsInstance(display_result, IPyImage)

    def test_image_to_dict(self):
        """Test Image to_dict method"""

        expected_dict = {
            "uri": self.uri,
            "bytes": self.bytes,
            "preview_bytes": self.preview_bytes,
        }

        self.assertEqual(self.image.to_dict(), expected_dict)

    def test_image_file_name(self):
        """Test Image file_name property"""

        self.assertEqual(self.image.file_name, self.file_name)


class TestParquetImage(unittest.TestCase):
    """Image test case for Parquet storage"""

    def setUp(self):
        """Tests setup"""

        uri_prefix = "http://farm3.staticflickr.com"

        self.image_list = [
            Image(uri="/2595/3984712091_e82c5ec1ca_z.jpg", uri_prefix=uri_prefix),
            Image(uri="/7150/6601367913_ae54305467_z.jpg", uri_prefix=uri_prefix),
        ]

    def test_image_table(self):
        """Test Image Parquet storage"""

        image_arr = ImageType.Array.from_pylist(self.image_list)
        table = pa.Table.from_arrays(
            [image_arr],
            schema=pa.schema([pa.field("image", ImageType)]),
        )

        with tempfile.NamedTemporaryFile(suffix=".parquet") as temp_file:
            temp_file_path = temp_file.name
            pq.write_table(table, temp_file_path, store_schema=True)
            re_table = pq.read_table(temp_file_path)

        self.assertEqual(re_table.column_names, ["image"])

        image0 = re_table.take([0])["image"][0].as_py()

        self.assertIsInstance(image0, Image)
