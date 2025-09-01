#!/usr/bin/env python3
"""
Website Connectivity Monitor - Web Interface
A minimalist web interface for monitoring website connectivity.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import threading
import time
from database import DatabaseManager
from monitor import ConnectivityMonitor, SingleCheckMonitor
from utils import validate_url, normalize_url

app = Flask(__name__)

# Global variables for monitoring
monitor = None
monitor_thread = None
monitor_running = False
db = DatabaseManager()

@app.route('/')
def index():
    """Main dashboard page"""
    sites = db.get_all_sites()
    return render_template('index.html', sites=sites)

@app.route('/api/sites', methods=['GET'])
def get_sites():
    """API endpoint to get all sites"""
    sites = db.get_all_sites()
    return jsonify({'sites': sites})

@app.route('/api/sites', methods=['POST'])
def add_site():
    """API endpoint to add a new site"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Normalize URL
    url = normalize_url(url)
    
    if not validate_url(url):
        return jsonify({'error': 'Invalid URL format'}), 400
    
    try:
        if db.add_site(url):
            return jsonify({'message': 'Site added successfully', 'url': url})
        else:
            return jsonify({'error': 'Site already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/<path:url>', methods=['DELETE'])
def remove_site(url):
    """API endpoint to remove a site"""
    try:
        if db.remove_site(url):
            return jsonify({'message': 'Site removed successfully'})
        else:
            return jsonify({'error': 'Site not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check', methods=['POST'])
def check_sites():
    """API endpoint to check all sites once"""
    try:
        checker = SingleCheckMonitor(db)
        sites = db.get_all_sites()
        
        if not sites:
            return jsonify({'message': 'No sites to check'})
        
        # Check all sites
        results = []
        for site in sites:
            url = site['url']
            status, response_time, error = checker.check_site(url)
            db.update_site_status(url, status, response_time, error)
            
            results.append({
                'url': url,
                'status': status,
                'response_time': response_time,
                'error': error
            })
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/start', methods=['POST'])
def start_monitoring():
    """API endpoint to start continuous monitoring"""
    global monitor, monitor_thread, monitor_running
    
    if monitor_running:
        return jsonify({'error': 'Monitoring is already running'}), 409
    
    try:
        sites = db.get_all_sites()
        if not sites:
            return jsonify({'error': 'No sites to monitor'}), 400
        
        data = request.get_json() or {}
        interval = data.get('interval', 60)
        timeout = data.get('timeout', 10)
        
        monitor = ConnectivityMonitor(db, interval, timeout)
        monitor_thread = threading.Thread(target=monitor.run, daemon=True)
        monitor_thread.start()
        monitor_running = True
        
        return jsonify({'message': 'Monitoring started', 'interval': interval})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitoring():
    """API endpoint to stop continuous monitoring"""
    global monitor, monitor_running
    
    if not monitor_running:
        return jsonify({'error': 'Monitoring is not running'}), 409
    
    try:
        if monitor:
            monitor.stop()
        monitor_running = False
        return jsonify({'message': 'Monitoring stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/status', methods=['GET'])
def monitoring_status():
    """API endpoint to get monitoring status"""
    return jsonify({'running': monitor_running})

@app.route('/api/sites/<path:url>/history', methods=['GET'])
def get_site_history(url):
    """API endpoint to get check history for a site"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = db.get_site_history(url, limit)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)