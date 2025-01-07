#!/usr/bin/env python3

from git_ops import GitMessageHandler
import os
from dotenv import load_dotenv

def test_git_operations():
    """Test the Git message handling operations."""
    
    # Load environment variables
    load_dotenv()
    
    # Ensure we have a GitHub token
    if not os.getenv('GITHUB_TOKEN'):
        print("Please set GITHUB_TOKEN in your .env file")
        return
    
    try:
        # Initialize the handler
        handler = GitMessageHandler(repo_name="test-messages")
        
        # Store a test message
        message = "Hello, this is a test message!"
        result = handler.store_message(message, author="TestUser")
        print("\nStored message:")
        print(result)
        
        # Retrieve messages
        messages = handler.get_messages()
        print("\nRetrieved messages:")
        for msg in messages:
            print(f"- {msg['author']} ({msg['timestamp']}): {msg['content']}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    test_git_operations()
