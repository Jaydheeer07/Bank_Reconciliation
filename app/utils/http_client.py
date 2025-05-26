import logging
import httpx
from typing import Dict, Any, Optional, Tuple

from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

# Create a shared client configuration
CLIENT_TIMEOUT = 180.0  # seconds
CLIENT_LIMITS = httpx.Limits(max_keepalive_connections=5, max_connections=10)

async def make_api_request(
    method: str, 
    url: str, 
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    content: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    use_brain_headers: bool = True,
    timeout: float = CLIENT_TIMEOUT,
    log_message: str = "API request",
    parse_json: bool = True
) -> Tuple[Dict[str, Any], int]:
    """
    Make an API request with standardized error handling.
    
    Args:
        method: HTTP method (get, post, etc.)
        url: The URL to request
        params: Optional query parameters
        json: Optional JSON body
        data: Optional form data
        content: Optional raw content
        headers: Optional headers to include
        use_brain_headers: Whether to include brain API headers
        timeout: Request timeout in seconds
        log_message: Message to log on success
        parse_json: Whether to parse the response as JSON

    Returns:
        Tuple[Dict[str, Any], int]: The JSON response and status code
        
    Raises:
        HTTPException: If the request fails
    """
    request_headers = {}
    if headers:
        request_headers.update(headers)
    if use_brain_headers:
        request_headers.update(settings.brain_headers)
        
    async with httpx.AsyncClient(timeout=timeout, limits=CLIENT_LIMITS) as client:
        try:
            request_kwargs = {
                "headers": request_headers,
            }
            if params is not None:
                request_kwargs["params"] = params
            if method.lower() != "get" and json is not None:
                request_kwargs["json"] = json
            if data is not None:
                request_kwargs["data"] = data
            if content is not None:
                request_kwargs["content"] = content
                
            response = await getattr(client, method.lower())(url, **request_kwargs)
            response.raise_for_status()
            logger.info(f"Successfully {log_message}")
            
            # Return either JSON or raw content based on parse_json flag
            if parse_json:
                try:
                    return response.json(), response.status_code
                except json.JSONDecodeError:
                    logger.warning(f"Response is not valid JSON: {response.text[:100]}...")
                    return response.text, response.status_code
            else:
                return response.content, response.status_code
            
        except httpx.TimeoutException:
            logger.error(f"Request timed out: {log_message}")
            raise HTTPException(status_code=504, detail="Request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to {log_message}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

async def get_json(url: str, params: Optional[Dict[str, Any]] = None, log_message: str = "fetch data", **kwargs) -> Dict[str, Any]:
    """Make a GET request and return the JSON response."""
    data, _ = await make_api_request("get", url, params=params, log_message=log_message, **kwargs)
    return data

async def post_json(url: str, json: Dict[str, Any], log_message: str = "post data", **kwargs) -> Dict[str, Any]:
    """Make a POST request with JSON data and return the JSON response."""
    data, _ = await make_api_request("post", url, json=json, log_message=log_message, **kwargs)
    return data

async def put_json(url: str, json: Dict[str, Any], log_message: str = "update data", **kwargs) -> Dict[str, Any]:
    """Make a PUT request with JSON data and return the JSON response."""
    data, _ = await make_api_request("put", url, json=json, log_message=log_message, **kwargs)
    return data

class HttpClientError(Exception):
    """Base exception for HTTP client errors"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP error {status_code}: {detail}")

def http_exception_handler(error: HttpClientError) -> None:
    """Convert an HttpClientError to a FastAPI HTTPException."""
    raise HTTPException(status_code=error.status_code, detail=error.detail)