from tempfile import TemporaryDirectory
import unittest
import os
from unittest.mock import patch, MagicMock
from scraper.scrape import Scraper
from scraper.discord import DiscordApi
from argparse import Namespace


class TestScraper(unittest.TestCase):

    def setUp(self):
        self.channel_id = "test_channel_id"
        self.channel_name = "test_channel_name"
        self.api = MagicMock(spec=DiscordApi)
        self.args = Namespace(limit_resolutions=None)
        self.scraper = Scraper(
            self.channel_id, self.channel_name, self.api, self.args)

    @patch('requests.get')
    @patch('hashlib.md5')
    def test_download_attachment_success(self, mock_md5, mock_get):
        # Setup
        with TemporaryDirectory() as tempdir:
            # Mock session and response
            mock_response = MagicMock()
            mock_response.content = b'test image content'
            mock_get.return_value = mock_response

            mock_md5.return_value.hexdigest.return_value = 'hash'

            # Test data
            attachment_data = {
                'url': 'https://example.com/test_image.jpg',
                'filename': 'test_image.jpg',
                'width': 1920,
                'height': 1080,
                'size': 1024
            }

            # Call the method
            downloaded_file = self.scraper.download_attachment(
                attachment_data, tempdir)

            # Assertions
            self.assertTrue(os.path.exists(downloaded_file))
            self.assertEqual(os.path.basename(
                downloaded_file), 'test_image_hash.jpg')

            # Verify session was created with correct parameters
            mock_get.assert_called_once()

            # Verify get was called with the URL
            mock_get.assert_called_once_with(
                'https://example.com/test_image.jpg', timeout=10)

            # Verify the file has the correct content
            with open(downloaded_file, 'rb') as f:
                self.assertEqual(f.read(), b'test image content')

    @patch('requests.get')
    @patch('hashlib.md5')
    def test_download_attachment_with_special_chars(self, mock_md5, mock_get):
        # Setup
        with TemporaryDirectory() as tempdir:
            # Mock session and response
            mock_response = MagicMock()
            mock_response.content = b'test image content'
            mock_get.return_value = mock_response

            mock_md5.return_value.hexdigest.return_value = 'hash'

            # Test data with special characters
            attachment_data = {
                'url': 'https://example.com/something_else_entirely.jpg',
                'filename': 'test_image_with_$pecial_chars!.jpg',
                'width': 1920,
                'height': 1080,
                'size': 1024
            }

            # Call the method
            downloaded_file = self.scraper.download_attachment(
                attachment_data, tempdir)

            # Assertions
            self.assertTrue(os.path.exists(downloaded_file))
            # Should have sanitized the filename
            self.assertEqual(os.path.basename(downloaded_file),
                             'test_image_with_pecial_chars_hash.jpg')

            # Verify the request was made with the original URL
            mock_get.assert_called_once_with(
                'https://example.com/something_else_entirely.jpg',
                timeout=10
            )

    @patch('requests.get')
    def test_download_attachment_directory_creation(self, mock_get):
        # Setup
        with TemporaryDirectory() as tempdir:
            non_existent_dir = os.path.join(tempdir, 'new_directory')

            # Mock session and response
            mock_response = MagicMock()
            mock_response.content = b'test image content'
            mock_get.return_value = mock_response

            # Test data
            attachment_data = {
                'url': 'https://example.com/test_image.jpg',
                'filename': 'test_image.jpg',
                'width': 1920,
                'height': 1080,
                'size': 1024
            }

            # Call the method with a non-existent directory
            downloaded_file = self.scraper.download_attachment(
                attachment_data, non_existent_dir)

            # Assertions
            self.assertTrue(os.path.exists(non_existent_dir))
            self.assertTrue(os.path.exists(downloaded_file))

    @patch('requests.get')
    def test_download_only_once(self, mock_get):
        # Setup
        with TemporaryDirectory() as tempdir:
            non_existent_dir = os.path.join(tempdir, 'new_directory')

            mock_response = MagicMock()
            mock_response.content = b'test image content'
            mock_get.return_value = mock_response

            # Test data
            attachment_data = {
                'url': 'https://example.com/test_image.jpg',
                'filename': 'test_image.jpg',
                'width': 1920,
                'height': 1080,
                'size': 1024
            }

            # Call twice, ensure we dont save the file twice
            self.scraper.download_attachment(
                attachment_data, non_existent_dir)
            self.scraper.download_attachment(
                attachment_data, non_existent_dir)

            # Assertions
            mock_get.assert_called_once()

    @patch('hashlib.md5')
    def test_get_safe_filename(self, mock_md5):
        mock_md5.return_value.hexdigest.return_value = 'hash'

        # Test data
        attachment_data = {
            'url': 'https://example.com/something/test_image.jpg',
            'filename': 'test_image$pe\tcial.jpg',
            'width': 1920,
            'height': 1080,
            'size': 1024
        }

        # Call the method
        filename = self.scraper.get_safe_local_filename(attachment_data)

        # Assertions
        self.assertEqual(filename, 'test_imagepecial_hash.jpg')


if __name__ == '__main__':
    unittest.main()
