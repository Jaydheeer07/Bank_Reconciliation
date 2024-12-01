import logging
from collections import defaultdict
from typing import List

import httpx
from fastapi import APIRouter, HTTPException, Query

from backend.config import brain_base_url, brain_headers
from backend.deciphr.models.brain_model import ReconciliationVerification

# Get the logger configured in main.py
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/transactions/invoices", description="Get invoice transactions")
async def get_invoice_transactions(
    brain_id: str = Query(..., description="Brain ID to filter transactions"),
    start: int = Query(0, description="Pagination start value"),
    limit: int = Query(20, description="Number of results to return"),
    sort: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
):
    """
    Fetch paginated invoice transactions for a brain and consolidate line items by invoiceNumber.
    """
    url = f"{brain_base_url}/v1/transaction/invoice"
    params = {
        "brainId": brain_id,
        "start": start,
        "limit": limit,
        "sort": sort,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=brain_headers, params=params)
            response.raise_for_status()
            data = response.json()["data"]

        # Group invoices by invoiceNumber
        consolidated_invoices = defaultdict(lambda: None)

        for item in data:
            invoice_number = item["invoiceNumber"]

            if invoice_number not in consolidated_invoices:
                # Create a new entry for the invoice without the lineItem
                consolidated_invoices[invoice_number] = {
                    k: v for k, v in item.items() if k != "lineItem"
                }
                # Initialize lineItems as a list
                consolidated_invoices[invoice_number]["lineItems"] = []

            # Append the line item to the lineItems list
            consolidated_invoices[invoice_number]["lineItems"].append(item["lineItem"])

        # Convert back to a list
        consolidated_data = list(consolidated_invoices.values())

        return {
            "data": consolidated_data,
            "hasMore": response.json()["hasMore"],
            "total": len(consolidated_data),
        }

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@router.get("/transactions/statements", description="Get statement transactions")
async def get_statement_transactions(
    brain_id: str = Query(..., description="Brain ID to filter transactions"),
    start: int = Query(0, description="Pagination start value"),
    limit: int = Query(20, description="Number of results to return"),
    sort: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
):
    """
    Fetch paginated statement transactions for a brain.
    """
    url = f"{brain_base_url}/v1/transaction/statement"
    params = {
        "brainId": brain_id,
        "start": start,
        "limit": limit,
        "sort": sort,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=brain_headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@router.get("/transactions/recon", description="Get reconciliation transactions")
async def get_reconciliation(
    brain_id: str = Query(..., description="Brain ID for reconciliation"),
    start_period: int = Query(0, description="Start of the period (Unix timestamp)"),
    end_period: int = Query(
        None, description="End of the period (Unix timestamp, defaults to now)"
    ),
    filter_by: str = Query(
        "all", description="Filter: 'all' or 'verified' (defaults to 'all')"
    ),
):
    """
    Fetch reconciliation data for a brain within a specified date range and consolidate matchingInvoiceItems by invoiceNumber.
    """
    url = f"{brain_base_url}/v1/transaction/recon"
    params = {
        "brainId": brain_id,
        "startPeriod": start_period,
        "endPeriod": end_period,
        "filter": filter_by,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=brain_headers, params=params)
            response.raise_for_status()
            data = response.json()["data"]

        # Process the data to consolidate matchingInvoiceItems by invoiceNumber
        for record in data:
            matching_invoices = record["matchingInvoiceItems"]

            # Group invoices by invoiceNumber
            grouped_invoices = defaultdict(lambda: None)
            for invoice in matching_invoices:
                invoice_number = invoice["invoiceNumber"]

                if invoice_number not in grouped_invoices:
                    grouped_invoices[invoice_number] = {
                        k: v for k, v in invoice.items() if k != "lineItem"
                    }
                    grouped_invoices[invoice_number]["lineItems"] = []

                grouped_invoices[invoice_number]["lineItems"].append(
                    invoice["lineItem"]
                )

            # Replace matchingInvoiceItems with consolidated data
            record["matchingInvoiceItems"] = list(grouped_invoices.values())

        return {"data": data}

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@router.post("/transactions/verify", description="Verify reconciliation")
async def verify_reconciliation(mapping: List[ReconciliationVerification]):
    """
    Verify one or more reconciled transactions.
    """
    url = f"{brain_base_url}/v1/transaction/verify"
    payload = {"mapping": [m.model_dump() for m in mapping]}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=brain_headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
