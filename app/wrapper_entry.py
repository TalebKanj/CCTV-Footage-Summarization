#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wrapper entry point that handles PyInstaller frozen mode."""

import sys
import os

def get_base_path():
    """Get the base path for the application."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    # Running as script
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_paths():
    """Setup all necessary paths for the application."""
    base_path = get_base_path()
    
    # Add project root to Python path for imports
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
    
    # Set working directory to executable location
    os.chdir(base_path)

if __name__ == "__main__":
    setup_paths()
    
    # Now import and run the actual main
    from app import main
    sys.exit(main.main())