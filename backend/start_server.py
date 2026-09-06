"""Reliable Render/Gunicorn startup for BIS SmartGuide.

Explicitly loads the conversation-routing startup patch before Gunicorn
imports the Flask application. This avoids relying on implicit startup
customization behavior.
"""

import sys

import sitecustomize  # noqa: F401,E402 - intentionally load the patch first


def main():
    sys.argv = [
        "gunicorn",
        "--chdir", "/app/backend",
        "--workers", "2",
        "--threads", "4",
        "--timeout", "120",
        "--bind", "0.0.0.0:5000",
        "app:app",
    ]
    from gunicorn.app.wsgiapp import run
    run()


if __name__ == "__main__":
    main()
