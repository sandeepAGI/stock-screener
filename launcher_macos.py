#!/usr/bin/env python3
"""
StockAnalyzer Pro - macOS Launcher
Starts Streamlit server and opens browser automatically

This launcher handles:
- Starting Streamlit in the correct mode (script vs bundled)
- Opening the default web browser automatically
- Graceful shutdown on Ctrl+C
- Port conflict handling
"""

import sys
import os
import subprocess
import webbrowser
import time
import socket
from pathlib import Path
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True


def find_available_port(start_port: int = 8501, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")


def get_app_directory() -> Path:
    """
    Get the application directory

    When running as a PyInstaller bundle, files are extracted to sys._MEIPASS.
    When running as a script, use the script's directory.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller bundle)
        app_dir = Path(sys._MEIPASS)
        logger.info(f"Running as bundled executable from: {app_dir}")
    else:
        # Running as script
        app_dir = Path(__file__).parent.absolute()
        logger.info(f"Running as script from: {app_dir}")

    return app_dir


def get_database_directory() -> Path:
    """
    Get the database directory (in user's home for bundled app)

    For bundled applications, we store the database in the user's home directory
    to ensure it persists across app updates and is writable.
    """
    if getattr(sys, 'frozen', False):
        # For bundled app, use user's home directory
        db_dir = Path.home() / '.stockanalyzer' / 'data'
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory: {db_dir}")
        return db_dir
    else:
        # For development, use the local data directory
        db_dir = Path(__file__).parent / 'data'
        return db_dir


def main():
    """Main launcher function"""
    print("=" * 60)
    print("  StockAnalyzer Pro - macOS Edition")
    print("  Starting application...")
    print("=" * 60)
    print()

    # Get application directory
    app_dir = get_app_directory()
    dashboard_path = app_dir / "analytics_dashboard.py"

    # Verify dashboard file exists
    if not dashboard_path.exists():
        logger.error(f"Dashboard file not found: {dashboard_path}")
        print()
        print("❌ Error: Application files not found.")
        print("Please ensure the application is properly installed.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Set up database directory for bundled app
    if getattr(sys, 'frozen', False):
        db_dir = get_database_directory()
        # Set environment variable so the app knows where to find the database
        os.environ['STOCKANALYZER_DATA_DIR'] = str(db_dir)

    # Find available port
    try:
        port = find_available_port()
        logger.info(f"Using port: {port}")
    except RuntimeError as e:
        logger.error(f"Could not find available port: {e}")
        print()
        print("❌ Error: Could not find available port for the application.")
        print("Please close other applications using ports 8501-8510 and try again.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Prepare Streamlit command
    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(dashboard_path),
        "--server.headless", "true",
        "--server.port", str(port),
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false",
        "--browser.serverAddress", "localhost",
        "--server.enableXsrfProtection", "true",
        "--server.enableCORS", "false"
    ]

    print(f"✓ Starting Streamlit server on port {port}...")

    # Start Streamlit process
    try:
        process = subprocess.Popen(
            streamlit_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
    except Exception as e:
        logger.error(f"Failed to start Streamlit: {e}")
        print()
        print(f"❌ Error: Failed to start application: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Wait for Streamlit to be ready
    print("✓ Waiting for server to initialize...")
    max_wait_time = 30  # seconds
    start_time = time.time()
    server_ready = False

    while time.time() - start_time < max_wait_time:
        # Check if process is still running
        if process.poll() is not None:
            print()
            print("❌ Error: Server process terminated unexpectedly")
            print("\nServer output:")
            for line in process.stdout:
                print(f"  {line.rstrip()}")
            input("\nPress Enter to exit...")
            sys.exit(1)

        # Check if port is now in use (server is listening)
        if is_port_in_use(port):
            server_ready = True
            break

        time.sleep(0.5)

    if not server_ready:
        print()
        print("❌ Error: Server did not start within the expected time")
        process.terminate()
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Server is ready, open browser
    url = f"http://localhost:{port}"
    print(f"✓ Server ready at {url}")
    print("✓ Opening web browser...")

    # Give it a moment before opening browser
    time.sleep(1)

    try:
        webbrowser.open(url)
        print()
        print("=" * 60)
        print("  ✓ StockAnalyzer Pro is now running!")
        print("=" * 60)
        print()
        print(f"  Open in browser: {url}")
        print()
        print("  Press Ctrl+C to stop the application")
        print("=" * 60)
        print()
    except Exception as e:
        logger.warning(f"Could not open browser automatically: {e}")
        print()
        print("⚠️  Could not open browser automatically")
        print(f"   Please open manually: {url}")
        print()

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print()
        print()
        print("=" * 60)
        print("  Shutting down StockAnalyzer Pro...")
        print("=" * 60)
        process.terminate()
        try:
            process.wait(timeout=5)
            print("  ✓ Application stopped successfully")
        except subprocess.TimeoutExpired:
            print("  ⚠️  Force killing application...")
            process.kill()
        print("=" * 60)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Wait for the process
    try:
        process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C
        signal_handler(None, None)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print()
        print(f"❌ Unexpected error: {e}")
        print()
        print("Please report this issue with the error message above.")
        input("\nPress Enter to exit...")
        sys.exit(1)
