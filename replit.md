# Website Connectivity Monitor

## Overview

This is a command-line tool for monitoring website connectivity with persistent storage and configurable intervals. The application allows users to add websites to a monitoring list, check their connectivity status, and maintain historical records of their uptime/downtime. It provides real-time monitoring capabilities with graceful shutdown handling and comprehensive logging of website performance metrics including response times and error messages.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern
The application follows a modular architecture with clear separation of concerns:

- **Database Layer** (`database.py`): Handles all SQLite operations using a thread-safe DatabaseManager class with connection pooling and proper resource management
- **Monitoring Engine** (`monitor.py`): Implements the core connectivity checking logic with configurable intervals and timeout settings
- **CLI Interface** (`main.py`): Provides a Click-based command-line interface with proper signal handling for graceful shutdowns
- **Utilities** (`utils.py`): Contains helper functions for URL validation, normalization, and timestamp formatting

### Data Storage Strategy
- **Database**: SQLite for lightweight, serverless data persistence
- **Schema Design**: Two-table structure with `sites` for monitored websites and `check_history` for historical status records
- **Thread Safety**: Database operations are protected with threading locks to handle concurrent access during monitoring

### Monitoring Architecture
- **Threading Model**: Uses separate threads for continuous monitoring without blocking the CLI interface
- **Request Handling**: Leverages the `requests` library with configurable timeouts and proper error handling
- **Status Tracking**: Maintains both current status and historical records for trend analysis

### CLI Design Pattern
- **Command Structure**: Uses Click framework for intuitive command grouping and parameter validation
- **Context Management**: Implements Click context passing for shared database instances across commands
- **Signal Handling**: Properly handles SIGINT (Ctrl+C) for graceful shutdown of monitoring threads

## External Dependencies

### Core Libraries
- **Click**: Command-line interface framework for building intuitive CLI commands
- **Requests**: HTTP library for making connectivity checks to monitored websites
- **SQLite3**: Built-in Python database interface for local data persistence
- **Threading**: Python's built-in threading module for concurrent monitoring operations

### System Dependencies
- **Python 3.x**: Runtime environment
- **SQLite**: Embedded database engine (typically bundled with Python)

### Network Requirements
- **Internet Connectivity**: Required for monitoring external websites
- **HTTP/HTTPS Access**: Application makes outbound requests to monitored URLs