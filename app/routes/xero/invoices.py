import logging
from typing import Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Path,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError
from xero_python.accounting import AccountingApi, CurrencyCode
from xero_python.accounting import Contact as XeroContact
from xero_python.accounting import Invoice as XeroInvoice
from xero_python.accounting import LineItem as XeroLineItem
from xero_python.api_client import serialize

from app.core.oauth import api_client, require_valid_token
from app.models.xero.invoice_models import InvoiceRequest
from app.utils.xero.tenant_utils import get_stored_tenant_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/invoices",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=JSONResponse,
    description="Returns a list of invoices for the current tenant.",
)
async def get_tenant_invoices(
    request: Request, token: dict = Depends(require_valid_token)
):
    try:
        xero_tenant_id = get_stored_tenant_id(request)
        if not xero_tenant_id:
            raise HTTPException(status_code=404, detail="No organisation tenant found")

        accounting_api = AccountingApi(api_client)
        invoices = accounting_api.get_invoices(xero_tenant_id)
        serialize_invoices = serialize(invoices)

        return JSONResponse(content=serialize_invoices)

    except Exception as e:
        logger.error(f"Failed to fetch invoices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/invoices/{invoice_id}",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=HTMLResponse,
    description="Returns a specific invoice for the current tenant.",
)
async def get_invoice_by_id(
    request: Request,
    invoice_id: str = Path(..., description="The ID of the invoice"),
    token: dict = Depends(require_valid_token),
) -> JSONResponse:
    try:
        # Get the stored tenant ID
        tenant_id = get_stored_tenant_id(request)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="No tenant selected. Please select a tenant first.",
            )
        accounting_api = AccountingApi(api_client)
        invoice = accounting_api.get_invoice(tenant_id, invoice_id=invoice_id)

        return JSONResponse(
            status_code=200,
            content={"status": "success", "invoice": serialize(invoice)},
        )
    except Exception as e:
        logger.error(f"Error selecting invoice: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/create-invoices")
async def create_invoice(
    request: Request,
    invoice_data: InvoiceRequest = Body(...),
    token: dict = Depends(require_valid_token),
    description="Creates a new invoice for the current tenant.",
) -> JSONResponse:
    try:
        tenant_id = get_stored_tenant_id(request)
        if not tenant_id:
            raise HTTPException(status_code=400, detail="No tenant selected")

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
            f"Processing {len(invoice_data.invoices)} invoices for tenant {tenant_id}"
        )
        request_body = {"Invoices": xero_invoices}

        created_invoices = accounting_api.create_invoices(
            tenant_id, invoices=request_body
        )
        logger.info(f"Successfully created {len(created_invoices.invoices)} invoices")
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "Invoices created successfully",
                "data": serialize(created_invoices),
            },
        )

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create invoice: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/invoice-attachment/{invoice_id}")
async def create_invoice_attachment(
    request: Request,
    invoice_id: str,
    file: Optional[UploadFile] = File(None, description="File to upload"),
    token: dict = Depends(require_valid_token),
    description="Creates a new invoice attachment for the current tenant.",
) -> JSONResponse:
    try:
        logger.info(f"Starting attachment upload process for invoice ID: {invoice_id}")

        tenant_id = get_stored_tenant_id(request)
        if not tenant_id:
            logger.error(f"No tenant ID found for invoice {invoice_id}")
            raise HTTPException(status_code=400, detail="No tenant selected")

        accounting_api = AccountingApi(api_client)

        # Handle file upload
        if file:
            logger.info(
                f"Processing file upload - Filename: {file.filename}, Content-Type: {file.content_type}"
            )
            file_content = await file.read()
            filename = file.filename
            body = file_content
            mime_type = file.content_type
        else:
            raise HTTPException(status_code=400, detail="Please provide a file.")

        # Include online parameter and generate an idempotency key
        include_online = True
        idempotency_key = f"attachment_{invoice_id}_{filename}"

        logger.info(
            f"Sending attachment to Xero API - Filename: {filename}, MIME type: {mime_type}"
        )
        try:
            attachment = accounting_api.create_invoice_attachment_by_file_name(
                xero_tenant_id=tenant_id,
                invoice_id=invoice_id,
                file_name=filename,
                body=body,
                include_online=include_online,
                idempotency_key=idempotency_key,
            )
            logger.info(f"Successfully created attachment for invoice {invoice_id}")
        except Exception as e:
            logger.error(
                f"Error uploading attachment to Xero API: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading to Xero API: {str(e)}",
            )

        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "Attachment uploaded successfully",
                "data": serialize(attachment),
            },
        )
    except Exception as e:
        logger.error(
            f"Error processing attachment for invoice {invoice_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
