"""Convenience entrypoint for local execution."""

from __future__ import annotations

from server.app import main as run_server


def main() -> None:
    """Start the FastAPI server on port 7860."""
    run_server()


if __name__ == "__main__":
    main()
