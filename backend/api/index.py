# api/index.py
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

# Vercel expects a handler named 'app'
handler = app