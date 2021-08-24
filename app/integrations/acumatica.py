import requests

from empowerb.settings import (ACCUMATICA_API_LOGOUT, ACCUMATICA_API_CUSTOMERS, ACCUMATICA_API_ITEMS,
                               ACCUMATICA_API_INVOICES, ACCUMATICA_API_LOGIN)


class AcumaticaRestService:

    def __init__(self, config):
        self.base_url = config['base_url']
        self.username = config['auth']['username']
        self.password = config['auth']['password']
        self.company_name = config['auth']['company']
        self.branch = config['auth']['branch']

        self.logout_url = f"{self.base_url}{ACCUMATICA_API_LOGOUT}"
        self.customers_url = f"{self.base_url}{ACCUMATICA_API_CUSTOMERS}"
        self.items_url = f"{self.base_url}{ACCUMATICA_API_ITEMS}"
        self.invoice_url = f"{self.base_url}{ACCUMATICA_API_INVOICES}"

        self.login_url = f"{self.base_url}{ACCUMATICA_API_LOGIN}"

        self.connected = False
        if self.username and self.password and self.company_name and self.branch:
            payload = {
                "name": self.username,
                "password": self.password,
                "company": self.company_name,
                "branch": self.branch
            }
            self.session = requests.Session()
            response = self.session.post(self.login_url, json=payload)
            if response.status_code == 204:
                self.connected = True

    def dispose(self):
        try:
            response = self.session.post(self.logout_url, data={})
            if response.status_code == 204:
                return response
            return None
        except Exception as ex:
            print(ex.__str__())
            return None

    def get_active_customers(self):
        try:
            payload = {
                "?$filter": "Status eq 'Active'"
            }
            response = self.session.get(self.customers_url, params=payload)
            if response.status_code == 200:
                return response
            return []
        except Exception as ex:
            print(ex.__str__())
            return []

    def get_active_customers_ids(self):
        try:
            payload = {
                "?$filter": "Status eq 'Active'",
                "$select": "CustomerID"
            }
            response = self.session.get(self.customers_url, params=payload)
            if response.status_code == 200:
                return response
            return []
        except Exception as ex:
            print(ex.__str__())
            return []

    def get_active_items(self):
        try:
            payload = {
                "$filter": "ItemStatus eq 'Active'"
            }
            response = self.session.get(self.items_url, params=payload)
            if response.status_code == 200:
                return response
            return []
        except Exception as ex:
            print(ex.__str__())
            return []

    def get_active_items_ids(self):
        try:
            payload = {
                "$filter": "ItemStatus eq 'Active'",
                "$select": "InventoryID"
            }
            response = self.session.get(self.items_url, params=payload)
            if response.status_code == 200:
                return response
            return []
        except Exception as ex:
            print(ex.__str__())
            return []

    def check_transaction(self, transaction_type, transaction_number):
        """
        Jeremy's ref:
        https://acsbapi.rssolutions.com/entity/Default/17.200.001/Invoice?$filter=Type eq ' Credit Memo' and ReferenceNbr eq '000022'&$top=1&$select=ReferenceNbr
        :return:
        """
        try:
            payload = {
                "$filter": f"Type eq '{transaction_type}' and ReferenceNbr eq '{transaction_number}'",
                "$top": "1",
                "$select": "ReferenceNbr"
            }
            response = self.session.get(self.invoice_url, params=payload)
            if response.status_code == 200:
                return response
            return []
        except Exception as ex:
            print(ex.__str__())
            return None

    def create_transaction(self, **kwargs):
        """
        Jeremy's ref: https://acsbapi.rssolutions.com/entity/Default/17.200.001/Invoice
        :param kwargs:
            customer_accno,
            transaction_type,
            description (cb number),
            post_date,
            transaction_number,
            terms,
            transaction_lines: obj [
                {
                    InventoryID,
                    UnitPrice,
                    Qty
                },
            ]
        :return:
        """
        try:
            customer_accno = kwargs['customer_accno']
            transaction_type = kwargs['transaction_type']
            description = kwargs['description']
            post_date = kwargs['post_date']
            transaction_number = kwargs['transaction_number']
            terms = kwargs['terms']
            transaction_lines = kwargs['transaction_lines']

            payload = {
                "Customer": {
                    "value": customer_accno
                },
                "Type": {
                    "value": transaction_type
                },
                "Description": {
                    "value": description
                },
                "Date": {
                    "value": post_date
                },
                "Terms": {
                    "value": terms
                },
                "Details": transaction_lines
            }

            if transaction_number:
                payload.update({
                    "ReferenceNbr": {
                        "value": transaction_number
                    }
                })
            # API
            response = self.session.put(self.invoice_url, json=payload)
            if response.status_code == 200:
                return response
            return []

        except Exception as ex:
            print(ex.__str__())
            return []
