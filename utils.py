#!/usr/bin/env python
"""
Utility functions for Record Matcher
Provides helpers for file management, serialization, and resource cleanup
"""

import os
import json
import glob
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def cleanup_temp_files(temp_dir='./temp/', max_age_days=7, pattern='*.xlsx'):
    """
    Clean up old temporary files in the temp directory.
    
    Args:
        temp_dir: Directory containing temporary files
        max_age_days: Maximum age of files to keep (older files are deleted)
        pattern: File pattern to match (e.g., '*.xlsx', '*.xls')
    
    Returns:
        Tuple of (files_deleted, total_size_freed_bytes)
    """
    if not os.path.exists(temp_dir):
        return 0, 0
    
    files_deleted = 0
    size_freed = 0
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    
    search_pattern = os.path.join(temp_dir, pattern)
    for filepath in glob.glob(search_pattern):
        try:
            # Check file modification time
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_mtime < cutoff_time:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                files_deleted += 1
                size_freed += file_size
        except OSError as e:
            print(f"Error deleting {filepath}: {e}")
            continue
    
    return files_deleted, size_freed


def cleanup_all_temp_files(temp_dir='./temp/'):
    """
    Remove all files from the temp directory.
    
    Args:
        temp_dir: Directory to clean
        
    Returns:
        Number of files deleted
    """
    if not os.path.exists(temp_dir):
        return 0
    
    files_deleted = 0
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
                files_deleted += 1
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
                files_deleted += 1
        except OSError as e:
            print(f"Error deleting {filepath}: {e}")
    
    return files_deleted


def ensure_temp_dir_exists(temp_dir='./temp/'):
    """
    Ensure the temp directory exists, create if it doesn't.
    
    Args:
        temp_dir: Directory path to ensure exists
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        os.makedirs(temp_dir, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating temp directory: {e}")
        return False


def save_to_json(data: Any, filepath: str, indent=2) -> bool:
    """
    Save data to JSON file with error handling.
    Safer alternative to pickle for serialization.
    
    Args:
        data: Data to serialize (must be JSON-serializable)
        filepath: Path to save the JSON file
        indent: JSON indentation level (default 2 for readability)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        return True
    except (TypeError, ValueError, OSError) as e:
        print(f"Error saving JSON to {filepath}: {e}")
        return False


def load_from_json(filepath: str, default=None) -> Any:
    """
    Load data from JSON file with error handling.
    Safer alternative to pickle for deserialization.
    
    Args:
        filepath: Path to the JSON file
        default: Default value to return if loading fails
        
    Returns:
        Loaded data or default value
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return default


def convert_pickle_to_json(pickle_path: str, json_path: str) -> bool:
    """
    Convert a pickle file to JSON format.
    Helps migrate from pickle to safer JSON storage.
    
    Args:
        pickle_path: Path to existing pickle file
        json_path: Path for output JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import pickle
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)
        return save_to_json(data, json_path)
    except Exception as e:
        print(f"Error converting pickle to JSON: {e}")
        return False


def get_temp_file_path(filename: str, temp_dir='./temp/') -> str:
    """
    Get a full path for a temporary file, ensuring temp directory exists.
    
    Args:
        filename: Name of the temporary file
        temp_dir: Temporary directory path
        
    Returns:
        Full path to the temporary file
    """
    ensure_temp_dir_exists(temp_dir)
    return os.path.join(temp_dir, filename)


def get_temp_dir_size(temp_dir='./temp/') -> int:
    """
    Calculate total size of temp directory in bytes.
    
    Args:
        temp_dir: Directory to calculate size for
        
    Returns:
        Total size in bytes
    """
    if not os.path.exists(temp_dir):
        return 0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(temp_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                continue
    return total_size


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
