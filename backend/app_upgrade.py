"""Upgraded Render entrypoint for BIS SmartGuide.

Loads the existing app unchanged, then registers the modular V4 compliance
intelligence blueprint before Gunicorn starts serving requests.
"""
from app import app
from compliance_upgrade import register

register(app)
