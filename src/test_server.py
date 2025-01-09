#!/usr/bin/env python3

import unittest
import json
import os
import threading
import http.server
import socketserver
import requests
import time
from unittest.mock import patch, MagicMock
from datetime import datetime
from db import DatabaseManager
from server import MessageHandler, run_server

class TestMessageEndpoint(unittest.TestCase):
    """Test cases for message endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Use a test port
        cls.port = 8001
        cls.server_url = f'http://localhost:{cls.port}'
        
        # Start server in a separate thread
        cls.server_thread = threading.Thread(
            target=run_server,
            args=(cls.port,),
            daemon=True
        )
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(1)
        
        # Initialize database
        cls.db = DatabaseManager()
        cls.db.init_db()
    
    def setUp(self):
        """Set up test database."""
        # Clear database before each test
        self.db.init_db()
    
    def test_get_messages_empty(self):
        """Test getting messages when database is empty."""
        response = requests.get(f'{self.server_url}/messages')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('messages', data)
        self.assertEqual(len(data['messages']), 0)
    
    def test_get_messages_with_data(self):
        """Test getting messages when database has content."""
        # Add some test messages
        test_messages = [
            {"message": "Test message 1", "author": "User1"},
            {"message": "Test message 2", "author": "User2"},
            {"message": "Test message 3", "author": "User3"}
        ]
        
        # Store messages in database
        for msg in test_messages:
            response = requests.post(
                f'{self.server_url}/messages',
                json=msg
            )
            self.assertEqual(response.status_code, 200)
        
        # Get all messages
        response = requests.get(f'{self.server_url}/messages')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('messages', data)
        messages = data['messages']
        
        # Verify message count
        self.assertEqual(len(messages), len(test_messages))
        
        # Verify message content (in reverse order due to timestamp sorting)
        for i, msg in enumerate(reversed(test_messages)):
            self.assertEqual(messages[i]['content'], msg['message'])
            self.assertEqual(messages[i]['author'], msg['author'])
            self.assertIn('timestamp', messages[i])
            self.assertIn('id', messages[i])
    
    def test_get_messages_limit(self):
        """Test message limit parameter."""
        # Add more messages than the default limit
        test_messages = [
            {"message": f"Test message {i}", "author": f"User{i}"}
            for i in range(150)  # More than default limit of 100
        ]
        
        # Store messages
        for msg in test_messages:
            response = requests.post(
                f'{self.server_url}/messages',
                json=msg
            )
            self.assertEqual(response.status_code, 200)
        
        # Test default limit
        response = requests.get(f'{self.server_url}/messages')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['messages']), 100)  # Default limit
        
        # Test custom limit
        response = requests.get(f'{self.server_url}/messages?limit=50')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['messages']), 50)
        
        # Test limit larger than available messages
        response = requests.get(f'{self.server_url}/messages?limit=200')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['messages']), len(test_messages))
    
    def test_get_messages_invalid_limit(self):
        """Test invalid limit parameter."""
        # Test negative limit
        response = requests.get(f'{self.server_url}/messages?limit=-1')
        self.assertEqual(response.status_code, 400)
        
        # Test zero limit
        response = requests.get(f'{self.server_url}/messages?limit=0')
        self.assertEqual(response.status_code, 400)
        
        # Test non-numeric limit
        response = requests.get(f'{self.server_url}/messages?limit=abc')
        self.assertEqual(response.status_code, 400)
    
    def test_post_message_success(self):
        """Test successful message posting."""
        message_data = {
            "message": "Test message",
            "author": "Test User"
        }
        
        response = requests.post(
            f'{self.server_url}/messages',
            json=message_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertEqual(data['data']['content'], message_data['message'])
        self.assertEqual(data['data']['author'], message_data['author'])
    
    def test_post_message_no_author(self):
        """Test message posting without author."""
        message_data = {
            "message": "Test message"
        }
        
        response = requests.post(
            f'{self.server_url}/messages',
            json=message_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['author'], 'Anonymous')
    
    def test_post_message_missing_content(self):
        """Test posting message without content."""
        message_data = {
            "author": "Test User"
        }
        
        response = requests.post(
            f'{self.server_url}/messages',
            json=message_data
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_post_message_invalid_json(self):
        """Test posting invalid JSON data."""
        response = requests.post(
            f'{self.server_url}/messages',
            data="Invalid JSON",
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_post_message_github_integration(self):
        """Test GitHub integration with message posting."""
        message_data = {
            "message": "Test GitHub integration",
            "author": "Test User"
        }
        
        with patch('git_ops.GitMessageHandler.store_message') as mock_store:
            mock_store.return_value = {
                'status': 'success',
                'details': {
                    'html_url': 'https://github.com/test/repo/commit/123'
                }
            }
            
            response = requests.post(
                f'{self.server_url}/messages',
                json=message_data
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('github_url', data['data'])
            self.assertEqual(
                data['data']['github_url'],
                'https://github.com/test/repo/commit/123'
            )
    
    def test_post_message_github_failure(self):
        """Test handling of GitHub storage failure."""
        message_data = {
            "message": "Test GitHub failure",
            "author": "Test User"
        }
        
        with patch('git_ops.GitMessageHandler.store_message') as mock_store:
            mock_store.side_effect = Exception("GitHub error")
            
            response = requests.post(
                f'{self.server_url}/messages',
                json=message_data
            )
            
            # Message should still be stored in database
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertNotIn('github_url', data['data'])
    
    def test_message_order(self):
        """Test that messages are returned in reverse chronological order."""
        # Add messages with different timestamps
        messages = [
            {"message": "First message", "author": "User1"},
            {"message": "Second message", "author": "User2"},
            {"message": "Third message", "author": "User3"}
        ]
        
        for msg in messages:
            response = requests.post(
                f'{self.server_url}/messages',
                json=msg
            )
            self.assertEqual(response.status_code, 200)
            time.sleep(1)  # Ensure different timestamps
        
        # Get messages
        response = requests.get(f'{self.server_url}/messages')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        messages = data['messages']
        
        # Verify reverse chronological order
        timestamps = [msg['timestamp'] for msg in messages]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        num_requests = 10
        
        def make_request():
            message_data = {
                "message": "Concurrent test",
                "author": "Test User"
            }
            return requests.post(
                f'{self.server_url}/messages',
                json=message_data
            )
        
        # Make concurrent requests
        threads = []
        responses = []
        for _ in range(num_requests):
            thread = threading.Thread(
                target=lambda: responses.append(make_request())
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests were successful
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        # Verify correct number of messages stored
        response = requests.get(f'{self.server_url}/messages')
        data = response.json()
        self.assertEqual(len(data['messages']), num_requests)

if __name__ == '__main__':
    unittest.main()
