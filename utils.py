"""
Utility functions for Website Connectivity Monitor
Contains helper functions for URL validation, formatting, and other utilities.
"""

import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

def validate_url(url: str) -> bool:
    if not url:
        return False
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def normalize_url(url: str) -> str:
    if not url.startswith(('http://', 'https://')):
        return 'http://' + url
    return url

def format_timestamp(timestamp: Optional[object]) -> str:
    """
    Format timestamp for display (supports ISO strings or datetime objects).
    """
    if not timestamp:
        return "Never"
    try:
        if isinstance(timestamp, datetime):
            dt = timestamp
        elif isinstance(timestamp, str):
            if "T" in timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            return str(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(timestamp)

def format_duration(seconds: float) -> str:
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
    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except Exception:
        return url

def truncate_string(text: str, max_length: int = 50) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def is_valid_interval(interval: int) -> bool:
    return 5 <= interval <= 86400  # 5s a 24h

def is_valid_timeout(timeout: int) -> bool:
    return 1 <= timeout <= 300  # 1s a 5 min

def get_status_emoji(status: str) -> str:
    status_emojis = {
        'online': '🟢',
        'offline': '🔴',
        'unknown': '⚪',
        'checking': '🟡'
    }
    return status_emojis.get(status.lower(), '⚪')

def format_error_message(error: str, max_length: int = 100) -> str:
    if not error:
        return ""
    error = error.strip()
    prefixes_to_remove = [
        "HTTPSConnectionPool",
        "HTTPConnectionPool",
        "Max retries exceeded with url:",
    ]
    for prefix in prefixes_to_remove:
        if error.startswith(prefix):
            parts = error.split(": ")
            if len(parts) > 1:
                error = parts[-1]
            break
    return truncate_string(error, max_length)
