import debugpy
import uvicorn

if __name__ == "__main__":
    # Setup debugpy
    debugpy.listen(("127.0.0.1", 5678))
    print("⏳ Waiting for debugger attach...")
    debugpy.wait_for_client()
    print("🚀 Debugger attached! Starting Uvicorn server...")

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Enable auto-reload
        workers=4,  # Number of worker processes
        log_level="info",
    )
