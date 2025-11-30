# sentinel_integrations/tests/test_crm.py
import pytest
from unittest.mock import MagicMock, patch
from src.crm.salesforce import SalesforceAdapter

@pytest.mark.asyncio
async def test_salesforce_log_activity():
    # Mock the Salesforce client library
    with patch("src.crm.salesforce.Salesforce") as MockSF:
        # Setup Mock
        mock_instance = MockSF.return_value
        
        # Mock Query Response (Found 1 Contact)
        mock_instance.query.return_value = {
            "totalSize": 1,
            "records": [{"Id": "003xxxxxxxxxxxx", "Name": "John Doe"}]
        }
        
        adapter = SalesforceAdapter()
        # Mock config to force real connection attempt (but intercepted by patch)
        with patch("src.config.settings.CRM_PROVIDER", "salesforce"):
            await adapter.connect()
            
            summary = {
                "summary": "Good call.",
                "action_items": ["Email pricing"],
                "sentiment": "Positive",
                "deal_risk_score": 2
            }
            
            success = await adapter.log_call_activity(
                "agent@company.com", 
                "customer@client.com", 
                summary
            )
            
            assert success is True
            # Verify Task creation was called
            mock_instance.Task.create.assert_called_once()
            
            # Check payload
            call_args = mock_instance.Task.create.call_args[0][0]
            assert call_args["WhoId"] == "003xxxxxxxxxxxx"
            assert "Good call" in call_args["Description"]