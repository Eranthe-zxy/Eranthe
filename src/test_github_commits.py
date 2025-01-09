#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import requests
from github_commits import GitHubCommitFetcher, CommitInfo

class TestGitHubCommitFetcher(unittest.TestCase):
    """Test cases for GitHubCommitFetcher class."""
    
    def setUp(self):
        """Set up test environment."""
        self.token = "test_token"
        self.fetcher = GitHubCommitFetcher(self.token)
        
        # Sample commit data
        self.sample_commit = {
            'sha': '1234567890abcdef',
            'commit': {
                'message': 'Test commit message',
                'author': {
                    'name': 'Test Author',
                    'email': 'test@example.com',
                    'date': '2025-01-08T17:55:13-05:00'
                }
            },
            'html_url': 'https://github.com/test/repo/commit/1234567890abcdef'
        }
    
    def test_init_without_token(self):
        """Test initialization without token."""
        with patch.dict('os.environ', clear=True):
            with self.assertRaises(ValueError):
                GitHubCommitFetcher()
    
    @patch('requests.get')
    def test_get_commits_success(self, mock_get):
        """Test successful commit retrieval."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [self.sample_commit]
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        commits = self.fetcher.get_commits('test', 'repo')
        
        self.assertEqual(len(commits), 1)
        commit = commits[0]
        self.assertEqual(commit.sha, '1234567890abcdef')
        self.assertEqual(commit.message, 'Test commit message')
        self.assertEqual(commit.author, 'Test Author')
        self.assertEqual(commit.author_email, 'test@example.com')
        self.assertEqual(commit.timestamp, '2025-01-08T17:55:13-05:00')
        self.assertEqual(commit.url, 'https://github.com/test/repo/commit/1234567890abcdef')
    
    @patch('requests.get')
    def test_get_commits_invalid_per_page(self, mock_get):
        """Test invalid per_page parameter."""
        with self.assertRaises(ValueError):
            self.fetcher.get_commits('test', 'repo', per_page=101)
        
        with self.assertRaises(ValueError):
            self.fetcher.get_commits('test', 'repo', per_page=0)
    
    @patch('requests.get')
    def test_get_commits_invalid_page(self, mock_get):
        """Test invalid page parameter."""
        with self.assertRaises(ValueError):
            self.fetcher.get_commits('test', 'repo', page=0)
    
    @patch('requests.get')
    def test_get_commits_api_error(self, mock_get):
        """Test API error handling."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_get.return_value = mock_response
        
        with self.assertRaises(RuntimeError) as ctx:
            self.fetcher.get_commits('test', 'repo')
        self.assertIn("Failed to fetch commits", str(ctx.exception))
    
    @patch('requests.get')
    def test_get_commit_success(self, mock_get):
        """Test successful single commit retrieval."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_commit
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        commit = self.fetcher.get_commit('test', 'repo', '1234567890abcdef')
        
        self.assertEqual(commit.sha, '1234567890abcdef')
        self.assertEqual(commit.message, 'Test commit message')
        self.assertEqual(commit.author, 'Test Author')
        self.assertEqual(commit.author_email, 'test@example.com')
        self.assertEqual(commit.timestamp, '2025-01-08T17:55:13-05:00')
        self.assertEqual(commit.url, 'https://github.com/test/repo/commit/1234567890abcdef')
    
    @patch('requests.get')
    def test_get_commit_not_found(self, mock_get):
        """Test commit not found error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
        mock_get.return_value = mock_response
        
        with self.assertRaises(RuntimeError) as ctx:
            self.fetcher.get_commit('test', 'repo', 'invalid_sha')
        self.assertIn("Failed to fetch commit", str(ctx.exception))

if __name__ == '__main__':
    unittest.main()
