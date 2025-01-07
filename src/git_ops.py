#!/usr/bin/env python3

import os
import json
from datetime import datetime
from github import Github
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
            
        self.g = Github(self.github_token)
        self.repo_name = repo_name
        self.message_dir = message_dir
        self.repo = self._get_or_create_repo()
        
    def _get_or_create_repo(self):
        """Get or create the GitHub repository."""
        try:
            user = self.g.get_user()
            try:
                repo = user.get_repo(self.repo_name)
                print(f"Repository {self.repo_name} found")
                return repo
            except Exception:
                print(f"Creating new repository {self.repo_name}")
                repo = user.create_repo(self.repo_name, private=True)
                # Initialize with README
                repo.create_file("README.md", 
                               "Initial commit", 
                               "# Message Repository\nStores messages for the messaging application.")
                return repo
        except Exception as e:
            raise Exception(f"Error accessing GitHub: {str(e)}")

    def store_message(self, message_content, author="Anonymous"):
        """Store a message in the GitHub repository.
        
        Args:
            message_content (str): Content of the message
            author (str): Author of the message
        
        Returns:
            dict: Message details including GitHub commit information
        """
        timestamp = datetime.now().isoformat()
        message_data = {
            "content": message_content,
            "author": author,
            "timestamp": timestamp
        }
        
        # Create filename based on timestamp
        filename = f"{self.message_dir}/{timestamp.replace(':', '-')}.json"
        
        try:
            # Create or update the file in the repository
            commit_message = f"Add message from {author}"
            self.repo.create_file(
                filename,
                commit_message,
                json.dumps(message_data, indent=2)
            )
            
            return {
                "status": "success",
                "message": "Message stored in GitHub",
                "details": message_data
            }
        except Exception as e:
            raise Exception(f"Error storing message: {str(e)}")

    def get_messages(self, limit=100):
        """Retrieve messages from the GitHub repository.
        
        Args:
            limit (int): Maximum number of messages to retrieve
            
        Returns:
            list: List of messages
        """
        try:
            # Get the contents of the messages directory
            contents = self.repo.get_contents(self.message_dir)
            messages = []
            
            for content in contents[:limit]:
                file_content = content.decoded_content.decode('utf-8')
                message_data = json.loads(file_content)
                messages.append(message_data)
                
            # Sort messages by timestamp
            messages.sort(key=lambda x: x['timestamp'], reverse=True)
            return messages
            
        except Exception as e:
            if "not found" in str(e).lower():
                return []
            raise Exception(f"Error retrieving messages: {str(e)}")

# Example usage
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
