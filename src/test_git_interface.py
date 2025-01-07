#!/usr/bin/env python3

import unittest
import os
import json
from datetime import datetime
from unittest.mock import Mock, patch
from git_ops import GitMessageHandler
from dotenv import load_dotenv

class TestGitMessageHandler(unittest.TestCase):
    """Test cases for GitMessageHandler class."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        load_dotenv()
        cls.github_token = os.getenv('GITHUB_TOKEN')
        if not cls.github_token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")

    def setUp(self):
        """Set up test fixtures."""
        self.repo_name = "test-messages-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        self.handler = GitMessageHandler(repo_name=self.repo_name)
        self.test_message = "Test message content"
        self.test_author = "TestUser"

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            # Delete test repository if it exists
            repo = self.handler.repo
            if repo:
                repo.delete()
        except Exception as e:
            print(f"Warning: Could not delete test repository: {str(e)}")

    def test_repository_creation(self):
        """Test repository creation and initialization."""
        self.assertIsNotNone(self.handler.repo)
        self.assertEqual(self.handler.repo.name, self.repo_name)
        self.assertTrue(self.handler.repo.private)

        # Check if README exists
        readme = self.handler.repo.get_contents("README.md")
        self.assertIsNotNone(readme)
        self.assertIn("Message Repository", readme.decoded_content.decode('utf-8'))

    def test_store_message(self):
        """Test storing a message in the repository."""
        result = self.handler.store_message(self.test_message, self.test_author)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['details']['content'], self.test_message)
        self.assertEqual(result['details']['author'], self.test_author)
        self.assertIn('timestamp', result['details'])

    def test_get_messages_empty(self):
        """Test retrieving messages from an empty repository."""
        messages = self.handler.get_messages()
        self.assertEqual(len(messages), 0)

    def test_get_messages_with_content(self):
        """Test retrieving messages after storing some."""
        # Store multiple messages
        messages_to_store = [
            ("Message 1", "User1"),
            ("Message 2", "User2"),
            ("Message 3", "User3")
        ]
        
        for content, author in messages_to_store:
            self.handler.store_message(content, author)

        # Retrieve and verify messages
        messages = self.handler.get_messages()
        self.assertEqual(len(messages), len(messages_to_store))
        
        # Check if messages are sorted by timestamp (newest first)
        timestamps = [msg['timestamp'] for msg in messages]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_message_content_format(self):
        """Test the format of stored message content."""
        self.handler.store_message(self.test_message, self.test_author)
        messages = self.handler.get_messages()
        
        message = messages[0]
        required_fields = ['content', 'author', 'timestamp']
        
        for field in required_fields:
            self.assertIn(field, message)
            self.assertIsNotNone(message[field])

    def test_invalid_message_content(self):
        """Test handling of invalid message content."""
        invalid_inputs = [None, "", " ", "\n", {}]
        
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(Exception):
                    self.handler.store_message(invalid_input, self.test_author)

    @patch('github.Github')
    def test_github_api_error(self, mock_github):
        """Test handling of GitHub API errors."""
        # Mock GitHub API error
        mock_github.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception) as context:
            GitMessageHandler(repo_name="test-repo")
        
        self.assertIn("Error accessing GitHub", str(context.exception))

def run_tests():
    """Run the test suite."""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_tests()
