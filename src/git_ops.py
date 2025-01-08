#!/usr/bin/env python3

import os
import json
from datetime import datetime
import requests
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GitMessageHandler:
    def __init__(self, message_dir="messages"):
        """Initialize the Git message handler.
        
        Args:
            message_dir (str): Directory where messages will be stored
        """
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GitHub token not found in environment variables")
            
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.api_base = 'https://api.github.com'
        self.message_dir = message_dir
        
        # Get the current repository from git config
        self.repo_info = self._get_current_repo_info()
        print(f"Using repository: {self.repo_info['full_name']}")

    def _get_current_repo_info(self):
        """Get the current repository information from local git config."""
        try:
            # Get the remote URL from git config
            with os.popen('git config --get remote.origin.url') as f:
                remote_url = f.read().strip()
            
            if not remote_url:
                raise ValueError("No git remote URL found")
            
            # Extract owner and repo name from the URL
            # Handle both HTTPS and SSH URLs
            if remote_url.startswith('https://'):
                parts = remote_url.replace('https://github.com/', '').replace('.git', '').split('/')
            else:  # SSH URL
                parts = remote_url.split(':')[1].replace('.git', '').split('/')
                
            owner, repo = parts[-2:]
            
            # Verify the repository exists and we have access
            repo_url = f'{self.api_base}/repos/{owner}/{repo}'
            response = requests.get(repo_url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise Exception(f"Error getting repository information: {str(e)}")

    def store_message(self, message_content, author="Anonymous"):
        """Store a message in the GitHub repository."""
        if not message_content or not isinstance(message_content, str):
            raise ValueError("Invalid message content")
            
        timestamp = datetime.now().isoformat()
        message_data = {
            "content": message_content,
            "author": author,
            "timestamp": timestamp
        }
        
        # Create filename based on timestamp
        filename = f"{self.message_dir}/{timestamp.replace(':', '-')}.json"
        
        try:
            # Create the messages directory if it doesn't exist
            self._ensure_messages_directory()
            
            # Create the file in the repository
            create_file_url = f'{self.api_base}/repos/{self.repo_info["full_name"]}/contents/{filename}'
            file_data = {
                'message': f'Add message from {author}',
                'content': base64.b64encode(json.dumps(message_data, indent=2).encode()).decode()
            }
            
            response = requests.put(create_file_url, json=file_data, headers=self.headers)
            response.raise_for_status()
            
            return {
                "status": "success",
                "message": "Message stored in GitHub",
                "details": message_data
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error storing message: {str(e)}")

    def _ensure_messages_directory(self):
        """Ensure the messages directory exists in the repository."""
        try:
            # Try to get the messages directory
            contents_url = f'{self.api_base}/repos/{self.repo_info["full_name"]}/contents/{self.message_dir}'
            response = requests.get(contents_url, headers=self.headers)
            
            if response.status_code == 404:
                # Create the directory with a .gitkeep file
                file_data = {
                    'message': 'Create messages directory',
                    'content': base64.b64encode(b'').decode(),
                    'path': f'{self.message_dir}/.gitkeep'
                }
                create_url = f'{self.api_base}/repos/{self.repo_info["full_name"]}/contents/{self.message_dir}/.gitkeep'
                response = requests.put(create_url, json=file_data, headers=self.headers)
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            if response.status_code != 404:  # Ignore 404 errors as we'll create the directory
                raise Exception(f"Error ensuring messages directory exists: {str(e)}")

    def get_messages(self, limit=100):
        """Retrieve messages from the GitHub repository."""
        try:
            # Get the contents of the messages directory
            contents_url = f'{self.api_base}/repos/{self.repo_info["full_name"]}/contents/{self.message_dir}'
            response = requests.get(contents_url, headers=self.headers)
            
            if response.status_code == 404:
                return []
                
            response.raise_for_status()
            contents = response.json()
            
            if not isinstance(contents, list):
                return []
                
            messages = []
            for content in contents[:limit]:
                if content['name'] == '.gitkeep':
                    continue
                    
                file_response = requests.get(content['download_url'], headers=self.headers)
                file_response.raise_for_status()
                message_data = file_response.json()
                messages.append(message_data)
                
            # Sort messages by timestamp
            messages.sort(key=lambda x: x['timestamp'], reverse=True)
            return messages
            
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                return []
            raise Exception(f"Error retrieving messages: {str(e)}")

if __name__ == "__main__":
    try:
        handler = GitMessageHandler()
        
        # Store a test message
        result = handler.store_message(
            "This is a test message",
            "TestUser"
        )
        print("Message stored:", result)
        
        # Retrieve messages
        messages = handler.get_messages()
        print("Retrieved messages:", messages)
        
    except Exception as e:
        print(f"Error: {str(e)}")
