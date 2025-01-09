# Project Specification: Git-Backed Message Board Application

Create a web-based messaging application that stores messages both locally in SQLite and remotely in GitHub repositories. The application should have both a web interface and a command-line interface.

## Core Features

### 1. Message Storage & Retrieval
- Store messages in SQLite database with fields:
  - Content (required)
  - Author (optional, default to "Anonymous")
  - Timestamp (ISO format)
  - GitHub URL (optional)
  - Message ID (auto-generated)
  - Repository source
- Support fetching messages from multiple GitHub repositories
- Implement message pagination/limiting (default 100)
- Sort messages in reverse chronological order
- Batch database operations for performance
- Message caching for faster retrieval
- Message structure using dataclasses:
  ```python
  @dataclass
  class Message:
      content: str
      author: str
      timestamp: datetime
      repository: str
      commit_url: Optional[str] = None
      message_id: Optional[str] = None
  ```

### 2. Web Interface
- Clean, modern UI with:
  - Message input field with validation
  - Submit button with loading state
  - Message display area with auto-refresh (30 seconds)
  - Error message display with auto-dismiss (5 seconds)
- Display for each message:
  - Content with word wrapping
  - Author name
  - Formatted timestamp
  - GitHub link (if available)
  - Repository source
- Responsive design features:
  - Mobile-friendly layout
  - Flexible message container
  - Touch-friendly inputs
  - Readable typography
- Error handling and user feedback:
  - Loading indicators
  - Error messages with auto-dismiss
  - Network status updates
  - Input validation feedback
- CSS Variables:
  ```css
  :root {
      --primary-color: #2563eb;
      --background-color: #f8fafc;
      --text-color: #1e293b;
      --border-color: #e2e8f0;
  }
  ```
- Modern styling:
  - Box shadows
  - Border radius
  - Flexible layouts
  - System fonts
- Message display:
  ```javascript
  function displayMessage(message) {
      const messageElement = document.createElement('div');
      messageElement.className = 'message';
      messageElement.innerHTML = `
          <div class="message-content">${escapeHtml(message.content)}</div>
          <div class="message-footer">
              <span class="author">${escapeHtml(message.author)}</span>
              <span class="timestamp">${formatDate(message.timestamp)}</span>
              ${message.github_url ? 
                  `<a href="${escapeHtml(message.github_url)}" target="_blank">View on GitHub</a>` : 
                  ''}
          </div>
      `;
      return messageElement;
  }
  ```
- Auto-refresh implementation:
  ```javascript
  function startAutoRefresh() {
      setInterval(async () => {
          try {
              await fetchAndDisplayMessages();
          } catch (error) {
              showError('Error refreshing messages');
          }
      }, 30000);
  }
  ```

### 3. GitHub Integration
- Store messages as JSON files in GitHub repositories
- Support multiple repository configurations:
  - Custom branch names per repository
  - Custom message paths per repository
  - Repository-specific configurations
- Message storage features:
  - JSON file format
  - Commit URL tracking
  - Author attribution
  - Timestamp preservation
- Error handling:
  - API rate limiting
  - Authentication failures
  - Network issues
  - Permission errors
- Async operations:
  - Parallel message fetching
  - Non-blocking storage
  - Background synchronization
- Fallback mechanisms:
  - Local storage if GitHub fails
  - Retry logic for failed operations
  - Error reporting
- GitHub API endpoints:
  - `/repos/{owner}/{name}/git/trees/{branch}?recursive=1`
  - `/repos/{owner}/{name}/git/blobs/{sha}`
  - `/repos/{owner}/{name}/contents/{path}`
- Headers:
  ```python
  headers = {
      "Authorization": f"token {github_token}",
      "Accept": "application/vnd.github.v3+json"
  }
  ```

### 4. Command Line Interface
- Environment variable management:
  - View all variables (with pretty printing)
  - Get specific variable
  - Set variable (with JSON validation)
  - Delete variable
  - Non-destructive updates
- Git operations:
  - Push changes to GitHub
  - Custom remote and branch support
  - Error handling for git operations
- Server management:
  - Start/stop server
  - Port configuration
  - Status checking
- Features:
  - JSON validation for complex values
  - Pretty printing for output
  - Detailed error messages
  - Help text and examples
  - Non-blocking operations
- Environment file handling:
  - Non-destructive updates
  - File creation if not exists
  - JSON value parsing
  - Proper line formatting

### 5. Configuration
- Environment variables:
  - GITHUB_TOKEN (required)
  - SERVER_PORT (default: 8000)
  - GITHUB_REPOSITORIES (JSON array)
- Repository configuration format:
  ```json
  {
    "owner": "username",
    "name": "repository",
    "branch": "main",
    "message_path": "messages"
  }
  ```
- Support for multiple repository configurations
- Non-destructive environment variable updates
- Secure token handling

## Technical Requirements

