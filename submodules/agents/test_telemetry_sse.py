#!/usr/bin/env python3
"""
Test SSE telemetry data flow
"""
import asyncio
import json
import time
from services.orchestrator.progress_listener import (
    get_or_create_queue,
    emit_flow_start,
    emit_subtask_dispatch,
    emit_subtask_result,
    emit_synthesis_start,
    emit_synthesis_complete,
    emit_final_complete,
    event_stream,
    cleanup_queue
)

async def test_telemetry_flow():
    request_id = "test-123"
    
    # Start the flow
    await emit_flow_start(request_id)
    
    # Dispatch a subtask
    await emit_subtask_dispatch(
        request_id,
        "Analyze the crypto market trends",
        ["crypto_data", "codex"]
    )
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    # Send result with telemetry
    telemetry_data = {
        "processing_time": {
            "start_time": time.time() - 2.5,
            "end_time": time.time(),
            "duration": 2.5
        },
        "token_usage": {
            "total_tokens": 1234,
            "prompt_tokens": 890,
            "completion_tokens": 344,
            "cached_prompt_tokens": 0
        }
    }
    
    await emit_subtask_result(
        request_id,
        "Analyze the crypto market trends",
        "Bitcoin is showing bullish sentiment with increased volume...",
        ["crypto_data", "codex"],
        telemetry_data
    )
    
    # Start synthesis
    await emit_synthesis_start(request_id)
    await asyncio.sleep(0.5)
    
    # Complete synthesis
    await emit_synthesis_complete(
        request_id,
        "Based on the analysis, the crypto market shows positive momentum..."
    )
    
    # Final complete
    await emit_final_complete(request_id)
    
    print("Test events sent!")

async def consume_stream(request_id):
    """Consume the event stream"""
    print("Starting to consume events...")
    async for event in event_stream(request_id):
        print(f"Event: {event}")

async def main():
    request_id = "test-123"
    
    # Start consumer in background
    consumer_task = asyncio.create_task(consume_stream(request_id))
    
    # Wait a bit then send events
    await asyncio.sleep(0.5)
    await test_telemetry_flow()
    
    # Wait for consumer to finish
    try:
        await asyncio.wait_for(consumer_task, timeout=10)
    except asyncio.TimeoutError:
        print("Consumer timeout")
    
    cleanup_queue(request_id)
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())