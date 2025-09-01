"""
Utility functions for Website Connectivity Monitor
Contains helper functions for URL validation, formatting, and other utilities.
"""

import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

def validate_url(url: str) -> bool:
    """
    Validate if a URL has a proper format.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url:
        return False
    
    # Add http:// if no scheme is provided
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def normalize_url(url: str) -> str:
    """
    Normalize URL by adding http:// if no scheme is provided.
    
    Args:
        url: The URL to normalize
        
    Returns:
        Normalized URL
    """
    if not url.startswith(('http://', 'https://')):
        return 'http://' + url
    return url

def format_timestamp(timestamp: Optional[str]) -> str:
    """
    Format timestamp string for display.
    
    Args:
        timestamp: ISO format timestamp string
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "Never"
    
    try:
        # Parse ISO format timestamp
        if 'T' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            # SQLite timestamp format
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return timestamp

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def get_domain_from_url(url: str) -> str:
    """
    Extract domain name from URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain name or original URL if extraction fails
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except Exception:
        return url

def truncate_string(text: str, max_length: int = 50) -> str:
    """
    Truncate string to maximum length with ellipsis.
    
    Args:
        text: The text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def is_valid_interval(interval: int) -> bool:
    """
    Check if monitoring interval is valid.
    
    Args:
        interval: Interval in seconds
        
    Returns:
        True if interval is valid (between 5 and 86400 seconds)
    """
    return 5 <= interval <= 86400  # 5 seconds to 24 hours

def is_valid_timeout(timeout: int) -> bool:
    """
    Check if request timeout is valid.
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        True if timeout is valid (between 1 and 300 seconds)
    """
    return 1 <= timeout <= 300  # 1 second to 5 minutes

def get_status_emoji(status: str) -> str:
    """
    Get emoji representation for status.
    
    Args:
        status: Status string ('online', 'offline', etc.)
        
    Returns:
        Emoji string
    """
    status_emojis = {
        'online': '🟢',
        'offline': '🔴',
        'unknown': '⚪',
        'checking': '🟡'
    }
    return status_emojis.get(status.lower(), '⚪')

def format_error_message(error: str, max_length: int = 100) -> str:
    """
    Format error message for display.
    
    Args:
        error: Error message
        max_length: Maximum length for the message
        
    Returns:
        Formatted error message
    """
    if not error:
        return ""
    
    # Clean up common error messages
    error = error.strip()
    
    # Remove redundant prefixes
    prefixes_to_remove = [
        "HTTPSConnectionPool",
        "HTTPConnectionPool",
        "Max retries exceeded with url:",
    ]
    
    for prefix in prefixes_to_remove:
        if error.startswith(prefix):
            # Find the actual error part
            parts = error.split(": ")
            if len(parts) > 1:
                error = parts[-1]
            break
    
    return truncate_string(error, max_length)
