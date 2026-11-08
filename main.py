"""
=============================================================================
EF101-P07: Classroom/Laboratory Booking System
Web Application Launcher (Runs in your Web Browser)
=============================================================================

Usage:
    python main.py        -> Starts the web server and automatically opens your browser
=============================================================================
"""

import sys
import webbrowser
import threading
import database
import app


def print_banner():
    print("=" * 65)
    print("  EF101-P07: Classroom/Laboratory Booking Information System")
    print("  Browser-Based Web Application (Python + Flask + SQLite)")
    print("=" * 65)


def main():
    print_banner()

    # Ensure database tables and 12 demo rooms are initialized
    database.init_db(force_reset=False)

    args = sys.argv[1:]

    # Run tests if requested
    if "--test" in args:
        print("[*] Running automated assignment tests...\n")
        import test_system
        test_system.run_tests()
        return

    # Start browser-based web application
    port = 5000
    url = f"http://127.0.0.1:{port}"
    print(f"\n[*] Starting Python Web Server...")
    print(f"[*] Opening your web browser automatically at: {url}")
    print("[*] If your browser does not open automatically, visit:")
    print(f"    --> {url}")
    print("[*] Press Ctrl + C in this terminal to stop the server.")
    print("=" * 65 + "\n")

    # Open the browser exactly once before starting the server
    try:
        webbrowser.open_new_tab(url)
    except Exception:
        pass

    # Start Flask Web Server (use_reloader=False prevents repeated restarts & opening multiple tabs)
    app.app.run(debug=True, use_reloader=False, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
