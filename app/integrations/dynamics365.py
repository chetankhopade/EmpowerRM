import json

import requests


class Dynamics365aRestService:
    """
    references:
    https://docs.microsoft.com/en-us/dynamics365/fin-ops-core/dev-itpro/data-entities/services-home-page
    https://docs.microsoft.com/en-us/azure/active-directory/azuread-dev/v1-oauth2-client-creds-grant-flow
    https://blog.magnetismsolutions.com/blog/johntowgood/2018/03/08/dynamics-365-online-authenticate-with-client-credentials

    Notes from meeting with DS365 people
    https://dcsllc-test61ceadc2bbda76b9aos.cloudax.dynamics.com/
    ReleasedProductsV2 - Items
    CustomersV3 - Customers
    SalesOrderHeadersV2 and SalesOrderLines - CBs
    [10:25 AM] Caleb Blanchard (Guest) /data/SalesOrderLines?$filter=dataAreaId%20eq%20'O2CA'&cross-company=true
    """
    def __init__(self, config, access_token=''):
        try:
            # main config
            self.login_url = config['login_url']
            self.resource_url = config['resource_url']
            self.client_id = config['client_id']
            self.client_secret = config['client_secret']

            if access_token:
                self.access_token = access_token
            else:
                self.access_token = ''
                if self.login_url and self.resource_url and self.client_id and self.client_secret:
                    response = requests.post(
                        self.login_url,
                        data=f'client_id={self.client_id}&client_secret={self.client_secret}&resource={self.resource_url}&grant_type=client_credentials'
                    )

                    if response.status_code == 200:
                        self.access_token = response.json()['access_token']

            self.common_headers = {
                'Authorization': f'Bearer {self.access_token}',
                'OData-MaxVersion': '4.0',
                'OData-Version': '4.0',
                'Content-Type': 'application/json; charset=utf-8'
            }

            self.common_params = {
                "?$filter": "dataAreaId eq 'O2CA'",
                "cross-company": True
            }

        except Exception as ex:
            self.access_token = ''
            print(ex.__str__())

    def get_all_entities(self):
        """
        Function to get all the DS365 entities
        :return:
        """
        response = requests.get(
            f"{self.resource_url}/data",
            headers=self.common_headers,
            params=self.common_params
        )

        entities_urls = sorted([x['url'] for x in response.json()['value']])
        for url in entities_urls:
            print(url)

    def get_customers_account_numbers(self):
        """
        Function to get all customers account numbers (DS365 endpoint: CustomersV3, field CustomerAccount)
        :return:
        """
        response = requests.get(
            f"{self.resource_url}/data/CustomersV3",
            headers=self.common_headers,
            params=self.common_params
        )

        if response.status_code == 200:
            # print(json.dumps([x['CustomerAccount'] for x in response.json()['value']], indent=4))
            return [x['CustomerAccount'] for x in response.json()['value']]

        return []

    def get_items_ndcs(self):
        """
        Function to get all items ndcs (DS365 endpoint: ReleasedProductsV2, field ItemNumber)
        :return:
        """
        response = requests.get(
            f"{self.resource_url}/data/ReleasedProductsV2",
            headers=self.common_headers,
            params=self.common_params
        )

        if response.status_code == 200:
            # print(json.dumps([x['ItemNumber'] for x in response.json()['value']], indent=4))
            return [x['ItemNumber'] for x in response.json()['value']]

        return []

    def get_sales_orders_header(self):
        """
        Function to get all SalesOrder headers (DS365 endpoint: SalesOrderHeadersV2)
        :return:
        """
        response = requests.get(
            f"{self.resource_url}/data/SalesOrderHeadersV2",
            headers=self.common_headers,
            params=self.common_params
        )

        if response.status_code == 200:
            items = [x for x in response.json()['value']]
            print(json.dumps(items[:10], indent=4))

    def get_sales_orders_lines(self):
        """
        Function to get all SalesOrder lines (DS365 endpoint: SalesOrderLines)
        :return:
        """
        response = requests.get(
            f"{self.resource_url}/data/SalesOrderLines",
            headers=self.common_headers,
            params=self.common_params
        )

        if response.status_code == 200:
            items = [x for x in response.json()['value']]
            print(json.dumps(items[:10], indent=4))

    def create_sale_order_header(self, sales_order_number, customer_accno, cb_number, is_empower_dictates_numbers_to_d365=False):
        """
        Function to create a SalesOrder header (DS365 endpoint: SalesOrderHeadersV2)
        :return:
        """
        if is_empower_dictates_numbers_to_d365:
            payload = {
                "SalesOrderNumber": sales_order_number,
                "OrderingCustomerAccountNumber": customer_accno,
                "CustomersOrderReference": cb_number,
                "dataAreaId": "O2CA",
                "SalesOrderPoolId": 'CB',
                'SalesOrderOriginCode': 'MDH'
            }
        else:
            payload = {
                "OrderingCustomerAccountNumber": customer_accno,
                "CustomersOrderReference": cb_number,
                "dataAreaId": "O2CA",
                "SalesOrderPoolId": 'CB',
                'SalesOrderOriginCode': 'MDH'
            }

        response = requests.post(
            f"{self.resource_url}/data/SalesOrderHeadersV2",
            headers=self.common_headers,
            json=payload
        )

        if response.status_code == 201:
            print(f'CREATED SalesOrderNumber: {response.json()["SalesOrderNumber"]}')
            # print(json.dumps(response.json(), indent=4))
            return response

        return None

    def create_sale_order_line(self, cb_number, item_ndc, item_qty, line_amount):
        """
        Function to create a SalesOrder lines (DS365 endpoint: SalesOrderLines)
        :return:
        """
        payload = {
            # "SalesOrderNumber": "CBJEREMY2020",   # max_number character: 20
            # "ItemNumber": "29300-0112-01 (CB)",
            # "OrderedSalesQuantity": -1.0,
            # "LineAmount": -100.0,
            "SalesOrderNumber": cb_number,
            "ItemNumber": item_ndc,
            "OrderedSalesQuantity": item_qty,
            "LineAmount": line_amount,
            "dataAreaId": "O2CA"
        }

        response = requests.post(
            f"{self.resource_url}/data/SalesOrderLines",
            headers=self.common_headers,
            json=payload
        )

        if response.status_code == 201:
            print(f'CREATED SaleOrderLine: {response.json()["ItemNumber"]} (SO: {response.json()["SalesOrderNumber"]})')
            # print(json.dumps(response.json(), indent=4))
            return response

        # print(f'ERROR: {json.loads(response.text["error"]["innererror"]["message"])}')
        return None


