import logging
import time

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Path,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from xero_python.accounting import AccountingApi, CurrencyCode
from xero_python.accounting import Contact as XeroContact
from xero_python.accounting import Invoice as XeroInvoice
from xero_python.accounting import LineItem as XeroLineItem
from xero_python.api_client import serialize

from app.core.deps import get_db
from app.core.oauth import api_client, require_valid_token
from app.models.xero.invoice_models import InvoiceRequest
from app.utils.xero.tenant_utils import get_active_tenant_id

router = APIRouter(prefix="/xero/invoices")
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_class=JSONResponse,
    description="Returns a list of invoices for the current tenant.",
)
async def get_tenant_invoices(
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
):
    """
    Get invoices for the current active tenant.
    Requires an active tenant to be selected.
    """
    try:
        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        # Get active tenant ID from token
        xero_tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
        if not xero_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active tenant found. Please select a tenant first.",
            )

        # Get invoices from Xero
        accounting_api = AccountingApi(api_client)
        invoices = accounting_api.get_invoices(xero_tenant_id)
        serialize_invoices = serialize(invoices)

        return JSONResponse(
            content=serialize_invoices,
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting invoices: {str(e)}",
        )


@router.get(
    "/{invoice_id}",
    response_class=JSONResponse,
    description="Returns an invoice by ID for the current tenant",
)
async def get_invoice_by_id(
    request: Request,
    invoice_id: str = Path(..., description="The ID of the invoice"),
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
):
    """
    Get a specific invoice by ID for the current active tenant.
    Requires an active tenant to be selected.
    """
    try:
        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        # Get active tenant ID from token
        xero_tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
        if not xero_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active tenant found. Please select a tenant first.",
            )

        # Get invoice from Xero
        accounting_api = AccountingApi(api_client)
        invoice = accounting_api.get_invoice(xero_tenant_id, invoice_id)
        serialized_invoice = serialize(invoice)

        return JSONResponse(
            content=serialized_invoice,
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice {invoice_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting invoice: {str(e)}",
        )


@router.put("/create")
async def create_invoice(
    request: Request,
    invoice_data: InvoiceRequest = Body(...),
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
    description="Creates a new invoice for the current tenant.",
) -> JSONResponse:
    try:
        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        # Get active tenant ID from token
        xero_tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
        if not xero_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active tenant found. Please select a tenant first.",
            )

        # Create invoice in Xero
        accounting_api = AccountingApi(api_client)

        xero_invoices = []
        for invoice in invoice_data.invoices:
            xero_contact = XeroContact(contact_id=invoice.contact.contact_id)

            xero_line_items = [
                XeroLineItem(
                    description=item.description,
                    quantity=item.quantity,
                    unit_amount=item.unit_amount,
                    account_code=item.account_code,
                    tax_type=item.tax_type,
                )
                for item in invoice.line_items
            ]

            xero_invoice = XeroInvoice(
                type=invoice.type,
                contact=xero_contact,
                line_items=xero_line_items,
                date=invoice.date,
                due_date=invoice.due_date,
                invoice_number=invoice.invoice_number,
                status=invoice.status,
                currency_code=CurrencyCode(invoice.currency_code),
                reference=invoice.reference,
            )
            xero_invoices.append(xero_invoice)

        # Create the request body in the format Xero expects
        logger.info(
            f"Processing {len(invoice_data.invoices)} invoices for tenant {xero_tenant_id}"
        )
        request_body = {"Invoices": xero_invoices}

        created_invoices = accounting_api.create_invoices(
            xero_tenant_id, invoices=request_body
        )
        logger.info(f"Successfully created {len(created_invoices.invoices)} invoices")
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "Invoices created successfully",
                "data": serialize(created_invoices),
            },
        )

    except ValidationError as e:
        logger.error(f"Validation error creating invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid invoice data: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating invoice: {str(e)}",
        )


@router.put(
    "/attachment/{invoice_id}",
    description="Creates a new invoice attachment for the current tenant.",
)
async def create_invoice_attachment(
    request: Request,
    invoice_id: str = Path(..., description="The ID of the invoice"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
) -> JSONResponse:
    try:
        logger.info(f"Starting attachment upload process for invoice ID: {invoice_id}")

        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        # Get active tenant ID from token
        xero_tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
        if not xero_tenant_id:
            logger.error(f"No tenant ID found for invoice {invoice_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active tenant found. Please select a tenant first.",
            )

        if not file or not file.filename:
            logger.error("No file provided or empty filename")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a file",
            )

        accounting_api = AccountingApi(api_client)

        try:
            # Handle file upload
            logger.info(
                f"Processing file upload - Filename: {file.filename}, Content-Type: {file.content_type}"
            )
            file_content = await file.read()
            if not file_content:
                logger.error("File content is empty")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File content is empty",
                )

            filename = file.filename
            # Use timestamp in idempotency key to avoid conflicts
            timestamp = int(time.time())
            idempotency_key = f"attachment_{invoice_id}_{timestamp}"

            logger.info(
                f"Sending attachment to Xero API - Filename: {filename}, MIME type: {file.content_type}"
            )

            attachment = accounting_api.create_invoice_attachment_by_file_name(
                xero_tenant_id=xero_tenant_id,
                invoice_id=invoice_id,
                file_name=filename,
                body=file_content,
                idempotency_key=idempotency_key,
            )
            logger.info(f"Successfully created attachment for invoice {invoice_id}")

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "status": "success",
                    "message": "Attachment uploaded successfully",
                    "data": serialize(attachment),
                },
            )
        except Exception as e:
            logger.error(
                f"Error uploading attachment to Xero API: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading to Xero API: {str(e)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing attachment for invoice {invoice_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