### Backend (Python)
- HTTP server:
  - Custom handler class
  - Static file serving
  - JSON response formatting
  - Error handling
- Database operations:
  - SQLite connection management
  - Prepared statements
  - Transaction support
  - Error handling
- GitHub integration:
  - REST API client
  - Async operations
  - Rate limiting
  - Error handling
- Security:
  - Input sanitization
  - XSS prevention
  - Content-Type validation
  - Error message sanitization
- Custom handler class:
  ```python
  class MessageHandler(http.server.SimpleHTTPRequestHandler):
      def __init__(self, *args, **kwargs):
          self.db = DatabaseManager()
          self.repo_manager = RepositoryManager(GITHUB_TOKEN)
          super().__init__(*args, **kwargs)
  ```

### Frontend
- Pure HTML/CSS/JavaScript (no frameworks)
- Features:
  - Modular JavaScript
  - Event delegation
  - Error handling
  - Auto-refresh
  - Form validation
- Styling:
  - CSS variables
  - Flexbox layout
  - Mobile-first design
  - Transitions and animations
- Security:
  - HTML escaping
  - Input validation
  - XSS prevention

### Project Structure
```
project/
├── src/
│   ├── server.py           # Main HTTP server
│   ├── db.py              # Database operations
│   ├── repository_manager.py   # GitHub operations
│   ├── cli.py             # Command-line interface
│   └── test_server.py     # Server tests
├── static/
│   ├── index.html         # Web interface
│   └── js/
│       └── messages.js    # Message handling logic
├── .env                  # Environment variables
├── .gitignore           # Git ignore file
├── README.md            # Documentation
└── requirements.txt     # Python dependencies
```

### Dependencies
Required Python packages:
```
aiohttp>=3.10.0
python-dotenv>=1.0.0
typing-extensions>=4.1.0
aiohappyeyeballs>=2.3.0
multidict>=6.0.0
yarl>=1.9.0
aiosignal>=1.3.0
async-timeout>=4.0.0
frozenlist>=1.4.0
```

## Implementation Details

### API Endpoints

1. GET `/messages`
   - Query parameters:
     - limit (optional, integer, default 100)
   - Response format:
     ```json
     {
       "messages": [
         {
           "content": "string",
           "author": "string",
           "timestamp": "ISO-8601",
           "github_url": "string?",
           "repository": "string",
           "id": "string"
         }
       ]
     }
     ```

2. POST `/messages`
   - Request body:
     ```json
     {
       "message": "string",
       "author": "string?",
       "repository": "string?"
     }
     ```
   - Response format:
     ```json
     {
       "status": "success",
       "data": {
         "content": "string",
         "author": "string",
         "timestamp": "ISO-8601",
         "github_url": "string?",
         "repository": "string",
         "id": "string"
       }
     }
     ```

### Database Schema
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous',
    timestamp TEXT NOT NULL,
    github_url TEXT,
    repository TEXT DEFAULT 'local'
);

CREATE INDEX idx_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_repository ON messages(repository);
```

### Error Response Format
```json
{
  "status": "error",
  "message": "string",
  "details": "string?"
}
```
- Detailed error responses:
  ```json
  {
    "status": "error",
    "message": "Failed to post message",
    "details": {
      "type": "github_error",
      "repository": "owner/repo",
      "status_code": 403,
      "reason": "rate_limit_exceeded"
    }
  }
  ```

### Testing Requirements
- Unit tests for:
  - Message endpoints (GET, POST)
  - Database operations (CRUD)
  - GitHub integration
  - Environment variable management
  - Concurrent operations
- Test scenarios:
  - Successful message operations
  - Error handling
  - Rate limiting
  - Network failures
  - Invalid inputs
  - Concurrent requests
  - Message ordering
  - Database constraints
  - GitHub API interactions
  - Environment variable parsing

### Error Handling
- HTTP status codes:
  - 200: Success
  - 400: Bad Request
  - 404: Not Found
  - 500: Internal Server Error
- Client-side error handling:
  - Network errors
  - Invalid input
  - Server errors
  - Timeout handling
  - Retry logic

### Security Considerations
- Input validation
- Content-Type verification
- XSS prevention
- Secure token handling
- Error message sanitization
- Rate limiting
- Safe environment variable handling

## Usage Examples

### CLI Commands
```bash
# Environment Variables
./src/cli.py env list
./src/cli.py env get GITHUB_TOKEN
./src/cli.py env set GITHUB_TOKEN your_token_here
./src/cli.py env set GITHUB_REPOSITORIES '[{"owner": "user", "name": "repo"}]'
./src/cli.py env delete OLD_VAR

# Git Operations
./src/cli.py push
./src/cli.py push --remote origin --branch main
```

### API Requests
```bash
# Get Messages
curl http://localhost:8000/messages
curl http://localhost:8000/messages?limit=50

# Post Message
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "author": "User"}'
```
