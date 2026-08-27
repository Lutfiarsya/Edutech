import uvicorn

from ai_worker.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "ai_worker.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
