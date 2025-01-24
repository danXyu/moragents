import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import load_agent_routes, setup_logging
from src.stores import workflow_manager_instance

# Configure routes
from src.routes import (
    chat_routes,
    agent_manager_routes,
    key_manager_routes,
    wallet_manager_routes,
    workflow_manager_routes,
    conversation_routes,
)

# Configure logging
logger = setup_logging()
logger.info("Logging configured successfully")

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup upload directory
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Upload folder created at {UPLOAD_FOLDER}")

# Include core routers
ROUTERS = [
    chat_routes.router,
    agent_manager_routes.router,
    key_manager_routes.router,
    conversation_routes.router,
    wallet_manager_routes.router,
    workflow_manager_routes.router,
]

# Dynamically load and add agent routers
agent_routers = load_agent_routes()
for router in agent_routers:
    app.include_router(router)

for router in ROUTERS:
    app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize workflow manager on startup"""
    logger.info("Starting workflow manager initialization")
    await workflow_manager_instance.initialize()
    logger.info("Workflow manager initialized successfully")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
