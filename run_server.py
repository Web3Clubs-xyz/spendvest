import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=80,
        reload=True,  # Enable auto-reload
        workers=4,  # Number of worker processes
        log_level="info",
    )
