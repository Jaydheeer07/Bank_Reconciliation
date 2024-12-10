import logging
import os

import httpx
from fastapi import APIRouter, Form, HTTPException, Query, UploadFile

from app.config import settings

# Get the logger configured in main.py
logger = logging.getLogger(__name__)

router = APIRouter()


# Helper function to upload a file using a signed URL
async def upload_to_signed_url(signed_url: str, file_path: str):
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as file:
                response = await client.put(
                    signed_url,
                    content=file.read(),
                    headers={"Content-Type": "application/octet-stream"},
                )
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.post("/upload-file", description="Upload a file")
async def upload_file(
    file: UploadFile,
    brain_id: str = Form(...),  # Brain ID to associate the file with
    document_type: str = Form(...),  # Document type (e.g., "invoice" or "statement")
):
    """
    Upload a file to the Dexterous API.

    Steps:
    1. Fetch a signed URL.
    2. Upload the file to the signed URL.
    3. Notify the server that the upload is complete.
    """
    try:
        # Save the uploaded file locally
        temp_file_path = f"./{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Step 1: Fetch a signed URL
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.brain_base_url}/v1/file/url?fileName={file.filename}",
                headers=settings.brain_headers,
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch signed URL: {response.text}",
                )
            signed_url_data = response.json()
            signed_url = signed_url_data["url"]
            upload_id = signed_url_data["uploadId"]

        # Step 2: Upload the file to the signed URL
        await upload_to_signed_url(signed_url, temp_file_path)

        # Step 3: Notify the server about the completed upload
        payload = {
            "uploadId": upload_id,
            "brainId": brain_id,
            "documentType": document_type,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.brain_base_url}/v1/file/process",
                headers=settings.brain_headers,
                json=payload,
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to complete upload process: {response.text}",
                )

        # Clean up the temporary file
        os.remove(temp_file_path)

        return {"message": "File uploaded successfully", "details": response.json()}

    except Exception as e:
        # Clean up the temporary file in case of error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=500, detail=f"Error during file upload: {str(e)}"
        )


@router.get("/file/{file_id}", description="Get details of a specific file")
async def get_file(file_id: str):
    """
    Fetch details of a specific file by its file_id.
    """
    url = f"{settings.brain_base_url}/v1/file/{file_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=settings.brain_headers)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@router.get("/files", description="List all files in a brain")
async def list_files(
    brain_id: str = Query(..., description="Brain ID to filter files"),
    start: int = Query(0, description="Pagination start value"),
    limit: int = Query(20, description="Number of results to return"),
    sort: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
    filter_by: str = Query(
        "all", description="Filter by: 'invoice', 'statement', or 'all'"
    ),
):
    """
    List all files in a brain with optional filters and pagination.
    """
    url = f"{settings.brain_base_url}/v1/file"
    params = {
        "brainId": brain_id,
        "start": start,
        "limit": limit,
        "sort": sort,
        "filterBy": filter_by,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=settings.brain_headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
