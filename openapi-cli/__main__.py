#!/usr/bin/env python3
"""
OpenAPI CLI Tool - Main entry point
Usage: python -m openapi_cli <url/path/to/openapi.json>
"""

import sys
from .cli import main

if __name__ == "__main__":
    main()

