import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Body
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_db
from app.core.oauth import require_valid_token
from app.models.brain.brain_model import ReconciliationVerification
from app.models.database.reconciliation_models import DraftReconciliationEntry
from app.utils.xero.tenant_utils import get_active_tenant_id, get_tenant_metadata
from app.utils.http_client import get_json, post_json, http_exception_handler, HttpClientError

# Get the logger configured in main.py
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain/transactions")

@router.get("/stats", description="Get brain statistics")
async def get_brain_stats(
    brain_id: str = Query(..., description="Brain ID to get statistics for"),
):
    """
    Fetch statistics for a brain, including reconciliation status counts.
    """
    url = f"{settings.brain_base_url}/v1/brain/stats/{brain_id}"
    
    try:
        data = await get_json(url, log_message="fetch brain statistics")
        return data
    except HttpClientError as e:
        http_exception_handler(e)

@router.get("/invoices", description="Get invoice transactions")
async def get_invoice_transactions(
    brain_id: str = Query(..., description="Brain ID to filter transactions"),
    start: int = Query(0, description="Pagination start value"),
    limit: int = Query(20, description="Number of results to return"),
    sort: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
    query: str = Query(None, description="Search query for invoices"),
):
    """
    Fetch paginated invoice transactions for a brain.
    """
    url = f"{settings.brain_base_url}/v1/transaction/invoice"
    params = {
        "brainId": brain_id,
        "start": start,
        "limit": limit,
        "sort": sort,
    }

    if query:
        params["query"] = query
    
    try:
        data = await get_json(url, params=params, log_message="fetch invoice transactions")
        return data
    except HttpClientError as e:
        http_exception_handler(e)


@router.get("/statements", description="Get statement transactions")
async def get_statement_transactions(
    brain_id: str = Query(..., description="Brain ID to filter transactions"),
    start: int = Query(0, description="Pagination start value"),
    limit: int = Query(20, description="Number of results to return"),
    sort: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
):
    """
    Fetch paginated statement transactions for a brain.
    """
    url = f"{settings.brain_base_url}/v1/transaction/statement"
    params = {
        "brainId": brain_id,
        "start": start,
        "limit": limit,
        "sort": sort,
    }
    
    try:
        data = await get_json(url, params=params, log_message="fetch statement transactions")
        return data
    except HttpClientError as e:
        http_exception_handler(e)


