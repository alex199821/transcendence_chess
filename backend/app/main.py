from fastapi import FastAPI

app = FastAPI(
    title="Chess API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
