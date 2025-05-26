import uvicorn
import multiprocessing
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Get environment settings
    ENV = os.getenv("ENV", "development")
    
    if ENV == "development":
        # Development configuration
        logger.info(" Running in DEVELOPMENT environment")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True  # Enable auto-reload
        )
    else:
        # Production configuration
        workers = (multiprocessing.cpu_count() * 2) + 1
        logger.info(" Running in PRODUCTION environment with %d workers", workers)
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            workers=workers,
            loop="uvloop",
            http="httptools"
        )