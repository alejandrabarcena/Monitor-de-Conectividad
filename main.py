#!/usr/bin/env python3
"""
Website Connectivity Monitor - Command Line Tool
A tool for monitoring website connectivity with persistent storage and configurable intervals.
"""

import click
import signal
import sys
import threading
import time
from database import DatabaseManager
from monitor import ConnectivityMonitor
from utils import validate_url, format_timestamp

# Global variables for monitoring
monitor = None
monitor_thread = None
stop_event = threading.Event()

def signal_handler(signum, frame):
    """Handle graceful shutdown on Ctrl+C"""
    click.echo("\n\nShutting down gracefully...")
    if monitor:
        monitor.stop()
    stop_event.set()
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

@click.group()
@click.pass_context
def cli(ctx):
    """Website Connectivity Monitor - Monitor multiple websites for connectivity status."""
    ctx.ensure_object(dict)
    ctx.obj['db'] = DatabaseManager()

@cli.command()
@click.argument('url')
@click.pass_context
def add(ctx, url):
    """Add a website URL to the monitoring list."""
    if not validate_url(url):
        click.echo(f"Error: Invalid URL format: {url}", err=True)
        return
    
    db = ctx.obj['db']
    try:
        if db.add_site(url):
            click.echo(f"✓ Added {url} to monitoring list")
        else:
            click.echo(f"⚠ URL {url} is already in the monitoring list")
    except Exception as e:
        click.echo(f"Error adding URL: {e}", err=True)

@cli.command()
@click.argument('url')
@click.pass_context
def remove(ctx, url):
    """Remove a website URL from the monitoring list."""
    db = ctx.obj['db']
    try:
        if db.remove_site(url):
            click.echo(f"✓ Removed {url} from monitoring list")
        else:
            click.echo(f"⚠ URL {url} not found in monitoring list")
    except Exception as e:
        click.echo(f"Error removing URL: {e}", err=True)

@cli.command()
@click.pass_context
def list(ctx):
    """List all websites in the monitoring list."""
    db = ctx.obj['db']
    try:
        sites = db.get_all_sites()
        if not sites:
            click.echo("No websites in monitoring list")
            return
        
        click.echo("Monitored websites:")
        for i, site in enumerate(sites, 1):
            status_indicator = "🟢" if site['last_status'] == 'online' else "🔴" if site['last_status'] == 'offline' else "⚪"
            last_check = format_timestamp(site['last_checked']) if site['last_checked'] else "Never"
            click.echo(f"{i:2d}. {status_indicator} {site['url']:<50} Last check: {last_check}")
    except Exception as e:
        click.echo(f"Error listing sites: {e}", err=True)

@cli.command()
@click.option('--interval', '-i', default=60, help='Check interval in seconds (default: 60)')
@click.option('--timeout', '-t', default=10, help='Request timeout in seconds (default: 10)')
@click.pass_context
def start(ctx, interval, timeout):
    """Start monitoring all websites in the list."""
    global monitor, monitor_thread
    
    db = ctx.obj['db']
    try:
        sites = db.get_all_sites()
        if not sites:
            click.echo("No websites to monitor. Add some websites first using 'add' command.")
            return
        
        click.echo(f"Starting connectivity monitor...")
        click.echo(f"Check interval: {interval} seconds")
        click.echo(f"Request timeout: {timeout} seconds")
        click.echo(f"Monitoring {len(sites)} website(s)")
        click.echo("Press Ctrl+C to stop monitoring\n")
        
        # Create and start monitor
        monitor = ConnectivityMonitor(db, interval, timeout)
        monitor_thread = threading.Thread(target=monitor.run, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive and display results
        try:
            while not stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
    except Exception as e:
        click.echo(f"Error starting monitor: {e}", err=True)

@cli.command()
@click.pass_context
def status(ctx):
    """Show current status of all monitored websites."""
    db = ctx.obj['db']
    try:
        sites = db.get_all_sites()
        if not sites:
            click.echo("No websites in monitoring list")
            return
        
        click.echo("Current website status:")
        click.echo("-" * 80)
        
        for site in sites:
            status_indicator = "🟢 ONLINE " if site['last_status'] == 'online' else "🔴 OFFLINE" if site['last_status'] == 'offline' else "⚪ UNKNOWN"
            last_check = format_timestamp(site['last_checked']) if site['last_checked'] else "Never checked"
            response_time = f"{site['response_time']:.3f}s" if site['response_time'] else "N/A"
            
            click.echo(f"{status_indicator:<10} {site['url']:<40}")
            click.echo(f"           Last check: {last_check}")
            click.echo(f"           Response time: {response_time}")
            if site['last_error']:
                click.echo(f"           Last error: {site['last_error']}")
            click.echo()
            
    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)

@cli.command()
@click.pass_context
def clear(ctx):
    """Clear all websites from the monitoring list."""
    db = ctx.obj['db']
    if click.confirm("Are you sure you want to remove all websites from the monitoring list?"):
        try:
            count = db.clear_all_sites()
            click.echo(f"✓ Removed {count} website(s) from monitoring list")
        except Exception as e:
            click.echo(f"Error clearing sites: {e}", err=True)

if __name__ == '__main__':
    cli()
