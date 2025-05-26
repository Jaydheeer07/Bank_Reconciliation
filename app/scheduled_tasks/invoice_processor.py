import asyncio
import logging
import concurrent.futures
from functools import partial

from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize
from app.core.oauth import api_client
from app.utils.http_client import post_json
from app.config import settings

logger = logging.getLogger(__name__)

async def process_xero_invoices(
    brain_id: str, xero_tenant_id: str
):
    """
    Fetches invoices from Xero and processes them through the brain API in batches.

    Args:
        brain_id: The ID of the brain to process invoices with
        xero_tenant_id: The Xero tenant ID to fetch invoices from
    """
    try:
        # Log the start of the process
        logger.info(
            f"Starting invoice processing for brain_id: {brain_id}, tenant_id: {xero_tenant_id}"
        )
        # Get Xero invoices
        accounting_api = AccountingApi(api_client)

        if not xero_tenant_id:
            logger.error("No organisation tenant found")
            return
        all_invoices = []
        page = 1
        page_size = 100
        more_pages = True
        logger.info(f"Starting to fetch invoices for tenant {xero_tenant_id}")
        while more_pages:
            logger.info(f"Fetching page {page} of invoices")
            invoices = accounting_api.get_invoices(
                xero_tenant_id,
                summary_only=False,
                page=page,
                page_size=page_size
            )
            serialized_invoices = serialize(invoices)
            
            # Get pagination info
            pagination = serialized_invoices.get("pagination", {})
            current_page = pagination.get("page", 1)
            page_count = pagination.get("pageCount", 1)
            
            # Get invoices from current page
            page_invoices = serialized_invoices.get("Invoices", [])
            all_invoices.extend(page_invoices)
            
            logger.info(f"Fetched {len(page_invoices)} invoices from page {current_page}/{page_count}")
            
            # Check if we need to fetch more pages
            if current_page >= page_count:
                more_pages = False
            else:
                page += 1
        num_invoices = len(all_invoices)
        logger.info(f"Processing all {num_invoices} invoices")
        if num_invoices > 0:
            # Create payload for the Xero processing endpoint
            payload = {
                "data": all_invoices,
                "brainId": brain_id,
                "documentType": "invoice"
            }
            
            # Send the request to the Xero processing endpoint
            result = await post_json(
                f"{settings.brain_base_url}/v1/file/xero/process",
                json=payload,
                log_message="process xero invoices",
            )
            
            logger.info(f"Successfully processed {num_invoices} invoices")
            return result
        else:
            logger.info(f"No invoices to process for brain {brain_id}")
            return None

    except Exception as e:
        logger.error(f"Error processing Xero invoices: {str(e)}", exc_info=True)
        return None


def process_xero_invoices_wrapper(brain_id: str, tenant_id: str):
    """
    Wrapper function to properly handle async execution in background threads.
    """
    loop = None
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Create partial function with args
            coro = partial(process_xero_invoices, brain_id, tenant_id)

            # Run with timeout to prevent hanging
            future = asyncio.wait_for(coro(), timeout=300)  # 5 minute timeout
            result = loop.run_until_complete(future)
            return result
        finally:
            # Make sure we clean up properly
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    except asyncio.TimeoutError:
        logger.error(f"Invoice processing timed out for brain_id: {brain_id}")
    except Exception as e:
        logger.error(f"Error processing invoices: {str(e)}", exc_info=True)
    finally:
        # Ensure the loop is properly cleaned up
        if loop and not loop.is_closed():
            try:
                if loop.is_running():
                    loop.stop()
                loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {str(e)}")
