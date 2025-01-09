#!/usr/bin/env python3

import os
import json
import http.server
import socketserver
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from dotenv import load_dotenv
from db import DatabaseManager
from repository_manager import RepositoryManager, RepositoryConfig

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv('SERVER_PORT', '8000'))
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPOSITORIES = json.loads(os.getenv('GITHUB_REPOSITORIES', '[]'))

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    """Handle HTTP requests for the message board application."""
    
    def __init__(self, *args, **kwargs):
        # Initialize database
        self.db = DatabaseManager()
        
        # Initialize repository manager
        self.repo_manager = RepositoryManager(GITHUB_TOKEN)
        
        # Configure repositories
        for repo in REPOSITORIES:
            self.repo_manager.add_repository(
                owner=repo['owner'],
                name=repo['name'],
                branch=repo.get('branch', 'main'),
                message_path=repo.get('message_path', 'messages')
            )
        
        # Initialize parent class
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/messages':
            self.handle_get_messages(parsed_path)
        else:
            # Serve static files
            if self.path == '/':
                self.path = '/static/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/messages':
            self.handle_post_message()
        else:
            self.send_error(404, "Not Found")
    
    async def fetch_messages(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Fetch messages from all repositories and the local database."""
        try:
            # Fetch messages from repositories
            repo_messages = await self.repo_manager.fetch_all_messages(limit)
            
            # Fetch messages from local database
            db_messages = self.db.get_messages(limit)
            
            # Convert database messages to common format
            formatted_db_messages = [
                {
                    "content": msg["content"],
                    "author": msg["author"],
                    "timestamp": msg["timestamp"],
                    "repository": "local",
                    "id": msg["id"]
                }
                for msg in db_messages
            ]
            
            # Combine and sort all messages
            all_messages = [
                self.repo_manager.to_dict(msg) for msg in repo_messages
            ] + formatted_db_messages
            
            all_messages.sort(
                key=lambda x: datetime.fromisoformat(x["timestamp"]),
                reverse=True
            )
            
            # Apply limit if specified
            if limit is not None:
                all_messages = all_messages[:limit]
            
            return {"messages": all_messages}
            
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return {"messages": [], "error": str(e)}
    
    def handle_get_messages(self, parsed_path: urlparse):
        """Handle GET /messages requests."""
        try:
            # Parse query parameters
            query = parse_qs(parsed_path.query)
            limit = int(query.get('limit', [100])[0])
            
            if limit <= 0:
                self.send_error(400, "Limit must be positive")
                return
            
            # Fetch messages asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_data = loop.run_until_complete(self.fetch_messages(limit))
            loop.close()
            
            # Send response
            self.send_json_response(response_data)
            
        except ValueError as e:
            self.send_error(400, str(e))
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_post_message(self):
        """Handle POST /messages requests."""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            message_data = json.loads(post_data.decode('utf-8'))
            
            if 'message' not in message_data:
                raise ValueError("Message content is required")
            
            # Get message details
            message = message_data['message']
            author = message_data.get('author', 'Anonymous')
            repository = message_data.get('repository')
            
            # Store in database
            stored_message = self.db.store_message(message, author)
            
            try:
                # Store in GitHub repository
                if repository:
                    repo_config = next(
                        (r for r in self.repo_manager.repositories 
                         if f"{r.owner}/{r.name}" == repository),
                        None
                    )
                else:
                    repo_config = self.repo_manager.repositories[0] if self.repo_manager.repositories else None
                
                if repo_config:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    github_result = loop.run_until_complete(
                        self.repo_manager.store_message(message, author, repo_config)
                    )
                    loop.close()
                    
                    # Update database entry with GitHub URL
                    if github_result and 'commit_url' in github_result:
                        self.db.update_message(
                            stored_message['id'],
                            {'github_url': github_result['commit_url']}
                        )
                        stored_message['github_url'] = github_result['commit_url']
                
            except Exception as e:
                print(f"Error storing message in GitHub: {e}")
                # Continue even if GitHub storage fails
            
            # Send response
            self.send_json_response({
                "status": "success",
                "data": stored_message
            })
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except ValueError as e:
            self.send_error(400, str(e))
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_json_response(self, data: Dict[str, Any]):
        """Send a JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def run_server(port: int = PORT):
    """Run the HTTP server."""
    with socketserver.TCPServer(("", port), MessageHandler) as httpd:
        print(f"Server running on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
