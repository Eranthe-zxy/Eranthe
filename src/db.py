#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="database/messages.db"):
        """Initialize the database manager.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    author TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    github_url TEXT
                )
            ''')
            conn.commit()

    def store_message(self, content, author="Anonymous", github_url=None):
        """Store a message in the database.
        
        Args:
            content (str): Message content
            author (str): Message author
            github_url (str, optional): URL to the message in GitHub
            
        Returns:
            dict: Stored message details
        """
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (content, author, timestamp, github_url)
                VALUES (?, ?, ?, ?)
            ''', (content, author, timestamp, github_url))
            message_id = cursor.lastrowid
            conn.commit()
            
        return self.get_message(message_id)

    def get_message(self, message_id):
        """Get a specific message by ID.
        
        Args:
            message_id (int): Message ID
            
        Returns:
            dict: Message details or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, author, timestamp, github_url
                FROM messages
                WHERE id = ?
            ''', (message_id,))
            row = cursor.fetchone()
            
        if row:
            return dict(row)
        return None

    def get_messages(self, limit=100):
        """Get most recent messages.
        
        Args:
            limit (int): Maximum number of messages to retrieve
            
        Returns:
            list: List of message dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, author, timestamp, github_url
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
        return [dict(row) for row in rows]

    def update_github_url(self, message_id, github_url):
        """Update the GitHub URL for a message.
        
        Args:
            message_id (int): Message ID
            github_url (str): GitHub URL for the message
            
        Returns:
            bool: True if successful, False if message not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages
                SET github_url = ?
                WHERE id = ?
            ''', (github_url, message_id))
            conn.commit()
            
        return cursor.rowcount > 0
