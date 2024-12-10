import logging

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.brain.brain_model import BrainCreateRequest

# Get the logger configured in main.py
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/brains", description="Get a list of brains")
async def get_brains(start: int = 0, limit: int = 20, sort: str = "desc"):
    url = f"{settings.brain_base_url}/v1/brain"
    params = {"start": start, "limit": limit, "sort": sort}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=settings.brain_headers, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            logger.info(f"Successfully fetched brains: {response.json()}")
            return JSONResponse(content=response.json(), status_code=status.HTTP_200_OK)
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            )
            raise HTTPException(
                status_code=e.response.status_code, detail="Failed to fetch brains"
            )
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )


@router.get("/brains/{brain_id}", description="Get a brain by ID")
async def get_brain_by_id(brain_id: str):
    url = f"{settings.brain_base_url}/v1/brain/{brain_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=settings.brain_headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            logger.info(
                f"Successfully fetched brain with ID {brain_id}: {response.json()}"
            )
            return JSONResponse(content=response.json(), status_code=status.HTTP_200_OK)
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            )
            raise HTTPException(
                status_code=e.response.status_code, detail="Failed to fetch brain by ID"
            )
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )


@router.post("/brains/create", description="Create a new brain")
async def create_brain(brain: BrainCreateRequest):
    url = f"{settings.brain_base_url}/v1/brain"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, headers=settings.brain_headers, json=brain.model_dump()
            )
            response.raise_for_status()  # Raise an HTTPError for bad responses
            logger.info(f"Successfully created brain: {response.json()}")
            return JSONResponse(
                content=response.json(), status_code=status.HTTP_201_CREATED
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            )
            raise HTTPException(
                status_code=e.response.status_code, detail="Failed to create brain"
            )
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
