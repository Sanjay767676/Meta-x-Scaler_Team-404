"""Server entrypoint expected by OpenEnv validator."""

from __future__ import annotations

import uvicorn

from app import app


def main() -> None:
    """Run API server for local/dev validation."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