async def store_reconciliation_data(request: Request,
    db: Session, tenant_id: str, reconciliation_data: List[Dict[str, Any]]
) -> List[DraftReconciliationEntry]:
    """
    Parse and store reconciliation data in the PostgreSQL database.
    """
    logger.info(f"Starting reconciliation data storage for tenant_id: {tenant_id}")
    logger.info(f"Number of reconciliation items to process: {len(reconciliation_data)}")

    entries = []
    user_id = str(request.state.user.id)
    tenant_metadata = await get_tenant_metadata(db, tenant_id, user_id)

    if not tenant_metadata:
        logger.error(f"Tenant metadata not found for tenant_id: {tenant_id}")
        raise HTTPException(status_code=404, detail="Tenant metadata not found")

    logger.info(f"Retrieved tenant metadata for {tenant_metadata.tenant_name}")

    for idx, item in enumerate(reconciliation_data):
        try:
            statement = item.get("statementItem", {})
            invoice = item.get("matchingInvoices", {})
            statement_id = str(statement.get("statementId", ""))
            logger.debug(
                f"Processing item {idx+1}/{len(reconciliation_data)}: "
                f"Statement: {statement.get('description')} "
                f"with {len(invoice)} matching invoices"
            )

            # For each matching invoice, create a draft reconciliation entry
            if invoice:
                try:
                    bank_details = invoice.get("bankDetails", {})
                    account_name = bank_details.get("accountName")
                    if not account_name:
                        account_name = bank_details.get("accountNumber")
                    invoice_id = str(invoice.get("invoiceId", ""))
                    
                    # Check if we already have an entry for this statement-invoice pair
                    existing_entry = db.query(DraftReconciliationEntry).filter(
                        DraftReconciliationEntry.tenant_shortcode == tenant_metadata.tenant_short_code,
                        DraftReconciliationEntry.statement_id == statement_id
                    ).first()
                    if existing_entry:
                        existing_entry.statement_client_name = tenant_metadata.tenant_name
                        existing_entry.account_name = account_name
                        existing_entry.transaction_date = datetime.fromtimestamp(
                            statement.get("statementTimestamp", 0)
                        )
                        existing_entry.payee = statement.get("payee")
                        existing_entry.particulars = statement.get("description")
                        existing_entry.statement_amount = statement.get("totalAmount")
                        existing_entry.file_name = statement.get("fileId")
                        existing_entry.invoice_client_name = invoice.get("sender", {}).get("name")
                        existing_entry.details = invoice.get("invoiceNumber")
                        existing_entry.invoice_date = datetime.fromtimestamp(invoice.get("invoiceTimestamp", 0))
                        existing_entry.invoice_amount = invoice.get("totalAmount")
                        existing_entry.status = "Active"
                        existing_entry.verified = statement.get("verified", False)
                        existing_entry.updated_at = datetime.now(timezone.utc)
                        # Don't update notes here to preserve user-entered notes
                        entries.append(existing_entry)
                    else:
                        entry = DraftReconciliationEntry(
                            tenant_shortcode=tenant_metadata.tenant_short_code,
                            statement_id=statement_id,
                            invoice_id=invoice_id,
                            statement_client_name=tenant_metadata.tenant_name,
                            account_name=account_name,
                            transaction_date=datetime.fromtimestamp(
                                statement.get("statementTimestamp", 0)
                            ),
                            payee=statement.get("payee"),
                            particulars=statement.get("description"),
                            statement_amount=statement.get("totalAmount"),
                            file_name=statement.get("fileId"),
                            invoice_client_name=invoice.get("sender", {}).get("name"),
                            details=invoice.get("invoiceNumber"),
                            invoice_date=datetime.fromtimestamp(invoice.get("invoiceTimestamp", 0)),
                            invoice_amount=invoice.get("totalAmount"),
                            status="Active",
                            verified=statement.get("verified", False),
                            notes=""
                        )
                        db.add(entry)
                        entries.append(entry)
                except Exception as e:
                    print(invoice)
                    logger.error(f"Error processing invoice entry: {str(e)}", exc_info=True)
                    raise HTTPException(status_code=500, detail=f"Error processing invoice: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing reconciliation item {idx+1}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing reconciliation item: {str(e)}")

    try:
        db.commit()
        logger.info(f"Successfully stored {len(entries)} reconciliation entries")
        return entries
    except Exception as e:
        logger.error("Error committing reconciliation entries to database", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/recon", description="Get reconciliation data")
async def get_reconciliation(
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
    brain_id: str = Query(..., description="Brain ID for reconciliation"),
    start_period: int = Query(0, description="Start of the period (Unix timestamp)"),
    end_period: int = Query(
        None, description="End of the period (Unix timestamp, defaults to now)"
    ),
    start: int = Query(0, description="Pagination start value"),
    limit: int = Query(20, description="Number of results to return"),
    filter_by: str = Query(
        "all", description="Filter: 'all' or 'verified' or 'matched' or 'unmatched' (defaults to 'all')"
    ),
):
    """
    Fetch reconciliation data for a brain within a specified date range.
    The API now returns matched invoices directly, so no consolidation is needed.
    """
    logger.info(f"Starting reconciliation request for brain_id: {brain_id}")
    
    # Get tenant ID from the request
    tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
    if not tenant_id:
        logger.error("No tenant ID found in request")
        raise HTTPException(status_code=400, detail="No tenant selected")

    logger.info(f"Retrieved tenant_id: {tenant_id}")

    url = f"{settings.brain_base_url}/v1/transaction/recon"
    params = {
        "brainId": brain_id,
        "start_period": start_period,
        "filter": filter_by,
        "start": start,
        "limit": limit,
    }
    if end_period is not None:
        params["end_period"] = end_period

    logger.info(f"Making request to Brain API: {url}")
    logger.debug(f"Request parameters: {params}")

    try:
        response_data = await get_json(
            url, 
            params=params, 
            log_message="fetch reconciliation data",
        )
        logger.info(f"Successfully retrieved reconciliation items from Brain API")

        logger.debug("Starting storage of reconciliation data")
        entries = await store_reconciliation_data(request, db, tenant_id, reconciliation_data=response_data["data"])
        logger.info(f"Successfully processed and stored {len(entries)} reconciliation entries")
        enhanced_data = []
        for item in response_data["data"]:
            statement_id = str(item.get("statementItem", {}).get("statementId", ""))
            invoice = item.get("matchingInvoices", {})
            
            if invoice:
                invoice_id = str(invoice.get("invoiceId", ""))
                
                # Find notes for this statement-invoice pair
                entry = db.query(DraftReconciliationEntry).filter(
                    # DraftReconciliationEntry.tenant_shortcode == tenant_id,
                    DraftReconciliationEntry.statement_id == statement_id,
                    DraftReconciliationEntry.invoice_id == invoice_id
                ).first()
                
                if entry and entry.notes:
                    # Add notes to the invoice data
                    invoice["notes"] = entry.notes
            
            enhanced_data.append(item)
        
        # Return the enhanced data
        response_data["data"] = enhanced_data
        return response_data

    except HttpClientError as e:
        http_exception_handler(e)
    except Exception as e:
        logger.error(f"Unexpected error in reconciliation process: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/verify", description="Verify reconciliation")
async def verify_reconciliation(mapping: List[ReconciliationVerification]):
    """
    Verify one or more reconciled transactions.
    """
    url = f"{settings.brain_base_url}/v1/transaction/verify"
    payload = {"mapping": [m.model_dump() for m in mapping]}
    
    try:
        data = await post_json(
            url, 
            json=payload, 
            log_message="verify reconciliation"
        )
        return data
    except HttpClientError as e:
        http_exception_handler(e)

@router.post("/invoice/notes", description="Save notes for an invoice")
async def save_invoice_notes(
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
    data: dict = Body(...),
):
    """
    Save notes for a specific invoice in the reconciliation system.
    """
    statement_id = data.get("statement_id")
    invoice_id = data.get("invoice_id")
    notes = data.get("notes")
    
    if not statement_id or not invoice_id:
        raise HTTPException(status_code=400, detail="Statement ID and Invoice ID are required")
    
    logger.info(f"Saving notes for statement ID: {statement_id}, invoice ID: {invoice_id}")
    
    try:
        # Get tenant ID from the request
        # tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
        # if not tenant_id:
        #     logger.error("No tenant ID found in request")
        #     raise HTTPException(status_code=400, detail="No tenant selected")
            
        # Find the reconciliation entry for this statement-invoice pair
        entry = db.query(DraftReconciliationEntry).filter(
            # DraftReconciliationEntry.tenant_shortcode == tenant_id,
            DraftReconciliationEntry.statement_id == statement_id,
            DraftReconciliationEntry.invoice_id == invoice_id
        ).first()
        
        if not entry:
            # If no entry exists, throw an error
            logger.error(f"No reconciliation entry found for statement ID: {statement_id}, invoice ID: {invoice_id}")
            raise HTTPException(status_code=404, detail="Reconciliation entry not found")
        else:
            # Update existing entry
            entry.notes = notes
            entry.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        logger.info(f"Successfully saved notes for statement ID: {statement_id}, invoice ID: {invoice_id}")
        
        return {"status": "success", "message": "Notes saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving notes: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving notes: {str(e)}")