import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.brain.brain_model import BrainCreateRequest
from app.utils.http_client import get_json, post_json, HttpClientError, http_exception_handler

# Get the logger configured in main.py
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain/me")

@router.get("/", description="Get a list of brains")
async def get_brains(start: int = 0, limit: int = 20, sort: str = "desc"):
    url = f"{settings.brain_base_url}/v1/brain"
    params = {"start": start, "limit": limit, "sort": sort}

    try:
        data = await get_json(url, params=params, log_message="fetch brains")
        return JSONResponse(content=data, status_code=status.HTTP_200_OK)
    except HttpClientError as e:
        http_exception_handler(e)


@router.get("/{brain_id}", description="Get a brain by ID")
async def get_brain_by_id(brain_id: str):
    url = f"{settings.brain_base_url}/v1/brain/{brain_id}"
    
    try:
        data = await get_json(url, log_message=f"fetch brain with ID {brain_id}")
        return JSONResponse(content=data, status_code=status.HTTP_200_OK)
    except HttpClientError as e:
        http_exception_handler(e)


@router.post("/create", description="Create a new brain")
async def create_brain(brain: BrainCreateRequest):
    url = f"{settings.brain_base_url}/v1/brain"
    
    try:
        data = await post_json(
            url, 
            json=brain.model_dump(), 
            log_message="create brain"
        )
        return JSONResponse(content=data, status_code=status.HTTP_201_CREATED)
    except HttpClientError as e:
        http_exception_handler(e)