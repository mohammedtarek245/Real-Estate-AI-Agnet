"""
This script launches the Arabic Real Estate AI Agent using Flask's development server.
"""

import os
from app import app

if __name__ == "__main__":
    # Determine debug mode from environment variable (default is True)
    debug_mode = os.environ.get("DEBUG", "true").lower() in ["1", "true", "yes"]

    # Run Flask application
    app.run(
        host="0.0.0.0",  # Listen on all interfaces (required for Spaces and external access)
        port=5000,
        debug=debug_mode
    )
