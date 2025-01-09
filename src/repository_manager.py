#!/usr/bin/env python3

import os
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class RepositoryConfig:
    owner: str
    name: str
    branch: str = "main"
    message_path: str = "messages"
    
@dataclass
class Message:
    content: str
    author: str
    timestamp: datetime
    repository: str
    commit_url: Optional[str] = None
    message_id: Optional[str] = None

class RepositoryManager:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.repositories: List[RepositoryConfig] = []
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
    def add_repository(self, owner: str, name: str, branch: str = "main", 
                      message_path: str = "messages") -> None:
        """Add a repository to be monitored for messages."""
        config = RepositoryConfig(owner=owner, name=name, branch=branch, 
                                message_path=message_path)
        self.repositories.append(config)
        
    async def fetch_messages_from_repo(self, session: aiohttp.ClientSession, 
                                     repo: RepositoryConfig) -> List[Message]:
        """Fetch messages from a single repository."""
        try:
            # Get the tree for the message directory
            url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/git/trees/{repo.branch}?recursive=1"
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Error fetching tree for {repo.owner}/{repo.name}: {response.status}")
                    return []
                
                tree_data = await response.json()
                message_files = [
                    item for item in tree_data.get("tree", [])
                    if item["path"].startswith(f"{repo.message_path}/") 
                    and item["path"].endswith(".json")
                ]
                
            # Fetch content of each message file
            messages = []
            for file_info in message_files:
                file_url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/contents/{file_info['path']}"
                async with session.get(file_url) as response:
                    if response.status != 200:
                        continue
                        
                    content_data = await response.json()
                    try:
                        content = json.loads(
                            content_data.get("content", "e30=").encode().decode()
                        )
                        
                        message = Message(
                            content=content.get("message", ""),
                            author=content.get("author", "Anonymous"),
                            timestamp=datetime.fromisoformat(
                                content.get("timestamp", datetime.now().isoformat())
                            ),
                            repository=f"{repo.owner}/{repo.name}",
                            commit_url=content.get("commit_url"),
                            message_id=content.get("id")
                        )
                        messages.append(message)
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Error parsing message from {file_info['path']}: {e}")
                        continue
                        
            return messages
            
        except Exception as e:
            print(f"Error fetching messages from {repo.owner}/{repo.name}: {e}")
            return []
            
    async def fetch_all_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Fetch messages from all configured repositories."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [
                self.fetch_messages_from_repo(session, repo)
                for repo in self.repositories
            ]
            
            all_messages = []
            for messages in await asyncio.gather(*tasks):
                all_messages.extend(messages)
                
            # Sort by timestamp
            all_messages.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit if specified
            if limit is not None:
                all_messages = all_messages[:limit]
                
            return all_messages
            
    async def store_message(self, message_content: str, author: str, 
                          target_repo: Optional[RepositoryConfig] = None) -> Dict[str, Any]:
        """Store a message in the specified repository (or first repository if none specified)."""
        if not self.repositories:
            raise ValueError("No repositories configured")
            
        repo = target_repo or self.repositories[0]
        timestamp = datetime.now().isoformat()
        message_id = f"{int(datetime.now().timestamp())}"
        
        message_data = {
            "id": message_id,
            "message": message_content,
            "author": author,
            "timestamp": timestamp,
            "repository": f"{repo.owner}/{repo.name}"
        }
        
        # Create message file in repository
        file_path = f"{repo.message_path}/{message_id}.json"
        file_content = json.dumps(message_data, indent=2)
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Create or update file
            url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/contents/{file_path}"
            
            data = {
                "message": f"Add message from {author}",
                "content": file_content.encode().encode('base64').decode(),
                "branch": repo.branch
            }
            
            async with session.put(url, json=data) as response:
                if response.status not in (200, 201):
                    error_data = await response.json()
                    raise ValueError(f"Failed to store message: {error_data.get('message')}")
                    
                result = await response.json()
                message_data["commit_url"] = result["commit"]["html_url"]
                return message_data
                
    def to_dict(self, message: Message) -> Dict[str, Any]:
        """Convert a Message object to a dictionary."""
        return {
            "content": message.content,
            "author": message.author,
            "timestamp": message.timestamp.isoformat(),
            "repository": message.repository,
            "commit_url": message.commit_url,
            "id": message.message_id
        }
