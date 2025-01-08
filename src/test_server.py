#!/usr/bin/env python3

import unittest
import json
import os
import threading
import http.server
import socketserver
import requests
from unittest.mock import Mock, patch
from datetime import datetime
import tempfile
import shutil

# Import our server modules
from server import MessageHandler
from db import DatabaseManager
from git_ops import GitMessageHandler

class TestMessageEndpoint(unittest.TestCase):
    """Test cases for the message POST endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up the test server in a separate thread."""
        # Create a temporary directory for test files
        cls.test_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.test_dir, 'test.db')
        cls.test_static_dir = os.path.join(cls.test_dir, 'static')
        os.makedirs(cls.test_static_dir, exist_ok=True)

        # Create a simple index.html for testing
        with open(os.path.join(cls.test_static_dir, 'index.html'), 'w') as f:
            f.write("<html><body>Test Page</body></html>")

        # Set up the test server
        cls.server_port = 8888
        cls.server_url = f'http://localhost:{cls.server_port}'
        
        # Create handler class with test configuration
        class TestHandler(MessageHandler):
            def __init__(self, *args, **kwargs):
                self.db = DatabaseManager(db_path=cls.test_db_path)
                self.git = GitMessageHandler()
                super().__init__(*args, **kwargs)

        # Start server in a separate thread
        cls.httpd = socketserver.TCPServer(("", cls.server_port), TestHandler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.server_thread.join()
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Set up test fixtures."""
        # Clear the database before each test
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = DatabaseManager(db_path=self.test_db_path)

    def test_post_message_success(self):
        """Test successful message posting."""
        test_message = {
            "message": "Test message content",
            "author": "TestUser"
        }

        response = requests.post(
            f'{self.server_url}/messages',
            json=test_message
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response format
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Message stored successfully')
        self.assertIn('data', data)
        
        # Verify message data
        stored_message = data['data']
        self.assertEqual(stored_message['content'], test_message['message'])
        self.assertEqual(stored_message['author'], test_message['author'])
        self.assertIn('timestamp', stored_message)
        self.assertIn('id', stored_message)

        # Verify message is in database
        messages = self.db.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['content'], test_message['message'])

    def test_post_message_no_author(self):
        """Test message posting without author."""
        test_message = {
            "message": "Test message without author"
        }

        response = requests.post(
            f'{self.server_url}/messages',
            json=test_message
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['author'], 'Anonymous')

    def test_post_message_invalid_json(self):
        """Test posting invalid JSON data."""
        response = requests.post(
            f'{self.server_url}/messages',
            data="Invalid JSON"
        )

        self.assertEqual(response.status_code, 400)

    def test_post_message_missing_content(self):
        """Test posting message without content."""
        test_message = {
            "author": "TestUser"
        }

        response = requests.post(
            f'{self.server_url}/messages',
            json=test_message
        )

        self.assertEqual(response.status_code, 400)

    def test_post_message_github_integration(self):
        """Test GitHub integration with message posting."""
        test_message = {
            "message": "Test GitHub integration",
            "author": "TestUser"
        }

        # Mock the GitHub storage
        mock_github_result = {
            'status': 'success',
            'message': 'Message stored in GitHub',
            'details': {
                'html_url': 'https://github.com/test/repo/blob/main/messages/test.json'
            }
        }

        with patch.object(GitMessageHandler, 'store_message', return_value=mock_github_result):
            response = requests.post(
                f'{self.server_url}/messages',
                json=test_message
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify GitHub URL was stored
            self.assertIn('github_url', data['data'])
            self.assertEqual(
                data['data']['github_url'],
                mock_github_result['details']['html_url']
            )

    def test_post_message_github_failure(self):
        """Test handling of GitHub storage failure."""
        test_message = {
            "message": "Test GitHub failure handling",
            "author": "TestUser"
        }

        # Mock GitHub storage to fail
        with patch.object(GitMessageHandler, 'store_message', side_effect=Exception("GitHub error")):
            response = requests.post(
                f'{self.server_url}/messages',
                json=test_message
            )

            # Message should still be stored successfully in database
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'success')
            
            # Verify message is in database
            messages = self.db.get_messages()
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]['content'], test_message['message'])
            
            # GitHub URL should not be present
            self.assertIsNone(messages[0]['github_url'])

def run_tests():
    """Run the test suite."""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests()
