"""
Monitoring module for Website Connectivity Monitor
Handles the actual connectivity checking and status reporting (SQLAlchemy version).
"""

import requests
import time
import threading
from datetime import datetime
import click
from database import db, Site, CheckHistory


class ConnectivityMonitor:
    """Monitors website connectivity at regular intervals."""

    def __init__(self, interval: int = 60, timeout: int = 10):
        self.interval = interval
        self.timeout = timeout
        self.running = False
        self.stop_event = threading.Event()

    def check_site(self, url: str) -> tuple:
        """Check connectivity status of a single website."""
        try:
            start_time = time.time()
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': 'Website-Connectivity-Monitor/1.0'},
                allow_redirects=True
            )
            response_time = time.time() - start_time

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
        sites = Site.query.all()
        if not sites:
            return

        click.echo(f"\n[{datetime.now()}] Checking {len(sites)} website(s)...")

        for site in sites:
            if self.stop_event.is_set():
                break

            status, response_time, error = self.check_site(site.url)

            site.last_checked = datetime.utcnow()
            site.last_status = status
            site.response_time = response_time
            site.last_error = error

            history = CheckHistory(
                site_id=site.id,
                status=status,
                response_time=response_time,
                error_message=error
            )
            db.session.add(history)

            status_indicator = "🟢" if status == 'online' else "🔴"
            response_str = f" ({response_time:.3f}s)" if response_time else ""
            error_str = f" - {error}" if error else ""
            click.echo(
                f"  {status_indicator} {site.url:<50} {status.upper()}{response_str}{error_str}"
            )

        db.session.commit()
        if not self.stop_event.is_set():
            click.echo(f"Next check in {self.interval} seconds...")

    def run(self):
        """Main monitoring loop."""
        self.running = True
        try:
            while self.running and not self.stop_event.is_set():
                self.run_single_check()
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

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def check_site(self, url: str) -> tuple:
        """Check connectivity status of a single website."""
        try:
            start_time = time.time()
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': 'Website-Connectivity-Monitor/1.0'},
                allow_redirects=True
            )
            response_time = time.time() - start_time

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
        sites = Site.query.all()
        if not sites:
            click.echo("No websites to check")
            return

        click.echo(f"Checking {len(sites)} website(s)...")
        for site in sites:
            status, response_time, error = self.check_site(site.url)

            site.last_checked = datetime.utcnow()
            site.last_status = status
            site.response_time = response_time
            site.last_error = error

            history = CheckHistory(
                site_id=site.id,
                status=status,
                response_time=response_time,
                error_message=error
            )
            db.session.add(history)

            status_indicator = "🟢" if status == 'online' else "🔴"
            response_str = f" ({response_time:.3f}s)" if response_time else ""
            error_str = f" - {error}" if error else ""
            click.echo(
                f"  {status_indicator} {site.url:<50} {status.upper()}{response_str}{error_str}"
            )

        db.session.commit()
