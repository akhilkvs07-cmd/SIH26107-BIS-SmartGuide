"""Reliable Render/Gunicorn startup for BIS SmartGuide."""

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
        "app_upgrade:app",
    ]
    from gunicorn.app.wsgiapp import run
    run()


if __name__ == "__main__":
    main()
