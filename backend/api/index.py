# api/index.py
import sys
import os
from pathlib import Path

# Add parent directory (backend/) to Python path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app

# Vercel expects a handler named 'app'
handler = app
