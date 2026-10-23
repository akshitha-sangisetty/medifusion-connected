"""Production entry point that verifies the model artifact before serving."""

import os

import uvicorn

from app.model_bootstrap import ensure_checkpoint


def main() -> None:
    ensure_checkpoint()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
