"""
Quick test to debug SSE double-data issue
"""
import asyncio
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import json

app = FastAPI()

async def test_event_stream():
    """Simple test stream"""
    yield f"data: {json.dumps({'type': 'test', 'message': 'Hello World'})}\n\n"
    await asyncio.sleep(1)
    yield f"data: {json.dumps({'type': 'complete', 'message': 'Done'})}\n\n"

@app.get("/test-sse")
async def test_sse():
    return EventSourceResponse(test_event_stream())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8889)