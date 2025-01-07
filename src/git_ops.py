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
    def __init__(self, repo_name="messages", message_dir="messages"):
        """Initialize the Git message handler.
        
        Args:
            repo_name (str): Name of the GitHub repository
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
        self.repo_name = repo_name
        self.message_dir = message_dir
        self.repo = self._get_or_create_repo()
        
    def _get_or_create_repo(self):
        """Get or create the GitHub repository."""
        try:
            # Try to get the authenticated user
            user_response = requests.get(f'{self.api_base}/user', headers=self.headers)
            user_response.raise_for_status()
            username = user_response.json()['login']
            
            # Try to get the repository
            repo_url = f'{self.api_base}/repos/{username}/{self.repo_name}'
            repo_response = requests.get(repo_url, headers=self.headers)
            
            if repo_response.status_code == 404:
                # Create repository if it doesn't exist
                create_repo_url = f'{self.api_base}/user/repos'
                repo_data = {
                    'name': self.repo_name,
                    'private': True,
                    'auto_init': True
                }
                repo_response = requests.post(create_repo_url, json=repo_data, headers=self.headers)
                repo_response.raise_for_status()
                print(f"Created new repository {self.repo_name}")
            else:
                repo_response.raise_for_status()
                print(f"Repository {self.repo_name} found")
                
            return repo_response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error accessing GitHub: {str(e)}")

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
            # Get the authenticated user
            user_response = requests.get(f'{self.api_base}/user', headers=self.headers)
            user_response.raise_for_status()
            username = user_response.json()['login']
            
            # Create the file in the repository
            create_file_url = f'{self.api_base}/repos/{username}/{self.repo_name}/contents/{filename}'
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

    def get_messages(self, limit=100):
        """Retrieve messages from the GitHub repository."""
        try:
            # Get the authenticated user
            user_response = requests.get(f'{self.api_base}/user', headers=self.headers)
            user_response.raise_for_status()
            username = user_response.json()['login']
            
            # Get the contents of the messages directory
            contents_url = f'{self.api_base}/repos/{username}/{self.repo_name}/contents/{self.message_dir}'
            response = requests.get(contents_url, headers=self.headers)
            
            if response.status_code == 404:
                return []
                
            response.raise_for_status()
            contents = response.json()
            
            messages = []
            for content in contents[:limit]:
                file_response = requests.get(content['download_url'], headers=self.headers)
                file_response.raise_for_status()
                message_data = json.loads(file_response.text)
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
