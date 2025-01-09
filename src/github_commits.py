#!/usr/bin/env python3

import os
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CommitInfo:
    """Structured representation of a commit."""
    sha: str
    message: str
    author: str
    author_email: str
    timestamp: str
    url: str

class GitHubCommitFetcher:
    """Fetches commit messages from a GitHub repository."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize with GitHub token."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
    
    def get_commits(self, owner: str, repo: str, per_page: int = 30, page: int = 1) -> List[CommitInfo]:
        """
        Fetch commits from a GitHub repository.
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            per_page: Number of commits per page (max 100)
            page: Page number for pagination
            
        Returns:
            List of CommitInfo objects containing commit details
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If invalid parameters are provided
        """
        if per_page > 100:
            raise ValueError("per_page cannot exceed 100")
        if per_page < 1:
            raise ValueError("per_page must be positive")
        if page < 1:
            raise ValueError("page must be positive")
            
        url = f'{self.base_url}/repos/{owner}/{repo}/commits'
        params = {
            'per_page': per_page,
            'page': page
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        try:
            response.raise_for_status()
            commits = []
            for commit_data in response.json():
                commit = commit_data['commit']
                commits.append(CommitInfo(
                    sha=commit_data['sha'],
                    message=commit['message'],
                    author=commit['author']['name'],
                    author_email=commit['author']['email'],
                    timestamp=commit['author']['date'],
                    url=commit_data['html_url']
                ))
            
            return commits
            
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Failed to fetch commits: {str(e)}")
        except (KeyError, ValueError) as e:
            raise RuntimeError(f"Invalid response format: {str(e)}")
    
    def get_commit(self, owner: str, repo: str, commit_sha: str) -> CommitInfo:
        """
        Fetch a specific commit by its SHA.
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            commit_sha: Commit SHA hash
            
        Returns:
            CommitInfo object containing commit details
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If invalid parameters are provided
        """
        url = f'{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}'
        
        response = requests.get(url, headers=self.headers)
        try:
            response.raise_for_status()
            commit_data = response.json()
            commit = commit_data['commit']
            
            return CommitInfo(
                sha=commit_data['sha'],
                message=commit['message'],
                author=commit['author']['name'],
                author_email=commit['author']['email'],
                timestamp=commit['author']['date'],
                url=commit_data['html_url']
            )
            
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Failed to fetch commit {commit_sha}: {str(e)}")
        except (KeyError, ValueError) as e:
            raise RuntimeError(f"Invalid response format: {str(e)}")

def format_commit_message(commit: CommitInfo) -> Dict:
    """Format a commit message for API response."""
    return {
        'sha': commit.sha,
        'message': commit.message,
        'author': {
            'name': commit.author,
            'email': commit.author_email
        },
        'timestamp': commit.timestamp,
        'url': commit.url
    }

if __name__ == '__main__':
    # Example usage
    try:
        fetcher = GitHubCommitFetcher()
        commits = fetcher.get_commits('Eranthe-zxy', 'Eranthe', per_page=5)
        
        print("Latest commits:")
        for commit in commits:
            print(f"\nCommit: {commit.sha[:8]}")
            print(f"Author: {commit.author}")
            print(f"Date: {commit.timestamp}")
            print(f"Message: {commit.message}")
            print(f"URL: {commit.url}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