# Remove after testing frontend-backend post to accounting functionality
# if __name__ == '__main__':
#
#     integration_config = {
#         'login_url': 'https://login.microsoftonline.com/3ca4644c-9c08-417c-93b6-d20b42d4cdcd/oauth2/token',
#         'resource_url': 'https://dcsllc-test61ceadc2bbda76b9aos.cloudax.dynamics.com',
#         'client_id': '48b09d35-1de3-47c7-928d-13ddc2cca80f',
#         'client_secret': 'xMw-.~n3.nxk5ZG_V843KSIKLu04USm9w_'
#     }
#     rs = Dynamics365aRestService(config=integration_config)
#     print(f'Connected: {"YES" if rs.connected else "NO"}')
#     print(f'Access Token: {rs.access_token}')

    # All Entities
    # rs.get_all_entities()

    # # Get Customers
    # rs.get_customers_account_numbers()
    #
    # # Get Items
    # rs.get_items_ndcs()

    # Get SalesOrders Header (CBs)
    # rs.get_sales_orders_header()
    #
    # # Get SalesOrders Lines (CBLines)
    # rs.get_sales_orders_lines()

    # Create SalesOrder Header (CBs)
    # rs.create_sale_order_header()

    # Get SalesOrders Lines (CBLine)
    # rs.create_sale_order_line()
