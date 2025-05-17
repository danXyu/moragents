"""
Progress listener for orchestration events to enable streaming responses
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Global queue for events - will be created per request
progress_queues: Dict[str, asyncio.Queue] = {}

def get_or_create_queue(request_id: str) -> asyncio.Queue:
    """Get or create a queue for a specific request"""
    if request_id not in progress_queues:
        progress_queues[request_id] = asyncio.Queue()
    return progress_queues[request_id]

def cleanup_queue(request_id: str):
    """Remove a queue when request is complete"""
    if request_id in progress_queues:
        del progress_queues[request_id]

# Custom events for orchestration flow
async def emit_flow_start(request_id: str):
    """Emit event when flow starts"""
    if request_id:
        queue = get_or_create_queue(request_id)
        await queue.put({
            "type": "flow_start",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Starting multi-agent orchestration..."
            }
        })

async def emit_flow_end(request_id: str):
    """Emit event when flow ends"""
    if request_id:
        queue = get_or_create_queue(request_id)
        await queue.put({
            "type": "flow_end",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Multi-agent orchestration complete"
            }
        })

async def emit_subtask_dispatch(request_id: str, subtask: str, agents: list):
    """Emit event when a subtask is dispatched"""
    if request_id:
        queue = get_or_create_queue(request_id)
        await queue.put({
            "type": "subtask_dispatch",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "subtask": subtask[:200],
                "agents": agents,
                "message": f"Dispatching: {subtask[:100]}..."
            }
        })

async def emit_subtask_result(request_id: str, subtask: str, output: str, agents: list, telemetry: Optional[Dict[str, Any]] = None):
    """Emit event when a subtask completes"""
    if request_id:
        queue = get_or_create_queue(request_id)
        event_data = {
            "subtask": subtask[:200],
            "output": output[:500],
            "agents": agents,
            "message": f"Result: {subtask[:100]}..."
        }
        
        # Add telemetry data if available - ensure correct format
        if telemetry:
            formatted_telemetry = {}
            
            # Format processing time
            if telemetry.get("processing_time"):
                formatted_telemetry["processing_time"] = {
                    "duration": telemetry["processing_time"].get("duration", 0)
                }
            
            # Format token usage
            if telemetry.get("token_usage"):
                formatted_telemetry["token_usage"] = {
                    "total_tokens": telemetry["token_usage"].get("total_tokens", 0),
                    "prompt_tokens": telemetry["token_usage"].get("prompt_tokens", 0),
                    "completion_tokens": telemetry["token_usage"].get("completion_tokens", 0),
                }
            
            event_data["telemetry"] = formatted_telemetry
        
        await queue.put({
            "type": "subtask_result",
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        })

async def emit_synthesis_start(request_id: str):
    """Emit event when synthesis begins"""
    if request_id:
        queue = get_or_create_queue(request_id)
        await queue.put({
            "type": "synthesis_start",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Synthesizing final answer..."
            }
        })

async def emit_synthesis_complete(request_id: str, final_answer: str):
    """Emit event when synthesis completes"""
    if request_id:
        queue = get_or_create_queue(request_id)
        await queue.put({
            "type": "synthesis_complete",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "final_answer": final_answer,
                "message": "Final answer ready"
            }
        })

async def emit_final_complete(request_id: str):
    """Emit final completion event"""
    if request_id:
        queue = get_or_create_queue(request_id)
        await queue.put({
            "type": "stream_complete",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Stream complete"
            }
        })

async def event_stream(request_id: str):
    """Generator that yields events for SSE"""
    queue = get_or_create_queue(request_id)
    
    try:
        while True:
            try:
                # Wait for events with a timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                # Format for SSE - just send the data line
                yield f"data: {json.dumps(event)}\n\n"
                
                # Check if this is the final event
                if event['type'] == 'stream_complete':
                    break
                    
            except asyncio.TimeoutError:
                # Send a heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                
    except Exception as e:
        logger.error(f"Error in event stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        # Cleanup the queue
        cleanup_queue(request_id)