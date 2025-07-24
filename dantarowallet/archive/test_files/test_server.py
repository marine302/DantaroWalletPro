"""
간단한 테스트 서버 - 문제 진단용
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Server")

@app.get("/")
async def root():
    return {"message": "Test server is running"}

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Server is healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
