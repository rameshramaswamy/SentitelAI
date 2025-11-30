# sentinel_integrations/src/crm/salesforce.py
import logging
import asyncio
from simple_salesforce import Salesforce
from src.config import settings
from src.crm.base import BaseCRM

logger = logging.getLogger("crm.salesforce")

class SalesforceAdapter(BaseCRM):
    def __init__(self):
        self.sf = None

    async def connect(self):
        if settings.CRM_PROVIDER == "mock":
            logger.info("CRM: Mock Mode enabled.")
            return

        # Connect synchronously (simple_salesforce is sync, usually fast enough)
        # In high-scale, wrap this in run_in_executor
        try:
            self.sf = Salesforce(
                username=settings.SF_USERNAME,
                password=settings.SF_PASSWORD,
                security_token=settings.SF_TOKEN,
                domain=settings.SF_DOMAIN
            )
            logger.info("Connected to Salesforce.")
        except Exception as e:
            logger.error(f"Salesforce Connection Failed: {e}")
            self.sf = None

    async def log_call_activity(self, user_email: str, customer_email: str, summary_data: Dict) -> bool:
        """
        1. Find Contact by Email.
        2. Create a 'Task' object linked to that Contact.
        """
        if settings.CRM_PROVIDER == "mock" or not self.sf:
            logger.info(f"[Mock CRM] Logged call for {customer_email}: {summary_data['summary'][:50]}...")
            return True

        loop = asyncio.get_running_loop()
        
        # Offload sync calls to thread
        return await loop.run_in_executor(
            None, 
            self._sync_log_activity, 
            user_email, 
            customer_email, 
            summary_data
        )

    def _sync_log_activity(self, user_email: str, customer_email: str, summary_data: dict):
        try:
            # 1. Find the Customer (Contact/Lead)
            # SOQL Query
            query = f"SELECT Id, Name FROM Contact WHERE Email = '{customer_email}' LIMIT 1"
            results = self.sf.query(query)
            
            contact_id = None
            if results['totalSize'] > 0:
                contact_id = results['records'][0]['Id']
            else:
                # Try finding a Lead if Contact not found
                query_lead = f"SELECT Id FROM Lead WHERE Email = '{customer_email}' LIMIT 1"
                lead_results = self.sf.query(query_lead)
                if lead_results['totalSize'] > 0:
                    contact_id = lead_results['records'][0]['Id'] # Maps to WhoId

            if not contact_id:
                logger.warning(f"CRM: Customer email {customer_email} not found in Salesforce.")
                # We could create a Lead here, but for now just skip linking
                return False

            # 2. Format the Description
            description = (
                f"SUMMARY:\n{summary_data.get('summary')}\n\n"
                f"ACTION ITEMS:\n- " + "\n- ".join(summary_data.get('action_items', [])) + "\n\n"
                f"SENTIMENT: {summary_data.get('sentiment')}\n"
                f"RISK SCORE: {summary_data.get('deal_risk_score')}/10"
            )

            # 3. Create Task Object
            task_payload = {
                "Subject": "Sentinel AI: Call Summary",
                "Status": "Completed",
                "Priority": "Normal",
                "Description": description,
                "WhoId": contact_id, # Links to Contact/Lead
                "ActivityDate": "2023-10-27" # In prod, use today's date
            }

            self.sf.Task.create(task_payload)
            logger.info(f"Salesforce Task created for {customer_email}")
            return True

        except Exception as e:
            logger.error(f"Salesforce Write Failed: {e}")
            return False