"""
Monitoring module for Website Connectivity Monitor
Handles the actual connectivity checking and status reporting.
"""

import requests
import time
import threading
from datetime import datetime
from typing import Optional
import click
from database import DatabaseManager
from utils import format_timestamp

class ConnectivityMonitor:
    """Monitors website connectivity at regular intervals."""
    
    def __init__(self, db_manager: DatabaseManager, interval: int = 60, timeout: int = 10):
        """
        Initialize the connectivity monitor.
        
        Args:
            db_manager: Database manager instance
            interval: Check interval in seconds
            timeout: Request timeout in seconds
        """
        self.db = db_manager
        self.interval = interval
        self.timeout = timeout
        self.running = False
        self.stop_event = threading.Event()
    
    def check_site(self, url: str) -> tuple:
        """
        Check connectivity status of a single website.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (status, response_time, error_message)
        """
        try:
            start_time = time.time()
            
            # Make HTTP request with timeout
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Website-Connectivity-Monitor/1.0'
                },
                allow_redirects=True
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Consider 2xx and 3xx status codes as online
            if 200 <= response.status_code < 400:
                return ('online', response_time, None)
            else:
                return ('offline', response_time, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            return ('offline', None, f"Timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            return ('offline', None, "Connection failed")
        except requests.exceptions.RequestException as e:
            return ('offline', None, str(e))
        except Exception as e:
            return ('offline', None, f"Unexpected error: {str(e)}")
    
    def run_single_check(self):
        """Run a single check cycle for all monitored sites."""
        sites = self.db.get_all_sites()
        
        if not sites:
            return
        
        # Display header
        current_time = format_timestamp(datetime.now().isoformat())
        click.echo(f"\n[{current_time}] Checking {len(sites)} website(s)...")
        
        for site in sites:
            if self.stop_event.is_set():
                break
                
            url = site['url']
            status, response_time, error = self.check_site(url)
            
            # Update database
            self.db.update_site_status(url, status, response_time, error)
            
            # Display result
            status_indicator = "🟢" if status == 'online' else "🔴"
            response_str = f" ({response_time:.3f}s)" if response_time else ""
            error_str = f" - {error}" if error else ""
            
            click.echo(f"  {status_indicator} {url:<50} {status.upper()}{response_str}{error_str}")
        
        if not self.stop_event.is_set():
            click.echo(f"Next check in {self.interval} seconds...")
    
    def run(self):
        """Main monitoring loop."""
        self.running = True
        
        try:
            while self.running and not self.stop_event.is_set():
                self.run_single_check()
                
                # Wait for next interval or stop event
                if self.stop_event.wait(timeout=self.interval):
                    break
                    
        except Exception as e:
            click.echo(f"Monitor error: {e}", err=True)
        finally:
            self.running = False
    
    def stop(self):
        """Stop the monitoring loop."""
        self.running = False
        self.stop_event.set()

class SingleCheckMonitor:
    """Performs a one-time check of all monitored sites."""
    
    def __init__(self, db_manager: DatabaseManager, timeout: int = 10):
        """
        Initialize the single check monitor.
        
        Args:
            db_manager: Database manager instance
            timeout: Request timeout in seconds
        """
        self.db = db_manager
        self.timeout = timeout
    
    def check_site(self, url: str) -> tuple:
        """
        Check connectivity status of a single website.
        
        Args:
            url: The URL to check
            
        Returns:
            Tuple of (status, response_time, error_message)
        """
        try:
            start_time = time.time()
            
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Website-Connectivity-Monitor/1.0'
                },
                allow_redirects=True
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if 200 <= response.status_code < 400:
                return ('online', response_time, None)
            else:
                return ('offline', response_time, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            return ('offline', None, f"Timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            return ('offline', None, "Connection failed")
        except requests.exceptions.RequestException as e:
            return ('offline', None, str(e))
        except Exception as e:
            return ('offline', None, f"Unexpected error: {str(e)}")
    
    def check_all_sites(self):
        """Check all monitored sites once and update their status."""
        sites = self.db.get_all_sites()
        
        if not sites:
            click.echo("No websites to check")
            return
        
        click.echo(f"Checking {len(sites)} website(s)...")
        
        for site in sites:
            url = site['url']
            status, response_time, error = self.check_site(url)
            
            # Update database
            self.db.update_site_status(url, status, response_time, error)
            
            # Display result
            status_indicator = "🟢" if status == 'online' else "🔴"
            response_str = f" ({response_time:.3f}s)" if response_time else ""
            error_str = f" - {error}" if error else ""
            
            click.echo(f"  {status_indicator} {url:<50} {status.upper()}{response_str}{error_str}")
