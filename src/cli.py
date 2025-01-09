#!/usr/bin/env python3

import os
import sys
import json
import argparse
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

class EnvManager:
    """Manage environment variables in .env file."""
    
    def __init__(self, env_path: str = ".env"):
        self.env_path = Path(env_path)
        self.create_env_if_not_exists()
    
    def create_env_if_not_exists(self) -> None:
        """Create .env file if it doesn't exist."""
        if not self.env_path.exists():
            self.env_path.touch()
    
    def load_env(self) -> Dict[str, Any]:
        """Load environment variables from .env file."""
        return dotenv_values(self.env_path)
    
    def save_env(self, env_vars: Dict[str, Any]) -> None:
        """Save environment variables to .env file."""
        with open(self.env_path, 'w') as f:
            for key, value in env_vars.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                f.write(f'{key}={value}\n')
    
    def get_var(self, key: str) -> Optional[str]:
        """Get value of a specific environment variable."""
        env_vars = self.load_env()
        return env_vars.get(key)
    
    def set_var(self, key: str, value: str) -> None:
        """Set value of a specific environment variable."""
        env_vars = self.load_env()
        env_vars[key] = value
        self.save_env(env_vars)
    
    def delete_var(self, key: str) -> bool:
        """Delete a specific environment variable."""
        env_vars = self.load_env()
        if key in env_vars:
            del env_vars[key]
            self.save_env(env_vars)
            return True
        return False
    
    def list_vars(self) -> Dict[str, str]:
        """List all environment variables."""
        return self.load_env()

def push_to_github(remote: str = "origin", branch: str = "main") -> None:
    """Push local changes to GitHub repository."""
    try:
        # Check if we're in a git repository
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            check=True,
            capture_output=True
        )
        
        # Add all changes
        subprocess.run(
            ["git", "add", "."],
            check=True,
            capture_output=True
        )
        
        # Create a commit if there are changes
        try:
            subprocess.run(
                ["git", "commit", "-m", "Update messages"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            # If there's nothing to commit, that's fine
            if "nothing to commit" not in e.stderr.decode():
                raise
        
        # Push changes
        result = subprocess.run(
            ["git", "push", remote, branch],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("Successfully pushed changes to GitHub!")
        
    except subprocess.CalledProcessError as e:
        error_message = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
        if "not a git repository" in error_message:
            print("Error: Not a git repository. Please run this command from your git project directory.")
        elif "remote origin already exists" in error_message:
            print("Error: Remote repository already exists. Use a different remote name or update the existing one.")
        elif "permission denied" in error_message:
            print("Error: Permission denied. Please check your GitHub credentials.")
        else:
            print(f"Error pushing to GitHub: {error_message}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

def handle_env_command(args: argparse.Namespace) -> None:
    """Handle environment variable commands."""
    env_manager = EnvManager()
    
    if args.env_command == "get":
        value = env_manager.get_var(args.key)
        if value is not None:
            print(f"{args.key}={value}")
        else:
            print(f"Environment variable '{args.key}' not found")
            sys.exit(1)
    
    elif args.env_command == "set":
        try:
            # If value is JSON string, parse it
            if args.value.startswith('{') or args.value.startswith('['):
                try:
                    json_value = json.loads(args.value)
                    args.value = json.dumps(json_value)
                except json.JSONDecodeError:
                    pass
            
            env_manager.set_var(args.key, args.value)
            print(f"Successfully set {args.key}")
        except Exception as e:
            print(f"Error setting environment variable: {str(e)}")
            sys.exit(1)
    
    elif args.env_command == "delete":
        if env_manager.delete_var(args.key):
            print(f"Successfully deleted {args.key}")
        else:
            print(f"Environment variable '{args.key}' not found")
            sys.exit(1)
    
    elif args.env_command == "list":
        env_vars = env_manager.list_vars()
        if env_vars:
            print("\nEnvironment Variables:")
            print("---------------------")
            for key, value in env_vars.items():
                print(f"{key}={value}")
            print()
        else:
            print("No environment variables found")

def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="SimpleChat CLI - Manage your chat application"
    )
    
    # Add commands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Push command
    push_parser = subparsers.add_parser(
        "push",
        help="Push local changes to GitHub repository"
    )
    push_parser.add_argument(
        "--remote",
        default="origin",
        help="Remote repository name (default: origin)"
    )
    push_parser.add_argument(
        "--branch",
        default="main",
        help="Branch name (default: main)"
    )
    
    # Environment variable commands
    env_parser = subparsers.add_parser(
        "env",
        help="Manage environment variables"
    )
    env_subparsers = env_parser.add_subparsers(
        dest="env_command",
        help="Environment variable commands"
    )
    
    # Get environment variable
    get_parser = env_subparsers.add_parser(
        "get",
        help="Get value of an environment variable"
    )
    get_parser.add_argument("key", help="Environment variable name")
    
    # Set environment variable
    set_parser = env_subparsers.add_parser(
        "set",
        help="Set value of an environment variable"
    )
    set_parser.add_argument("key", help="Environment variable name")
    set_parser.add_argument("value", help="Environment variable value")
    
    # Delete environment variable
    delete_parser = env_subparsers.add_parser(
        "delete",
        help="Delete an environment variable"
    )
    delete_parser.add_argument("key", help="Environment variable name")
    
    # List environment variables
    env_subparsers.add_parser(
        "list",
        help="List all environment variables"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "push":
        push_to_github(args.remote, args.branch)
    elif args.command == "env":
        if args.env_command:
            handle_env_command(args)
        else:
            env_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
