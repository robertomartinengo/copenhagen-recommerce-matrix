from fastapi import FastAPI

app = FastAPI(
    title="Copenhagen Re-Commerce Matrix API",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "Copenhagen Re-Commerce Matrix",
        "version": "0.1.0"
    }