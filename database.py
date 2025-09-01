"""
Database module for Website Connectivity Monitor
Handles SQLite operations for storing monitored sites and their status.
"""

import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    """Manages SQLite database operations for the connectivity monitor."""
    
    def __init__(self, db_path: str = "connectivity_monitor.db"):
        """Initialize database manager with given database path."""
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_checked TIMESTAMP,
                        last_status TEXT,
                        response_time REAL,
                        last_error TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS check_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        site_id INTEGER,
                        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT NOT NULL,
                        response_time REAL,
                        error_message TEXT,
                        FOREIGN KEY (site_id) REFERENCES sites (id)
                    )
                ''')
                
                conn.commit()
            finally:
                conn.close()
    
    def add_site(self, url: str) -> bool:
        """
        Add a new site to monitor.
        
        Args:
            url: The URL to add
            
        Returns:
            True if site was added, False if it already exists
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO sites (url) VALUES (?)', (url,))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # URL already exists
                return False
            finally:
                conn.close()
    
    def remove_site(self, url: str) -> bool:
        """
        Remove a site from monitoring.
        
        Args:
            url: The URL to remove
            
        Returns:
            True if site was removed, False if it didn't exist
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sites WHERE url = ?', (url,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    def get_all_sites(self) -> List[Dict]:
        """
        Get all sites from the database.
        
        Returns:
            List of dictionaries containing site information
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, url, added_at, last_checked, last_status, response_time, last_error
                    FROM sites ORDER BY url
                ''')
                
                sites = []
                for row in cursor.fetchall():
                    sites.append({
                        'id': row[0],
                        'url': row[1],
                        'added_at': row[2],
                        'last_checked': row[3],
                        'last_status': row[4],
                        'response_time': row[5],
                        'last_error': row[6]
                    })
                return sites
            finally:
                conn.close()
    
    def update_site_status(self, url: str, status: str, response_time: Optional[float] = None, error: Optional[str] = None):
        """
        Update the status of a monitored site.
        
        Args:
            url: The URL to update
            status: The status ('online', 'offline')
            response_time: Response time in seconds
            error: Error message if any
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                # Update the sites table
                cursor.execute('''
                    UPDATE sites 
                    SET last_checked = CURRENT_TIMESTAMP, last_status = ?, response_time = ?, last_error = ?
                    WHERE url = ?
                ''', (status, response_time, error, url))
                
                # Get site ID for history entry
                cursor.execute('SELECT id FROM sites WHERE url = ?', (url,))
                site_row = cursor.fetchone()
                if site_row:
                    site_id = site_row[0]
                    
                    # Add to check history
                    cursor.execute('''
                        INSERT INTO check_history (site_id, status, response_time, error_message)
                        VALUES (?, ?, ?, ?)
                    ''', (site_id, status, response_time, error))
                
                conn.commit()
            finally:
                conn.close()
    
    def clear_all_sites(self) -> int:
        """
        Remove all sites from monitoring.
        
        Returns:
            Number of sites removed
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM sites')
                count = cursor.fetchone()[0]
                
                cursor.execute('DELETE FROM check_history')
                cursor.execute('DELETE FROM sites')
                conn.commit()
                
                return count
            finally:
                conn.close()
    
    def get_site_history(self, url: str, limit: int = 100) -> List[Dict]:
        """
        Get check history for a specific site.
        
        Args:
            url: The URL to get history for
            limit: Maximum number of history entries to return
            
        Returns:
            List of dictionaries containing check history
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT h.checked_at, h.status, h.response_time, h.error_message
                    FROM check_history h
                    JOIN sites s ON h.site_id = s.id
                    WHERE s.url = ?
                    ORDER BY h.checked_at DESC
                    LIMIT ?
                ''', (url, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'checked_at': row[0],
                        'status': row[1],
                        'response_time': row[2],
                        'error_message': row[3]
                    })
                return history
            finally:
                conn.close()
