#!/usr/bin/env python3
"""
Application runner script
"""

import os
from app import app

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print("=" * 60)
    print("Course Management System")
    print("=" * 60)
    print(f"Environment: {'Development' if debug else 'Production'}")
    print(f"Running on: http://{host}:{port}")
    print(f"Admin URL: http://{host}:{port}/admin/login")
    print("=" * 60)
    print("\nPress CTRL+C to quit\n")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug
    )