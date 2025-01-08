#!/usr/bin/env python3

import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus
from datetime import datetime
from db import DatabaseManager
from git_ops import GitMessageHandler

class MessageHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the messaging application."""
    
    def __init__(self, *args, **kwargs):
        # Initialize database and GitHub handlers
        self.db = DatabaseManager()
        self.git = GitMessageHandler()
        # Initialize the parent class
        super(http.server.SimpleHTTPRequestHandler, self).__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        # Route handling
        if parsed_path.path == '/':
            # Serve the main page
            self.serve_static_file('index.html')
        elif parsed_path.path == '/messages':
            # Return list of messages from database
            messages = self.db.get_messages()
            self.send_json_response({'messages': messages})
        else:
            # Try to serve static files
            self.serve_static_file(parsed_path.path.lstrip('/'))
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        
        # Get the content length to read the body
        content_length = int(self.headers.get('Content-Length', 0))
        
        if parsed_path.path == '/messages':
            # Read and parse the request body
            post_data = self.rfile.read(content_length)
            try:
                message_data = json.loads(post_data.decode('utf-8'))
                
                # Validate message data
                if 'message' not in message_data:
                    raise ValueError("Message content is required")
                
                # Get author from message data or use default
                author = message_data.get('author', 'Anonymous')
                
                # Store message in database first
                db_message = self.db.store_message(
                    content=message_data['message'],
                    author=author
                )
                
                try:
                    # Store message in GitHub
                    git_result = self.git.store_message(
                        message_content=message_data['message'],
                        author=author
                    )
                    
                    # Update database with GitHub URL if available
                    if git_result.get('details', {}).get('html_url'):
                        self.db.update_github_url(
                            db_message['id'],
                            git_result['details']['html_url']
                        )
                        db_message['github_url'] = git_result['details']['html_url']
                        
                except Exception as e:
                    print(f"Warning: Failed to store message in GitHub: {str(e)}")
                    # Continue even if GitHub storage fails
                
                response_data = {
                    'status': 'success',
                    'message': 'Message stored successfully',
                    'data': db_message
                }
                self.send_json_response(response_data)
                
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON data")
            except ValueError as e:
                self.send_error(HTTPStatus.BAD_REQUEST, str(e))
            except Exception as e:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Error processing message: {str(e)}")
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
    
    def serve_static_file(self, file_path):
        """Serve static files from the static directory."""
        try:
            # Construct the full path
            full_path = os.path.join(os.path.dirname(__file__), '..', 'static', file_path)
            
            # Get the file extension
            _, ext = os.path.splitext(file_path)
            
            # Set content type based on file extension
            content_types = {
                '.html': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.json': 'application/json',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.gif': 'image/gif'
            }
            
            content_type = content_types.get(ext.lower(), 'application/octet-stream')
            
            with open(full_path, 'rb') as f:
                content = f.read()
                
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
    
    def send_json_response(self, data):
        """Helper method to send JSON responses."""
        response = json.dumps(data).encode('utf-8')
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

def run_server(port=8000):
    """Start the HTTP server."""
    # Ensure database is initialized
    db = DatabaseManager()
    db.init_db()
    
    with socketserver.TCPServer(("", port), MessageHandler) as httpd:
        print(f"Server running on port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

if __name__ == "__main__":
    # Get port from environment variable or use default
    PORT = int(os.getenv('SERVER_PORT', 8000))
    run_server(PORT)
