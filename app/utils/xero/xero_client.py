from xero_python.accounting import AccountingApi
from xero_python.identity import IdentityApi

from app.core.oauth import api_client


class XeroClient:
    def __init__(self):
        self.accounting_api = AccountingApi(api_client)
        self.identity_api = IdentityApi(api_client)

    async def get_connections(self):
        return self.identity_api.get_connections()

    def get_organisations(self, tenant_id: str):
        return self.accounting_api.get_organisations(xero_tenant_id=tenant_id)

    def get_invoices(self, tenant_id: str, statuses=None):
        return self.accounting_api.get_invoices(
            xero_tenant_id=tenant_id, statuses=statuses
        )

    def get_accounts(self, tenant_id: str, where_clause: str = None):
        return self.accounting_api.get_accounts(
            xero_tenant_id=tenant_id, where=where_clause
        )
