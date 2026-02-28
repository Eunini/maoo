from __future__ import annotations

from fastapi import FastAPI

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="MAOO Mock API", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("mock_api.server:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()

