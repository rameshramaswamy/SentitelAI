# sentinel_integrations/src/crm/__init__.py
from src.config import settings
from src.crm.salesforce import SalesforceAdapter
# from src.crm.hubspot import HubspotAdapter

def get_crm_adapter():
    if settings.CRM_PROVIDER == "hubspot":
        # return HubspotAdapter()
        raise NotImplementedError("HubSpot not yet implemented")
    else:
        # Default to Salesforce (handles "mock" mode internally)
        return SalesforceAdapter()