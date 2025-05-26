import logging
import os
import json
from fastapi import APIRouter, Form, HTTPException, Query, UploadFile
from app.config import settings
from app.models.brain.brain_model import TextProcessRequest
from app.utils.http_client import get_json, post_json, make_api_request, HttpClientError, http_exception_handler

# Get the logger configured in main.py
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain/files")

@router.get("/", description="List all documents in a brain")
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
    
    data = await get_json(url, params=params, log_message="list files")
    return data


@router.post("/upload", description="Upload a document")
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
    temp_file_path = None
    try:
        # Validate document type
        if document_type not in ["invoice", "statement", "bill"]:
            raise ValueError("document_type should be either 'invoice' or 'statement' or 'bill'")
            
        # Save the uploaded file locally
        temp_file_path = f"./{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Step 1: Fetch a signed URL
        url = f"{settings.brain_base_url}/v1/file/url?fileName={file.filename}"
        signed_url_data = await get_json(url, log_message="fetch signed URL")
        signed_url = signed_url_data["url"]
        upload_id = signed_url_data["uploadId"]

        # Step 2: Upload the file to the signed URL
        # Read file content
        with open(temp_file_path, "rb") as file_content:
            file_bytes = file_content.read()
        
        # Use our utility function for the upload
        try:
            response = await make_api_request(
                "put",
                signed_url,
                content=file_bytes,
                headers={"Content-Type": "application/octet-stream"},
                use_brain_headers=False,  # Don't use brain headers for S3 upload
                log_message="upload file to storage",
                parse_json=False  # Don't try to parse the response as JSON
            )
            status_code = response[1] if isinstance(response, tuple) else 200
            logger.info(f"File upload successful with status code: {status_code}")
        except Exception as e:
            logger.error(f"Error uploading file to storage: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error uploading file to storage: {str(e)}")
        
        logger.info(f"File upload successful with status code: {status_code}")

        # Step 3: Notify the server about the completed upload
        payload = {
            "uploadId": upload_id,
            "brainId": brain_id,
            "documentType": document_type,
        }

        process_data = await post_json(
            f"{settings.brain_base_url}/v1/file/process",
            json=payload,
            log_message="complete file processing",
            timeout=120  # Longer timeout for processing
        )

        return {"message": "File uploaded successfully", "details": process_data}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HttpClientError as e:
        logger.error(f"HTTP client error: {e.detail}")
        http_exception_handler(e)
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during file upload: {str(e)}")
    finally:
        # Clean up the temporary file regardless of success or failure
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.debug(f"Temporary file {temp_file_path} removed")


@router.get("/{file_id}", description="Get details of a specific document")
async def get_file(file_id: str):
    """
    Fetch details of a specific file by its file_id.
    """
    url = f"{settings.brain_base_url}/v1/file/{file_id}"
    data = await get_json(url, log_message=f"fetch file {file_id}")
    return data


@router.post("/text/process", description="Process text content from various document types")
async def process_text(request: TextProcessRequest):
    """
    Process text content through the Dexterous API.

    Steps:
    1. Validate the document type
    2. Send the text content for processing
    """
    try:
        logger.info(f"Processing text for brain_id: {request.brain_id}, document_type: {request.document_type}")
        
        # Validate document type
        if request.document_type not in ["invoice", "statement"]:
            logger.error(f"Invalid document_type: {request.document_type}")
            raise ValueError("document_type should be either 'invoice' or 'statement'")

        # Clean and validate the text content
        try:
            # Handle both string and dict inputs
            if isinstance(request.text, str):
                try:
                    # If it's a string, try to parse it as JSON
                    parsed_text = json.loads(request.text)
                    logger.info("Successfully parsed JSON from string input")
                except json.JSONDecodeError:
                    # If it's not valid JSON, use it as is
                    logger.warning("Text is not JSON format, using as plain text")
                    parsed_text = request.text
            else:
                # If it's already a dict, use it directly
                parsed_text = request.text
                logger.info("Using provided dict input")

            # Convert to properly formatted JSON string
            text = json.dumps(parsed_text, indent=2)
            
            # Log the number of invoices if present
            if isinstance(parsed_text, dict) and 'Invoices' in parsed_text:
                logger.info(f"Processing {len(parsed_text['Invoices'])} invoices")

        except Exception as e:
            logger.error(f"Error processing text content: {str(e)}")
            raise ValueError(f"Invalid text content: {str(e)}")

        # Send the text for processing
        payload = {
            "text": text,
            "brainId": request.brain_id,
            "documentType": request.document_type,
        }

        logger.info("Sending request to brain API")
        data = await post_json(
            f"{settings.brain_base_url}/v1/file/text/process",
            json=payload,
            log_message="process text content",
        )
        
        logger.info("Successfully processed text content")
        return data

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text content: {str(e)}")