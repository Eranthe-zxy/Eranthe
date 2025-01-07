# Git-Backed Messaging Application

A lightweight, web-based messaging application that uses Git as a backend storage system. This application is built using Python, SQLite, and GitHub APIs for the backend, with a simple HTML/CSS/JavaScript frontend.

## Features

- Real-time messaging interface
- Git-backed message storage
- User authentication
- Message history
- Simple and clean UI
- SQLite database for user management

## Tech Stack

- Backend: Python (no frameworks)
- Database: SQLite
- Frontend: HTML, CSS, JavaScript (vanilla)
- Version Control & Storage: Git/GitHub API
- Authentication: GitHub OAuth

## Project Structure

```
eranthe/
├── .env                 # Environment variables (GitHub tokens, etc.)
├── .gitignore          # Git ignore file
├── README.md           # This file
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── database/           # SQLite database files
└── src/               # Source code
    ├── server.py      # Main server file
    ├── db.py          # Database operations
    ├── git_ops.py     # Git operations
    └── auth.py        # Authentication handling
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/eranthe.git
   cd eranthe
   ```

2. Create and configure `.env` file with your GitHub credentials:
   ```
   GITHUB_TOKEN=your_github_token
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```

3. Create necessary directories:
   ```bash
   mkdir static templates database src
   ```

4. Install required Python packages (requirements.txt will be provided)

5. Initialize the SQLite database (script will be provided)

6. Run the server:
   ```bash
   python src/server.py
   ```

## Development Status

🚧 Under active development

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
