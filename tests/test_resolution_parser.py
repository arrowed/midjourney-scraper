from tempfile import TemporaryDirectory
import unittest
from scraper.resolution_parser import ResolutionParser
from PIL import Image
import os


class TestResolutionParser(unittest.TestCase):

    def setUp(self):
        self.parser = ResolutionParser()

    def test_get_folder_for_file_1080(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_1024.jpg')

            with Image.new('RGB', (1920, 1280)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(
                fname)
            self.assertEqual(folder, "1080")
            self.assertEqual(width, 1920)
            self.assertEqual(height, 1280)
            self.assertAlmostEqual(ratio, 1920/1280, 2)

    def test_get_folder_for_file_4k(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_4k.jpg')
            with Image.new('RGB', (3840, 2160)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(
                fname)
            self.assertEqual(folder, "uhd")
            self.assertEqual(width, 3840)
            self.assertEqual(height, 2160)
            self.assertAlmostEqual(ratio, 3840/2160, 2)

    def test_get_folder_for_file_4k_aspect(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_4k.jpg')
            with Image.new('RGB', (2133, 1200)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(
                fname)
            self.assertEqual(folder, "uhd-small")
            self.assertEqual(width, 2133)
            self.assertEqual(height, 1200)
            self.assertAlmostEqual(ratio, 16/9.0, 2)

    def test_get_folder_for_file_widescreen(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_widescreen.jpg')
            with Image.new('RGB', (1600, 900)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(
                fname)
            self.assertEqual(folder, "widescreen")
            self.assertEqual(width, 1600)
            self.assertEqual(height, 900)
            self.assertAlmostEqual(ratio, 1600/900, 2)

    def test_get_folder_for_file_square(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_square.jpg')
            with Image.new('RGB', (1000, 1000)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(
                fname)
            self.assertEqual(folder, "square")
            self.assertEqual(width, 1000)
            self.assertEqual(height, 1000)
            self.assertAlmostEqual(ratio, 1.0, 2)

    def test_get_folder_for_file_error(self):
        folder, width, height, ratio = self.parser.get_folder_for_file(
            'non_existent_file.jpg')
        self.assertEqual(folder, "undefined")
        self.assertEqual(width, 0)
        self.assertEqual(height, 0)
        self.assertAlmostEqual(ratio, 0.0, 2)

    def test_get_folder_for_dimensions_1080(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            1920, 1280)
        self.assertEqual(folder, "1080")
        self.assertEqual(width, 1920)
        self.assertEqual(height, 1280)
        self.assertAlmostEqual(ratio, 1920/1280, 2)

    def test_get_folder_for_dimensions_uhd(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            3840, 2160)
        self.assertEqual(folder, "uhd")
        self.assertEqual(width, 3840)
        self.assertEqual(height, 2160)
        self.assertAlmostEqual(ratio, 3840/2160, 2)

    def test_get_folder_for_dimensions_uhd_small(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            2133, 1200)
        self.assertEqual(folder, "uhd-small")
        self.assertEqual(width, 2133)
        self.assertEqual(height, 1200)
        self.assertAlmostEqual(ratio, 16/9.0, 2)

    def test_get_folder_for_dimensions_widescreen(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            1600, 900)
        self.assertEqual(folder, "widescreen")
        self.assertEqual(width, 1600)
        self.assertEqual(height, 900)
        self.assertAlmostEqual(ratio, 1600/900, 2)

    def test_get_folder_for_dimensions_square(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            1000, 1000)
        self.assertEqual(folder, "square")
        self.assertEqual(width, 1000)
        self.assertEqual(height, 1000)
        self.assertAlmostEqual(ratio, 1.0, 2)

    def test_get_folder_for_dimensions_ultrawide(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            3840, 1600)
        self.assertEqual(folder, "ultrawide")
        self.assertEqual(width, 3840)
        self.assertEqual(height, 1600)
        self.assertAlmostEqual(ratio, 3840/1600, 2)

    def test_get_folder_for_dimensions_ultrawide_small(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            1920, 800)
        self.assertEqual(folder, "ultrawide-small")
        self.assertEqual(width, 1920)
        self.assertEqual(height, 800)
        self.assertAlmostEqual(ratio, 12/5.0, 2)

    def test_get_folder_for_dimensions_undefined(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            500, 500)
        self.assertEqual(folder, "square")
        self.assertEqual(width, 500)
        self.assertEqual(height, 500)
        self.assertAlmostEqual(ratio, 1.0, 2)

    def test_get_folder_for_dimensions_edge_case(self):
        folder, width, height, ratio = self.parser.get_folder_for_dimensions(
            0, 0)
        self.assertEqual(folder, "undefined")
        self.assertEqual(width, 0)
        self.assertEqual(height, 0)
        self.assertEqual(ratio, 0.0)


if __name__ == '__main__':
    unittest.main()
