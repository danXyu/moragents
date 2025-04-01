from typing import Any, Dict

from config import setup_logging
from controllers.user_controller import UserController
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = setup_logging()

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/users/{user_id}")
async def get_user(user_id: int) -> JSONResponse:
    """Get a user by ID"""
    logger.info(f"Received request to get user {user_id}")

    try:
        with UserController() as controller:
            user = controller.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            return JSONResponse(content=user.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/wallet/{wallet_address}")
async def get_user_by_wallet(wallet_address: str) -> JSONResponse:
    """Get a user by wallet address"""
    logger.info(f"Received request to get user by wallet {wallet_address}")

    try:
        with UserController() as controller:
            user = controller.get_user_by_wallet(wallet_address)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with wallet {wallet_address} not found",
                )
            return JSONResponse(content=user.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by wallet: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users() -> JSONResponse:
    """List all users"""
    logger.info("Received request to list all users")

    try:
        with UserController() as controller:
            users = controller.list_users()
            return JSONResponse(content=[user.model_dump() for user in users])

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users")
async def create_user(wallet_address: str) -> JSONResponse:
    """Create a new user"""
    logger.info(f"Received request to create user with wallet {wallet_address}")

    try:
        with UserController() as controller:
            user = controller.create_user(wallet_address)
            return JSONResponse(content=user.model_dump(), status_code=201)

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
async def update_user(user_id: int, wallet_address: str) -> JSONResponse:
    """Update an existing user"""
    logger.info(f"Received request to update user {user_id}")

    try:
        with UserController() as controller:
            user = controller.update_user(user_id, wallet_address)
            if not user:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            return JSONResponse(content=user.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(user_id: int) -> JSONResponse:
    """Delete a user"""
    logger.info(f"Received request to delete user {user_id}")

    try:
        with UserController() as controller:
            success = controller.delete_user(user_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            return JSONResponse(content={"status": "success"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/settings/{settings_key}")
async def get_user_setting(user_id: int, settings_key: str) -> JSONResponse:
    """Get a user setting by key"""
    logger.info(f"Received request to get setting {settings_key} for user {user_id}")

    try:
        with UserController() as controller:
            setting = controller.get_setting(user_id, settings_key)
            if not setting:
                raise HTTPException(
                    status_code=404,
                    detail=f"Setting {settings_key} not found for user {user_id}",
                )
            return JSONResponse(content=setting.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user setting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/settings")
async def list_user_settings(user_id: int) -> JSONResponse:
    """List all settings for a user"""
    logger.info(f"Received request to list settings for user {user_id}")

    try:
        with UserController() as controller:
            settings = controller.list_user_settings(user_id)
            return JSONResponse(content=[setting.model_dump() for setting in settings])

    except Exception as e:
        logger.error(f"Error listing user settings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/settings/{settings_key}")
async def create_user_setting(user_id: int, settings_key: str, settings_value: Dict[str, Any]) -> JSONResponse:
    """Create a new user setting"""
    logger.info(f"Received request to create setting {settings_key} for user {user_id}")

    try:
        with UserController() as controller:
            setting = controller.create_setting(user_id, settings_key, settings_value)
            return JSONResponse(content=setting.model_dump(), status_code=201)

    except Exception as e:
        logger.error(f"Error creating user setting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/settings/{settings_key}")
async def update_user_setting(user_id: int, settings_key: str, settings_value: Dict[str, Any]) -> JSONResponse:
    """Update an existing user setting"""
    logger.info(f"Received request to update setting {settings_key} for user {user_id}")

    try:
        with UserController() as controller:
            setting = controller.update_setting(user_id, settings_key, settings_value)
            if not setting:
                raise HTTPException(
                    status_code=404,
                    detail=f"Setting {settings_key} not found for user {user_id}",
                )
            return JSONResponse(content=setting.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user setting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/settings/{settings_key}")
async def delete_user_setting(user_id: int, settings_key: str) -> JSONResponse:
    """Delete a user setting"""
    logger.info(f"Received request to delete setting {settings_key} for user {user_id}")

    try:
        with UserController() as controller:
            success = controller.delete_setting(user_id, settings_key)
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Setting {settings_key} not found for user {user_id}",
                )
            return JSONResponse(content={"status": "success"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user setting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
