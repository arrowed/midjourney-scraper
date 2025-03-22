from tempfile import TemporaryDirectory
import unittest
from resolution_parser import ResolutionParser
from PIL import Image
import os

class TestResolutionParser(unittest.TestCase):

    def setUp(self):
        self.parser = ResolutionParser()

    def test_get_all_targets(self):
        expected_folders = ["1080", "4k", "widescreen", "undefined", "square"]
        self.assertEqual(sorted(list(self.parser.get_all_targets())), sorted(expected_folders))

    def test_get_folder_for_file_1080(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_1024.jpg')

            with Image.new('RGB', (1024, 1080)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(fname)
            self.assertEqual(folder, "1080")
            self.assertEqual(width, 1024)
            self.assertEqual(height, 1080)
            self.assertAlmostEqual(ratio, 1024/1080)

    def test_get_folder_for_file_4k(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_4k.jpg')
            with Image.new('RGB', (3840, 2160)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(fname)
            self.assertEqual(folder, "4k")
            self.assertEqual(width, 3840)
            self.assertEqual(height, 2160)
            self.assertAlmostEqual(ratio, 3840/2160)

    def test_get_folder_for_file_widescreen(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_widescreen.jpg')
            with Image.new('RGB', (1600, 900)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(fname)
            self.assertEqual(folder, "widescreen")
            self.assertEqual(width, 1600)
            self.assertEqual(height, 900)
            self.assertAlmostEqual(ratio, 1600/900)

    def test_get_folder_for_file_square(self):
        with TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, 'test_square.jpg')
            with Image.new('RGB', (1000, 1000)) as img:
                img.save(fname)
            folder, width, height, ratio = self.parser.get_folder_for_file(fname)
            self.assertEqual(folder, "square")
            self.assertEqual(width, 1000)
            self.assertEqual(height, 1000)
            self.assertAlmostEqual(ratio, 1.0)

    def test_get_folder_for_file_error(self):
        folder, width, height, ratio = self.parser.get_folder_for_file('non_existent_file.jpg')
        self.assertEqual(folder, "undefined")
        self.assertEqual(width, 0)
        self.assertEqual(height, 0)
        self.assertAlmostEqual(ratio, 0.0)

if __name__ == '__main__':
    unittest.main()