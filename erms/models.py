import datetime
import random
from abc import abstractmethod
from decimal import Decimal

import dateutil
from django.apps import apps
from django.core.exceptions import MultipleObjectsReturned
from django.core.mail import EmailMessage
from django.db import models, connections
from django.db.models import Sum, Count, F, DecimalField, CharField, When, Value, Case
from django.template.loader import render_to_string
from django_mysql.models import Model, JSONField

from app.management.utilities.basemodel import BaseModel
from app.management.utilities.constants import (CONTRACT_TYPES, STATUSES, STAGES_TYPES, SUBSTAGES_TYPES,
                                                STATUS_ACTIVE, STATUS_INACTIVE, COLORS_LIST, CB_ACTION_LOGS,
                                                CB_ACTION_LOG_COMPLETED, ELIGIBILITIES, LINE_STATUSES, CUSTOMER_TYPES,
                                                LINE_STATUS_PENDING, STATUS_PENDING, CONTRACT_TYPE_INDIRECT,
                                                SUBSTAGE_TYPE_NO_ERRORS, SUBSTAGE_TYPE_ERRORS, SUBSTAGE_TYPE_DUPLICATES,
                                                SUBSTAGE_TYPE_RESUBMISSIONS, SUBSTAGE_TYPE_INVALID, STAGE_TYPE_IMPORTED,
                                                CONTRACT_TYPE_DIRECT, LINE_STATUS_APPROVED,
                                                LINE_STATUS_DISPUTED, EXCEPTIONS_ACTIONS_TAKEN,
                                                ACCOUNTING_TRANSACTION_STATUSES, ACCOUNTING_TRANSACTION_STATUS_PENDING,
                                                REPORT_TYPES, DATA_RANGES, MONTHS, WEEKDAYS, COT_GROUPS,
                                                REPORT_FIELD_TYPES, REPORT_FIELD_SYSTEM, REPORT_SCHEDULE_FREQUENCIES,
                                                REPORT_SCHEDULE_FREQUENCY_DAILY, MONTHDAYS,
                                                REPORT_SCHEDULE_FREQUENCY_WEEKLY, REPORT_SCHEDULE_FREQUENCY_MONTHLY,REPORT_SCHEDULE_FREQUENCY_QUARTARLY,
                                                REPORT_FIELD_PERCENT, REPORT_FIELD_CALCULATED, REPORT_FIELD_STATIC,
                                                REPORT_FIELD_CASE_STATEMENT, EXCEPTION_ACTION_TAKEN_NONE)
from app.management.utilities.exports import export_report
from app.management.utilities.functions import (is_valid_date, get_next_cbid, is_float, get_next_cblnid,
                                                generate_chargeback_id, generate_chargebackline_id, query_range,
                                                get_dates_for_report_filter,is_valid_location_number)
from empowerb.middleware import db_ctx
from empowerb.settings import EMAIL_HOST_USER
from ermm.models import Company


class DirectCustomer(BaseModel):
    """
        Direct Customers
    """
    customer_id = models.CharField(max_length=50, blank=True, null=True)  # DirectCustomer ID (model in master db)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.SmallIntegerField(choices=CUSTOMER_TYPES, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)
    metadata = JSONField(blank=True, null=True)  # add more data for this specific customer and company
    # ticket 730
    enabled_844 = models.BooleanField(default=False)
    enabled_849 = models.BooleanField(default=False)
    # ticket 977
    enabled_852 = models.BooleanField(default=False)
    enabled_867 = models.BooleanField(default=False)
    # ticket 735
    nocredit = models.BooleanField(default=False)
    # ticket 1382
    all_outbound_folder = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Direct Customer'
        verbose_name_plural = 'Direct Customers'
        db_table = "direct_customers"
        ordering = ('name',)

    def my_global_customer(self):
        from ermm.models import DirectCustomer as GlobalCustomer
        if self.customer_id:
            return GlobalCustomer.objects.get(id=self.customer_id)
        return None

    def get_short_name(self):
        if self.account_number:
            return f"{self.get_name()} ({self.account_number})"
        return f"{self.get_name()}"

    def get_account_number(self):
        return self.account_number

    def get_name(self):
        if not self.name:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.name = my_global_customer.name
                self.save()
        return self.name

    def get_email(self):
        if not self.email:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.email = my_global_customer.email
                self.save()
        return self.email

    def get_phone(self):
        if not self.phone:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.phone = my_global_customer.phone
                self.save()
        return self.phone

    def get_address1(self):
        if not self.address1:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.address1 = my_global_customer.address1
                self.save()
        return self.address1

    def get_address2(self):
        if not self.address2:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.address2 = my_global_customer.address2
                self.save()
        return self.address2

    def get_city(self):
        if not self.city:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.city = my_global_customer.city
                self.save()
        return self.city

    def get_state(self):
        if not self.state:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.state = my_global_customer.state
                self.save()
        return self.state

    def get_zip_code(self):
        if not self.zip_code:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.zip_code = my_global_customer.zip_code
                self.save()
        return self.zip_code

    def get_type(self):
        if not self.type:
            my_global_customer = self.my_global_customer()
            if my_global_customer:
                self.type = my_global_customer.type
                self.save()
        return self.type

    def get_metadata(self):
        return self.metadata

    def get_my_chargebacks(self):
        return ChargeBack.objects.filter(customer_id=self.id)

    def get_my_chargebacks_count(self):
        return self.get_my_chargebacks().count()

    def get_chargebacks_history(self):
        return ChargeBackHistory.objects.filter(customer_id=self.id)

    def get_my_chargeback_history(self):
        return ChargeBackHistory.objects.filter(customer_id=self.id)

    def get_chargebacks_history_count(self):
        return self.get_chargebacks_history().count()

    def get_active_contracts(self):
        return self.contract_set.filter(status=STATUS_ACTIVE)

    def get_active_contracts_by_range(self, range):
        return self.get_active_contracts().filter(updated_at__date__range=range)

    def get_active_contracts_count(self):
        return self.get_active_contracts().count()

    def get_ndc_sold_count(self):
        my_active_contracts = self.get_active_contracts()
        if my_active_contracts:
            return Item.objects.filter(contractline__contract__in=my_active_contracts).distinct().count()
        return 0

    def get_ndc_sold_count_by_active_contracts(self, active_contracts):
        if active_contracts:
            return Item.objects.filter(contractline__contract__in=active_contracts).distinct().count()
        return 0

    def get_distribution_centers(self):
        from ermm.models import DistributionCenter as GlobalDistributionCenter
        if not self.distributioncenter_set.exists() and self.customer_id:
            for gdc in GlobalDistributionCenter.objects.filter(customer_id=self.customer_id):
                # dea_number must be unique so add distribution center only if that dea_number is not present
                try:
                    dcs = DistributionCenter.objects.get(dea_number=gdc.dea_number)
                except:
                    dc = DistributionCenter(distribution_center_id=gdc.id,
                                            customer=self,
                                            name=gdc.name,
                                            dea_number=gdc.dea_number,
                                            hin_number=gdc.hin_number,
                                            address1=gdc.address1,
                                            address2=gdc.address2,
                                            city=gdc.city,
                                            state=gdc.state,
                                            zip_code=gdc.zip_code)
                    dc.save()

        return self.distributioncenter_set.order_by('name')

    def has_distribution_centers(self):
        return self.distributioncenter_set.exists()

    def get_my_distribution_centers_by_range(self, range):
        return self.get_distribution_centers().filter(updated_at__date__range=range)

    def get_distribution_centers_count(self):
        return self.get_distribution_centers().count()

    def get_complete_address(self):
        address1 = self.get_address1()
        address2 = self.get_address2()
        complete_address = f'{address1}'
        if address2:
            complete_address += f' | {address2}'
        return complete_address

    def is_a_server_of_contract(self, contract):
        return ContractCustomer.objects.filter(contract=contract, customer=self).exists()

    def get_item_sold(self):
        my_chargebacks = self.get_chargebacks_history().filter(customer_id=self.id)
        value = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in my_chargebacks]).aggregate(sum=Sum('item_qty'))['sum']
        return value if value else 0

    def get_my_items_from_history(self):
        cbh = self.get_chargebacks_history().filter(customer_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh])
        return Item.objects.filter(id__in=[x.item_id for x in cblines_history])

    def get_my_items_by_range(self, range):
        cbh = self.get_chargebacks_history().filter(customer_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh],
                                                               updated_at__date__range=range)
        return Item.objects.filter(id__in=[x.item_id for x in cblines_history])

    def get_my_revenue(self):
        cbh = self.get_chargebacks_history().filter(customer_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh])
        revenue = 0
        for cblh in cblines_history:
            qty = cblh.item_qty if cblh.item_qty else 0
            contract_price_system = cblh.contract_price_system if cblh.contract_price_system else 0
            revenue += qty * contract_price_system
        return revenue if revenue else 0

    def get_my_revenue_by_range(self, range):
        cbh = self.get_chargebacks_history().filter(customer_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh],
                                                               updated_at__date__range=range)
        revenue = 0
        for cblh in cblines_history:
            qty = cblh.item_qty if cblh.item_qty else 0
            contract_price_system = cblh.contract_price_system if cblh.contract_price_system else 0
            revenue += qty * contract_price_system
        return revenue if revenue else 0

    def get_my_revenue_by_cblines_history(self, range):
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=self.id,
                                                               updated_at__date__range=range)
        revenue = cblines_history.annotate(revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(sum=Sum('revenue'))['sum']
        return Decimal(revenue).quantize(Decimal(10) ** -2) if revenue else 0

    def get_my_item_quantities(self, range):
        cbh = self.get_chargebacks_history().filter(customer_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh],
                                                               updated_at__date__range=range)
        units = 0
        for cblh in cblines_history:
            qty = cblh.item_qty if cblh.item_qty else 0
            units += qty
        return units if units else 0

    def get_my_item_quantities_by_cblines_history(self, range):
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_ref__customer_ref=self.id,
                                                               updated_at__date__range=range)
        units_sold = cblines_history.aggregate(sum=Sum('item_qty'))['sum']
        return units_sold if units_sold else 0

    def get_close_sales(self):
        cbh = self.get_my_chargeback_history()
        items_sold = []
        for cb in cbh:
            cb_lines = cb.get_my_chargeback_lines()
            for cb_line in cb_lines:
                item = cb_line.get_my_item()
                if item not in items_sold:
                    items_sold.append(item)
        return items_sold

    @staticmethod
    def get_random_color_for_charts():
        return random.choice(COLORS_LIST)

    @staticmethod
    def get_random_hex_colour():
        random_number = random.randint(0, 16777215)
        hex_number = format(random_number, 'x')
        hex_number = '#' + hex_number
        return hex_number

    def get_current_info_for_audit(self):
        return {
            'customer_id': self.customer_id,
            'account_number': self.account_number,
            'name': self.name,
            'type': self.type,
            'email': self.email,
            'phone': self.phone,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'enabled_844': self.enabled_844,
            'enabled_849': self.enabled_849,
            'enabled_852': self.enabled_852,
            'enabled_867': self.enabled_867,
        }

    def dict_for_datatable(self, is_summary=True):
        active_contracts_count = ''
        ndc_sold_count = ''
        distribution_centers_count = ''
        if not is_summary:
            active_contracts = self.get_active_contracts()
            active_contracts_count = active_contracts.count()
            ndc_sold_count = self.get_ndc_sold_count_by_active_contracts(active_contracts)
            # EA - 1590 - HOTFIX: When assigning a New Direct Customer, the count of Distribution centers stays at zero unless you click into the Direct customer detail and then the DC tab
            # distribution_centers_count = self.distributioncenter_set.count()
            distribution_centers_count = self.get_distribution_centers_count()

        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'account_number': self.account_number,
            'name': self.name,
            'address': self.get_complete_address(),
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'active_contracts_count': active_contracts_count,
            'ndc_sold_count': ndc_sold_count,
            'distribution_centers_count': distribution_centers_count,
            'enabled_844': self.enabled_844,
            'enabled_849': self.enabled_849,
            'enabled_852': self.enabled_852,
            'enabled_867': self.enabled_867,
            'nocredit': self.nocredit,
            'all_outbound_folder': self.all_outbound_folder if self.all_outbound_folder else '',
        }


class ClassOfTrade(BaseModel):
    trade_class = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    group = models.SmallIntegerField(choices=COT_GROUPS, blank=True, null=True)

    def __str__(self):
        return self.trade_class

    class Meta:
        verbose_name = 'Class of Trade'
        verbose_name_plural = 'Classes of Trades'
        db_table = "class_of_trade"
        ordering = ('group', 'trade_class')

    def dict_for_datatable_in_contracts(self, contract_id):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'name': self.trade_class if self.trade_class else '',
            'description': self.description if self.description else '',
            'is_active': 'true' if self.is_active else 'false',
            'is_assigned_to_contract': 'true' if ContractCoT.objects.filter(contract_id=contract_id,
                                                                            cot_id=self.id).exists() else 'false'
        }

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'name': self.trade_class if self.trade_class else '',
            'description': self.description if self.description else '',
            'is_active': 'true' if self.is_active else 'false',
        }


class IndirectCustomer(BaseModel):
    """
        Indirect Customers
    """
    location_number = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=140, blank=True, null=True)
    parent = models.ForeignKey(DirectCustomer, on_delete=models.CASCADE, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)  # global indirect customer id
    metadata = JSONField(blank=True, null=True)

    # Address
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=300, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)

    # Ticket 904 Change CoT field to dropdown in Indir Customers edit
    cot = models.ForeignKey(ClassOfTrade, models.SET_NULL, blank=True, null=True)

    # new fields Ticket EA-783 (CoT, GLN_No, 340B_ID)
    gln_no = models.CharField(max_length=100, blank=True, null=True)
    bid_340 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.location_number}"

    class Meta:
        verbose_name = 'Indirect Customer'
        verbose_name_plural = 'Indirect Customers'
        db_table = "indirect_customers"
        ordering = ('customer_id',)
        unique_together = ('customer_id',)

    def get_my_chargeback_lines(self):
        """
        Get CBLines here IndirectCustomer is the purchaser
        :return:
        """
        return ChargeBackLine.objects.filter(indirect_customer_id=self.id)

    def get_my_chargeback_lines_history(self):
        """
        Get CBLines History here IndirectCustomer is the purchaser
        :return:
        """
        return ChargeBackLineHistory.objects.filter(indirect_customer_id=self.id)

    def get_active_indirect_contracts_from_history(self):
        """
        Get of all unique contracts found in the CBLH table where Indirect Customer is the Purchaser
        :return:
        """
        return Contract.objects.filter(type=CONTRACT_TYPE_INDIRECT,
                                       id__in=[x.contract_id for x in self.get_my_chargeback_lines_history()])

    def count_active_indirect_contracts_from_history(self):
        """
        Count of all unique contracts found in the CBLH table where Indirect Customer is the Purchaser
        :return:
        """
        return self.get_active_indirect_contracts_from_history().count()

    def get_total_product_revenue_by_range(self, range):
        """
        Sum of all extended contract Price (CP * QTY) for all rows in CBLH
        where updated date is in the current month and Indirect Customer is the purchaser
        :param range:
        :return:
        """
        total = 0
        for cbline in self.get_my_chargeback_lines_history().filter(updated_at__date__range=range):
            total += cbline.get_extended_contract_sales()
        return Decimal(total).quantize(Decimal(10) ** -2)

    def get_total_products_sales(self):
        """
        Sum of all QTY in CBLH where Ind Cust is purchaser
        :return:
        """
        value = self.get_my_chargeback_lines_history().aggregate(sum=Sum('item_qty'))['sum']
        return value if value else 0

    def get_related_contracts_from_history(self):
        """
        Get of related contracts found in the CBLH table where Indirect Customer is the Purchaser
        :return:
        """
        return Contract.objects.filter(id__in=[x.contract_id for x in self.get_my_chargeback_lines_history()])

    def get_related_products_from_history(self):
        """
        Get of all related products found in the CBLH table where Indirect Customer is the Purchaser
        :return:
        """
        return Item.objects.filter(id__in=[x.item_id for x in self.get_my_chargeback_lines_history()])

    def get_top_product(self):
        """
        The NDC with the highest QTY count in CBLH where Ind Cust is the purchaser
        :return:
        """
        try:
            cbline_with_max_qty = self.get_my_chargeback_lines_history().order_by('-item_qty')
            item = Item.objects.get(id=cbline_with_max_qty[0].item_id)
            return item.ndc
        except Exception as ex:
            print(ex.__str__())
            return ''

    def elements_with_highest_sales(self):
        results = []
        for cbline in self.get_my_chargeback_lines_history():
            contract = Contract.objects.get(id=cbline.contract_id)
            extended_sales = cbline.get_extended_contract_sales()
            results.append({
                'contract_number': contract.number,
                'customer_name': contract.customer.name,
                'extended_sales': extended_sales if extended_sales else 0
            })

        if results:
            return max(results, key=lambda x: x['extended_sales'])
        return None

    def get_top_contract(self):
        """
        The Contract with the highest Dollar CP Sales (CP * QTY) where Ind Cust is purchaser
        :return:
        """
        highest_sales_elem = self.elements_with_highest_sales()
        return highest_sales_elem['contract_number'] if highest_sales_elem else ''

    def get_top_distributor(self):
        """
        Direct Customer with the highest CP Sales where Ind Cust is the purchaser
        :return:
        """
        highest_sales_elem = self.elements_with_highest_sales()
        return highest_sales_elem['customer_name'] if highest_sales_elem else ''

    def get_complete_address(self):
        return f'{self.address1}, {self.address2}' if self.address1 and self.address2 else self.address1

    def get_current_info_for_audit(self):
        try:
            cot = self.cot.trade_class
        except:
            cot = ''
        return {
            'location_number': self.location_number,
            'company_name': self.company_name,
            'customer_id': self.customer_id,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'cot': cot,
            'gln_no': self.gln_no,
            'bid_340': self.bid_340,
        }

    def dict_for_datatable(self, is_summary=True):
        try:
            cot = self.cot.trade_class
        except:
            cot = ''
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'company_name': self.company_name,
            'location_number': self.location_number,
            'address1': self.address1,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'cot': cot,
            'gln_no': self.gln_no,
            'bid_340': self.bid_340,
        }


class DistributionCenter(BaseModel):
    distribution_center_id = models.CharField(max_length=50, blank=True, null=True)  # DCenter ID (master db)
    customer = models.ForeignKey(DirectCustomer, blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=300, blank=True, null=True)
    dea_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    hin_number = models.CharField(max_length=20, blank=True, null=True)
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=300, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"DC: {self.name} ({self.dea_number})"

    class Meta:
        verbose_name = 'Distribution Center'
        verbose_name_plural = 'Distribution Centers'
        db_table = "distribution_centers"
        ordering = ('-created_at',)

    def my_global_distribution_center(self):
        from ermm.models import DistributionCenter as GlobalDistributionCenter
        if self.distribution_center_id:
            return GlobalDistributionCenter.objects.get(id=self.distribution_center_id)
        return None

    def get_name(self):
        if not self.name:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.name = my_global_dc.name
                self.save()
        return self.name

    def get_dea_number(self):
        if not self.dea_number:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.dea_number = my_global_dc.dea_number
                self.save()
        return self.dea_number

    def get_hin_number(self):
        if not self.hin_number:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.hin_number = my_global_dc.hin_number
                self.save()
        return self.hin_number

    def get_address1(self):
        if not self.address1:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.address1 = my_global_dc.address1
                self.save()
        return self.address1

    def get_address2(self):
        if not self.address2:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.address2 = my_global_dc.address2
                self.save()
        return self.address2

    def get_complete_address(self):
        return f'{self.address1}, {self.address2}' if self.address1 and self.address2 else self.address1

    def get_city(self):
        if not self.city:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.city = my_global_dc.city
                self.save()
        return self.city

    def get_state(self):
        if not self.state:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.state = my_global_dc.state
                self.save()
        return self.state

    def get_zip_code(self):
        if not self.zip_code:
            my_global_dc = self.my_global_distribution_center()
            if my_global_dc:
                self.zip_code = my_global_dc.zip_code
                self.save()
        return self.zip_code

    def get_my_revenue(self):
        cbh = ChargeBackHistory.objects.filter(distribution_center_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh])
        revenue = 0
        for cblh in cblines_history:
            revenue += cblh.item_qty * cblh.contract_price_system
        return revenue if revenue else 0

    def get_my_revenue_by_range(self, range):
        cbh = ChargeBackHistory.objects.filter(distribution_center_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh],
                                                               updated_at__date__range=range)
        revenue = 0
        for cblh in cblines_history:
            revenue += cblh.item_qty * cblh.contract_price_system
        return revenue if revenue else 0

    def get_sold_items(self):
        """
        :return: Item queryset sold by the distribution center
        """
        cbh = ChargeBackHistory.objects.filter(distribution_center_id=self.id)
        cblines_history = ChargeBackLineHistory.objects.filter(chargeback_id__in=[x.id for x in cbh])
        return [x.get_my_item() for x in cblines_history]

    @staticmethod
    def get_random_color_for_charts():
        return random.choice(COLORS_LIST)

    def get_current_info_for_audit(self):
        return {
            'distribution_center_id': self.distribution_center_id,
            'customer_id': self.customer.get_id_str(),
            'name': self.name if self.name else '',
            'dea_number': self.dea_number if self.dea_number else '',
            'hin_number': self.hin_number if self.hin_number else '',
            'address1': self.address1 if self.address1 else '',
            'address2': self.address2 if self.address2 else '',
            'city': self.city if self.city else '',
            'state': self.state if self.state else '',
            'zip_code': self.zip_code if self.zip_code else '',
        }

    def dict_for_datatable(self, is_summary=True):
        return {
            'id': self.get_id_str(),
            'name': self.name if self.name else '',
            'dea_number': self.dea_number if self.dea_number else '',
            'address1': self.address1,
            'address2': self.address2 if self.address2 else '',
            'city': self.city if self.city else '',
            'state': self.state if self.state else '',
            'zip_code': self.zip_code if self.zip_code else '',
        }


class Contract(BaseModel):
    number = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    type = models.SmallIntegerField(choices=CONTRACT_TYPES, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    customer = models.ForeignKey(DirectCustomer, blank=True, null=True, on_delete=models.CASCADE)

    status = models.SmallIntegerField(choices=STATUSES, blank=True, null=True)
    is_bill_back = models.BooleanField(default=False)

    # new fields Ticket 284
    cots = models.TextField(blank=True, null=True)
    eligibility = models.SmallIntegerField(choices=ELIGIBILITIES, blank=True, null=True)

    # new fields Ticket 880
    member_eval = models.BooleanField(default=False)
    cot_eval = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.number}"

    class Meta:
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'
        db_table = "contracts"
        ordering = ('number',)

    def has_contract_lines(self):
        return self.contractline_set.exists()

    def get_products_count(self):
        return self.contractline_set.count()

    def get_my_contract_lines(self):
        return self.contractline_set.order_by('item__ndc')

    def get_my_contract_membership_lines(self):
        return self.contractmember_set.order_by('indirect_customer__id')

    def get_my_contract_lines_active(self):
        return self.get_my_contract_lines().filter(status=STATUS_ACTIVE)

    def get_my_customers(self):
        return [x.customer for x in self.contractcustomer_set.all()]

    def get_my_servers(self):
        return DirectCustomer.objects.filter(contractcustomer__contract=self).distinct()

    def get_my_servers_active(self):
        return self.get_my_servers().filter(contractcustomer__status=STATUS_ACTIVE).distinct()

    def get_my_membership(self):
        return self.contractmember_set.all()

    def get_my_contractcustomer_relations(self):
        return self.contractcustomer_set.all()

    def get_my_contractcustomer_relations_active(self):
        return self.get_my_contractcustomer_relations().filter(status=STATUS_ACTIVE)

    def get_my_contractcustomer_relations_inactive(self):
        return self.get_my_contractcustomer_relations().filter(status=STATUS_INACTIVE)

    def get_my_contractcustomer_relations_pending(self):
        return self.get_my_contractcustomer_relations().filter(status=STATUS_PENDING)

    def is_already_a_server(self, direct_customer):
        return direct_customer in self.get_my_servers()

    def get_my_chargebackline_history(self):
        return self.chargebacklinehistory_set.all()

    def get_my_chargebackline(self):
        return self.chargebackline_set.all()

    def get_chargebacklines_by_range(self, date_range):
        return self.get_my_chargebackline().filter(updated_at__range=query_range(date_range))

    def sum_of_all_chageback_issued(self, date_range):
        value = self.get_chargebacklines_by_range(date_range).aggregate(sum=Sum('claim_amount_issue'))['sum']
        return Decimal(value).quantize(Decimal(10) ** -2) if value else 0

    def total_wac_revenue(self, date_range):
        cbls = self.get_chargebacklines_by_range(date_range)
        value = Decimal('0.00')
        for cbl in cbls:
            # EA-1075 - Error on Contract
            if not cbl.item_qty:
                cbl.item_qty = 1  # It is getting multiplied with was_submitted
            value += Decimal(cbl.item_qty) * cbl.wac_submitted
        return Decimal(value).quantize(Decimal(10) ** -2) if value else 0

    def total_revenue(self, date_range):
        cbls = self.get_chargebacklines_by_range(date_range)
        total = 0.00
        for cbl in cbls:
            total += (cbl.item_qty * cbl.wac_submitted)
        return total

    def get_mtd_cb_lines_from_chargeback_history(self):
        # count how many lines
        today = datetime.datetime.now().date()
        init_date = datetime.datetime(today.year, 1, 1, 0, 0, 0).date()
        return self.get_my_chargebackline_history().filter(updated_at__date__range=(init_date, today))

    def get_mtd_units_sold_from_chargeback_history(self):
        # sum of all item quantity
        value = self.get_mtd_cb_lines_from_chargeback_history().aggregate(sum=Sum('item_qty'))['sum']
        return value if value else 0

    def get_mtd_total_from_chargeback_history(self):
        # sum of all claim amount sys
        value = self.get_mtd_cb_lines_from_chargeback_history().aggregate(sum=Sum('claim_amount_system'))['sum']
        return Decimal(value).quantize(Decimal(10) ** -2) if value else 0

    def get_contract_eligibility(self):
        try:
            return [el[1] for el in ELIGIBILITIES if el[0] == self.eligibility][0]
        except:
            return ''

    def get_contract_cb_count_by_server(self, direct_customer):
        return self.chargebacklinehistory_set.filter(chargeback_ref__customer_ref=direct_customer).values('chargeback_ref').order_by('chargeback_ref').distinct().count()

    def get_contract_cbline_count_by_server(self, direct_customer):
        # 1394 - Lines, is how many cblines have been processed for the server (MTD).  Add {MTD) after Lines on the header
        return self.chargebacklinehistory_set.filter(chargeback_ref__customer_ref=direct_customer, updated_at__date__range=query_range('MTD')).values('id').order_by('id').distinct().count()

    def get_contract_units_sold_by_server(self, direct_customer):
        # 1394 - Sold is sum of qty of all the lines found in previous bullet point (MTD)
        units_sold = self.chargebacklinehistory_set.filter(chargeback_ref__customer_ref=direct_customer, updated_at__date__range=query_range('MTD')).aggregate(sum=Sum('item_qty'))['sum']
        return units_sold if units_sold else 0

    def get_mtd_chargebacks_received_by_server(self, direct_customer):
        # Chargebacks :  list of CBs using this contract MTD received by that server
        today = datetime.datetime.now().date()
        init_date = datetime.datetime(today.year, today.month, 1, 0, 0, 0).date()
        my_chargebacks_ids = [x.chargeback_id for x in
                              self.get_my_chargebackline().filter(created_at__date__range=(init_date, today))]
        return ChargeBack.objects.filter(customer_id=direct_customer.id).filter(id__in=my_chargebacks_ids)

    def get_mtd_amount_of_chargebacks_received_by_server(self, direct_customer):
        # Chargebacks :  Amount of CBs for this contract MTD received by that server
        return self.get_mtd_chargebacks_received_by_server(direct_customer).count()

    def get_mtd_count_of_disputes_received_by_server(self, direct_customer):
        # Errors:  Count of Disputes from CBs for this contract, MTD from that server
        chargebacks = self.get_mtd_chargebacks_received_by_server(direct_customer)
        return ChargeBackDispute.objects.filter(chargeback_id=[x.id for x in chargebacks]).count()

    def get_mtd_count_of_qty_received_by_server(self, direct_customer):
        # Units Sold: MTD Count of QTY from all CB Lines from all CBs for this contract from that server
        chargebacks = self.get_mtd_chargebacks_received_by_server(direct_customer)
        value = 0
        for cb in chargebacks:
            value += cb.calculate_total_item_quantity()
        return value

    def get_my_revenue(self):
        revenue = ChargeBackLineHistory.objects.filter(contract_ref=self).annotate(
            revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('revenue'))['sum']
        return Decimal(revenue).quantize(Decimal(10) ** -2) if revenue else 0

    def get_my_revenue_by_range(self, range):
        revenue = ChargeBackLineHistory.objects.filter(contract_ref=self, updated_at__date__range=range).annotate(
            revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('revenue'))['sum']
        return Decimal(revenue).quantize(Decimal(10) ** -2) if revenue else 0

    def get_my_items_sold(self):
        units_sold = self.chargebacklinehistory_set.all().aggregate(sum=Sum('item_qty'))['sum']
        return units_sold if units_sold else 0

    def get_my_items_sold_by_range(self, range):
        units_sold = \
            self.chargebacklinehistory_set.filter(updated_at__date__range=range).aggregate(sum=Sum('item_qty'))['sum']
        return units_sold if units_sold else 0

    def get_my_indirect_purchasers_by_range(self, range):
        unique_indirect_purchasers = self.chargebacklinehistory_set.filter(updated_at__date__range=range).values(
            'indirect_customer_ref').annotate(count=Count('indirect_customer_ref'))
        return sum(x['count'] for x in unique_indirect_purchasers) if unique_indirect_purchasers else 0

    def get_my_revenue_by_cblines_history(self, cblines_history, range=None, indirect_customer_id=None):
        if range:
            cblines_history = cblines_history.filter(updated_at__date__range=range)
        if indirect_customer_id:
            cblines_history = cblines_history.filter(indirect_customer_ref_id=indirect_customer_id)
        revenue = cblines_history.annotate(
            revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('revenue'))['sum']
        return Decimal(revenue).quantize(Decimal(10) ** -2) if revenue else 0

    def get_my_items_sold_by_cblines_history(self, cblines_history, range=None, indirect_customer_id=None):
        if range:
            cblines_history = cblines_history.filter(updated_at__date__range=range)
        if indirect_customer_id:
            cblines_history = cblines_history.filter(indirect_customer_ref_id=indirect_customer_id)
        units_sold = cblines_history.aggregate(sum=Sum('item_qty'))['sum']
        return units_sold if units_sold else 0

    def get_my_indirect_purchasers_by_cblines_history(self, cblines_history, range=None):
        if range:
            cblines_history = cblines_history.filter(updated_at__date__range=range)
        unique_indirect_purchasers = cblines_history.values('indirect_customer_ref').annotate(
            count=Count('indirect_customer_ref'))
        return sum(x['count'] for x in unique_indirect_purchasers) if unique_indirect_purchasers else 0

    # Currently these are used by sort con contract overview page
    def get_my_revenue_by_mtd(self):
        cblines_history = self.get_my_chargebackline_history()
        return self.get_my_revenue_by_cblines_history(cblines_history, query_range('MTD'))

    def get_my_units_sold_by_mtd(self):
        cblines_history = self.get_my_chargebackline_history()
        return self.get_my_items_sold_by_cblines_history(cblines_history, query_range('MTD'))

    def get_my_indirect_purchasers_by_mtd(self):
        cblines_history = self.get_my_chargebackline_history()
        return self.get_my_indirect_purchasers_by_cblines_history(cblines_history, query_range('MTD'))

    @staticmethod
    def get_random_data_for_charts():
        return random.randint(10000, 150000)

    @staticmethod
    def get_random_color():
        return random.choice(COLORS_LIST)

    # EA-890 - Contract's Server tab missing Start and end Dates
    def get_my_servers_to_manage(self):
        """
        Get Servers (DirectCustomers through ContractCustomer ManyToMany relationship model)
        @To-Do - Inspired by method het_my_servers(). If this method can get modify then this one can be removed
        """
        return ContractCustomer.objects.all().select_related('contract').select_related('customer')

    # EA-1004 - Contract Number Alias
    def get_my_contract_aliases(self):
        return self.contractalias_set.order_by('alias')

    def get_contract_type(self):
        try:
            return [el[1] for el in CONTRACT_TYPES if el[0] == self.type][0]
        except:
            return ''

    def get_audits(self):
        return self.contractaudittrail_set.all()

    def get_current_info_for_audit(self):
        return {
            'number': self.number,
            'description': self.description,
            'customer_id': self.customer.name if self.customer else '',
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'eligibility': self.get_contract_eligibility(),
            'cots': self.cots,
            'type': self.get_contract_type()
        }

    def dict_for_datatable_contracts_in_indc(self, indirect_customer_id):

        cblines_history = self.get_my_chargebackline_history()
        units_sold = self.get_my_items_sold_by_cblines_history(cblines_history, query_range('MTD'),
                                                               indirect_customer_id)
        total_amount = self.get_my_revenue_by_cblines_history(cblines_history, query_range('MTD'), indirect_customer_id)
        total_sale = self.get_my_revenue_by_cblines_history(cblines_history, '', indirect_customer_id)

        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'number': self.number,
            'units_sold': units_sold,
            'total_amount': total_amount,
            'total_sale': total_sale,
        }

    def dict_for_datatable(self, is_summary=True):

        cb_lines = None
        units_sold = ''
        total_amount = ''
        indirect_purchasers = ''
        total_sale = ''
        if not is_summary:
            cblines_history = self.get_my_chargebackline_history()
            units_sold = self.get_my_items_sold_by_cblines_history(cblines_history, query_range('MTD'))
            total_amount = self.get_my_revenue_by_cblines_history(cblines_history, query_range('MTD'))
            total_sale = self.get_my_revenue_by_cblines_history(cblines_history)
            indirect_purchasers = self.get_my_indirect_purchasers_by_cblines_history(cblines_history,
                                                                                     query_range('MTD'))

        return {
            'id': self.get_id_str(),
            'number': self.number,
            'description': self.description,
            'customer_name': self.customer.name if self.customer else '',
            'type': self.get_type_display(),
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'cb_lines': cb_lines,
            'units_sold': units_sold,
            'total_amount': total_amount,
            'total_sale': total_sale,
            'indirect_purchasers': indirect_purchasers,
            'status': self.status,
            'status_name': self.get_status_display(),
        }


class ContractCustomer(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    customer = models.ForeignKey(DirectCustomer, on_delete=models.CASCADE)
    status = models.SmallIntegerField(choices=STATUSES, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.contract} {self.customer}"

    class Meta:
        verbose_name = 'Contract - Customer'
        verbose_name_plural = 'Contracts - Customers'
        db_table = "contracts_customers"
        unique_together = ('contract', 'customer')
        ordering = ('contract',)

    def get_my_chargebackline_history(self):
        return ChargeBackLineHistory.objects.filter(contract_id=self.contract.id)

    def get_my_chargeback_history(self):
        """
        :return: Queryset of Chargeback History related to the Contract customer Direct Customer
        """
        cbh = ChargeBackHistory.objects.filter(customer_id=self.customer.id)
        if cbh:
            return cbh
        return []

    def get_error_count(self):
        # Errors:  Count of Disputes from CBs for this contract, MTD from that server
        chargebacks = self.get_my_chargeback_history()
        return ChargeBackDispute.objects.filter(chargeback_id=[x.id for x in chargebacks]).count()

    @staticmethod
    def get_random_color_for_charts():
        return random.choice(COLORS_LIST)

    def get_direct_contract_cb_count_by_server(self, direct_customer, contract):
        db_name = db_ctx.get()
        cursor = connections[db_name].cursor()
        query = f'SELECT COUNT(distinct `ch`.`id`) as `cb_count` FROM `chargebacks_lines_history` `cl` INNER JOIN `chargebacks_history` `ch` ON `cl`.`chargeback_ref` = `ch`.`id` INNER JOIN `direct_customers` `dc` ON `ch`.`customer_ref` = `dc`.`id` INNER JOIN `contracts_customers` `cc` ON `dc`.`id` = `cc`.`customer_id` INNER JOIN `contracts` `c` ON `cc`.`contract_id` = `c`.`id` WHERE (`c`.`type` = "{CONTRACT_TYPE_DIRECT}" AND `c`.`number`="{contract.number}" AND `dc`.`name`="{direct_customer.name}")'
        # print(query)
        cursor.execute(query)
        row = cursor.fetchone()  # row returns tuple
        return row[0] if row[0] else '0'

    def get_direct_contract_cb_lines_and_units_sold_by_server_mtd(self, direct_customer, contract):
        cb_lines = '0'
        units_sold = '0'
        mtd_dates = query_range('MTD')
        db_name = db_ctx.get()
        cursor = connections[db_name].cursor()
        # adding 1 day to MTD because MySQL BETWEEN does not fetch data of end date provided
        query = f'SELECT COUNT(*) as `chargeback_line_count`, SUM(`cl`.`item_qty`) as `units_sold` FROM `chargebacks_lines_history` `cl` INNER JOIN `chargebacks_history` `ch` ON `cl`.`chargeback_ref` = `ch`.`id` INNER JOIN `direct_customers` `dc` ON `ch`.`customer_ref` = `dc`.`id` INNER JOIN `contracts_customers` `cc` ON `dc`.`id` = `cc`.`customer_id` INNER JOIN `contracts` `c` ON `cc`.`contract_id` = `c`.`id` WHERE (`c`.`type` = "{CONTRACT_TYPE_DIRECT}" AND `c`.`number`="{contract.number}" AND `dc`.`name`="{direct_customer.name}" AND `ch`.`processed_date` BETWEEN "{mtd_dates[0]}" AND "{mtd_dates[1] + datetime.timedelta(days=1)}")'
        # print(query)
        cursor.execute(query)
        row = cursor.fetchone()  # row returns tuple
        if row[0]:
            cb_lines = row[0]
        if row[1]:
            units_sold = int(row[1])
        return {'cb_lines': cb_lines, 'units_sold': units_sold}

    def dict_for_datatable(self, is_summary=True):
        cb_amount = 0
        cb_lines = 0
        units_sold = 0
        if not is_summary:
            cb_amount = self.contract.get_contract_cb_count_by_server(self.customer)
            cb_lines = self.contract.get_contract_cbline_count_by_server(self.customer)
            units_sold = self.contract.get_contract_units_sold_by_server(self.customer)
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'cid': self.customer.get_id_str(),
            'account_number': self.customer.account_number,
            'name': self.customer.name,
            'address': self.customer.address1,
            'city': self.customer.city,
            'state': self.customer.state,
            'zip_code': self.customer.zip_code,
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'cb_amount': cb_amount,
            'cb_lines': cb_lines,
            'units_sold': units_sold,
            'status': self.get_status_display(),
            'status_id': self.status,
        }

    # EA-1702 - Counts on the Contract's Servers tab are all showing 0 even when data is available.
    def dict_for_datatable_in_contracts(self, contract_id):
        try:
            contract = Contract.objects.get(id=contract_id)
        except:
            contract = None
        if contract.type == CONTRACT_TYPE_DIRECT:
            cb_amount = self.get_direct_contract_cb_count_by_server(self.customer, contract)
            cb_lines_attributes = self.get_direct_contract_cb_lines_and_units_sold_by_server_mtd(self.customer, contract)
        else:
            cb_amount = self.contract.get_contract_cb_count_by_server(self.customer)
            cb_lines_attributes = {}
            cb_lines_attributes["cb_lines"] = self.contract.get_contract_cbline_count_by_server(self.customer)
            cb_lines_attributes["units_sold"] = self.contract.get_contract_units_sold_by_server(self.customer)
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'cid': self.customer.get_id_str(),
            'account_number': self.customer.account_number,
            'name': self.customer.name,
            'address': self.customer.address1,
            'city': self.customer.city,
            'state': self.customer.state,
            'zip_code': self.customer.zip_code,
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'cb_amount': cb_amount if cb_amount else 0,
            'cb_lines': cb_lines_attributes["cb_lines"],
            'units_sold': cb_lines_attributes["units_sold"],
            'status': self.get_status_display(),
            'status_id': self.status,
        }

    def get_current_info_for_audit(self):
        return {
            'contract_id': self.contract.get_id_str(),
            'type': self.status,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.get_status_display()
        }


class Item(BaseModel):
    ndc = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    status = models.SmallIntegerField(choices=STATUSES, default=STATUS_ACTIVE, blank=True, null=True)

    size = models.FloatField(blank=True, null=True)
    strength = models.CharField(max_length=50, blank=True, null=True)
    brand = models.CharField(max_length=50, blank=True, null=True)
    upc = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.ndc} | {self.description} | {self.account_number}"

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ('-created_at', 'ndc')
        db_table = "items"

    def get_formatted_ndc(self):
        return f'{self.ndc[:5]}-{self.ndc[5:9]}-{self.ndc[-2:]}'

    def get_chargeback_history(self):
        return self.chargebacklinehistory_set.all()
        # return ChargeBackLineHistory.objects.filter(item_id=self.id)

    def get_mtd_units_sold_from_chargeback_history(self):
        # sum of all item quantity
        today = datetime.datetime.now().date()
        init_date = datetime.datetime(today.year, today.month, 1, 0, 0, 0).date()
        value = self.get_chargeback_history().filter(updated_at__date__range=(init_date, today)).aggregate(sum=Sum('item_qty'))['sum']
        return value if value else 0

    def get_mtd_total_from_chargeback_history(self):
        # sum of all claim amount sys
        today = datetime.datetime.now().date()
        init_date = datetime.datetime(today.year, today.month, 1, 0, 0, 0).date()
        value = self.get_chargeback_history().filter(updated_at__date__range=(init_date, today)).aggregate(
            sum=Sum('claim_amount_system'))['sum']
        return Decimal(value).quantize(Decimal(10) ** -2) if value else 0

    def get_my_revenue(self):
        """
        :return: total sum all the Charge Back revenue for this item
        """
        cbl_history = ChargeBackLineHistory.objects.filter(item_id=self.id)
        total = 0
        for cbl in cbl_history:
            total += cbl.get_extended_contract_sales()
        return total

    def get_my_revenue_by_range(self, range):
        """
        :return: total sum all the Charge Back revenue for this item
        """
        cbl_history = ChargeBackLineHistory.objects.filter(item_id=self.id, updated_at__date__range=range)
        total = 0
        for cbl in cbl_history:
            total += cbl.get_extended_contract_sales()
        return total

    def get_my_revenue_by_cblines_history(self, cblines_history, range=None, indirect_customer_id=None):
        if range:
            cblines_history = cblines_history.filter(updated_at__date__range=range)

        if indirect_customer_id:
            cblines_history = cblines_history.filter(indirect_customer_ref=indirect_customer_id)

        revenue = cblines_history.annotate(
            revenue=Sum(F('contract_price_system') * F('item_qty'), output_field=DecimalField())).aggregate(
            sum=Sum('revenue'))['sum']

        return Decimal(revenue).quantize(Decimal(10) ** -2) if revenue else 0

    def get_my_items_sold_by_cblines_history(self, cblines_history, range=None, indirect_customer_id=None):
        if range:
            cblines_history = cblines_history.filter(updated_at__date__range=range)

        if indirect_customer_id:
            cblines_history = cblines_history.filter(indirect_customer_ref=indirect_customer_id)

        units_sold = cblines_history.aggregate(sum=Sum('item_qty'))['sum']
        return units_sold if units_sold else 0

    @staticmethod
    def get_random_color():
        return random.choice(COLORS_LIST)

    def get_current_info_for_audit(self):
        return {
            'ndc': self.ndc,
            'description': self.description,
            'account_number': self.account_number,
            'strength': self.strength,
            'size': self.size,
            'brand': self.brand,
            'upc': self.upc,
            'status': self.status
        }

    def dict_for_datatable_items_in_indc(self, indirect_customer_id):

        cblines_history = self.get_chargeback_history()
        units_sold = self.get_my_items_sold_by_cblines_history(cblines_history, query_range('MTD'),
                                                               indirect_customer_id)
        total_amount = self.get_my_revenue_by_cblines_history(cblines_history, query_range('MTD'), indirect_customer_id)
        total_sale = self.get_my_revenue_by_cblines_history(cblines_history, '', indirect_customer_id)

        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'ndc': self.ndc,
            'ndc_formatted': self.get_formatted_ndc(),
            'units_sold': units_sold,
            'total_amount': total_amount,
            'total_sale': total_sale
        }

    def dict_for_datatable(self, is_summary=True):

        units_sold = ''
        total_amount = ''
        total_sale = ''
        if not is_summary:
            cblines_history = self.get_chargeback_history()
            units_sold = self.get_my_items_sold_by_cblines_history(cblines_history, query_range('MTD'))
            total_amount = self.get_my_revenue_by_cblines_history(cblines_history, query_range('MTD'))
            total_sale = self.get_my_revenue_by_cblines_history(cblines_history)

        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'ndc': self.ndc,
            'ndc_formatted': self.get_formatted_ndc(),
            'description': self.description,
            'account_number': self.account_number,
            'strength': self.strength,
            'size': self.size,
            'brand': self.brand,
            'upc': self.upc,
            'status_id': self.status,
            'status': self.get_status_display(),
            'units_sold': units_sold,
            'total_amount': total_amount,
            'total_sale': total_sale
        }


class ContractLine(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    type = models.SmallIntegerField(choices=CONTRACT_TYPES, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.SmallIntegerField(choices=STATUSES, blank=True, null=True)
    contract_line_old_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.contract.number} - {self.item}"

    class Meta:
        verbose_name = 'Contract Line'
        verbose_name_plural = 'Contracts Lines'
        ordering = ('contract',)
        db_table = "contracts_lines"

    def is_expiring_in_two_weeks(self):
        """
        Ticket 158
        - Products expiring within two weeks should show in red text.
        :return: boolean
        """
        return self.end_date <= (datetime.datetime.now() + datetime.timedelta(days=14)).date()

    def get_current_info_for_audit(self):
        return {
            'contract_id': self.contract.get_id_str(),
            'item_id': self.item.get_id_str(),
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'price': self.price,
            'type': self.type,
            'status': self.status,
            'ndc': self.item.get_formatted_ndc()
        }

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'number': self.contract.number,
            'ctype': self.contract.get_type_display(),
            'name': self.contract.description,
            'contract__start_date': self.contract.start_date.strftime('%m/%d/%Y'),
            'contract__end_date': self.contract.end_date.strftime('%m/%d/%Y'),
            'item__ndc': self.item.ndc if self.item else '',
            'item__ndc__formatted': self.item.get_formatted_ndc() if self.item else '',
            'item__type': 'NDC',
            'item__name': self.item.description if self.item else '',
            'item_uom': 'EA',
            'price': float(self.price) if self.price else '',
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'status': self.get_status_display(),
            'status_id': self.status
        }


class ContractPerformance(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    month = models.IntegerField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    order_count = models.IntegerField(blank=True, null=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    rev_by_item_json = models.CharField(max_length=100)
    orders_by_item_json = models.CharField(max_length=100)
    rev_by_whsl_json = models.CharField(max_length=100)
    contract_old_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.contract}"

    class Meta:
        verbose_name = 'Contract Performance'
        verbose_name_plural = 'Contracts Performances'
        ordering = ('contract',)
        db_table = "contracts_performances"


class ItemPerformance(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    order_count = models.IntegerField()
    orders_by_whsl_json = models.CharField(max_length=100)
    item_old_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.item}"

    class Meta:
        verbose_name = 'Item Performance'
        verbose_name_plural = 'Items Performances'
        ordering = ('item',)
        db_table = "items_performances"


class Import844(BaseModel):
    """
    844 Import model
    """
    header = JSONField(blank=True, null=True)
    line = JSONField(blank=True, null=True)
    file_name = models.CharField(max_length=200, blank=True, null=True)
    bulk_id = models.CharField(max_length=50, blank=True, null=True)  # for bulk process

    def __str__(self):
        return f"844 Import: {self.id} ({self.created_at})"

    class Meta:
        verbose_name = '844 Import'
        verbose_name_plural = '844 Imports'
        db_table = "844_imports"
        ordering = ('-created_at',)

    def chargeback_import_instances(self, db, header_validations_results, cbid_counter):

        # Distributor and DirectCustomer (from header validation results)
        distribution_center_id = header_validations_results['distribution_center_id']
        direct_customer_id = header_validations_results['direct_customer_id']

        # CHARGEBACK
        chargeback_id = generate_chargeback_id(db)
        chargeback = ChargeBack(id=chargeback_id,
                                cbid=cbid_counter,
                                import844_id=self.get_id_str(),
                                distribution_center_id=distribution_center_id if distribution_center_id else None,
                                customer_id=direct_customer_id if direct_customer_id else None,
                                document_type=self.header.get("H_DocType", "844"),
                                type=self.header.get("H_CBType", "00"),
                                date=is_valid_date(self.header["H_CBDate"]),
                                number=self.header["H_CBNumber"],
                                resubmit_number=self.header["H_ResubNo"],
                                resubmit_description=self.header["H_ResubDesc"],
                                claim_subtotal=Decimal(self.header["H_SubClaimAmt"]),
                                claim_calculate=Decimal('0.00'),
                                claim_issue=Decimal('0.00'),
                                claim_adjustment=Decimal('0.00'),
                                total_line_count=int(self.header["H_TotalCONCount"]) if self.header["H_TotalCONCount"] else None,
                                is_received_edi=True,
                                accounting_credit_memo_number='',
                                accounting_credit_memo_date=None,
                                accounting_credit_memo_amount=None,
                                is_export_849=False,
                                export_849_date=None,
                                original_chargeback_id=header_validations_results["original_chargeback_id"],
                                stage=STAGE_TYPE_IMPORTED,
                                substage=header_validations_results["substage"])

        cb_disputes_instances = []
        for dispute in header_validations_results["disputes"]:
            cb_dispute = ChargeBackDispute(chargeback_id=chargeback_id,
                                           dispute_code=dispute['code'],
                                           dispute_note=dispute['error'],
                                           field_name=dispute['field'],
                                           field_value=dispute['value'],
                                           is_active=True)
            cb_disputes_instances.append(cb_dispute)

        return chargeback, cb_disputes_instances

    def store_data_in_chargeback_table(self, header_validations_results, database):

        # Distributor and DirectCustomer (from header validation results)
        distribution_center_id = header_validations_results['distribution_center_id']
        direct_customer_id = header_validations_results['direct_customer_id']

        # CREATE CHARGEBACK
        chargeback = ChargeBack(cbid=get_next_cbid(database),
                                import844_id=self.get_id_str(),
                                distribution_center_id=distribution_center_id if distribution_center_id else None,
                                customer_id=direct_customer_id if direct_customer_id else None,
                                document_type=self.header.get("H_DocType", "844"),
                                type=self.header.get("H_CBType", "00"),
                                date=is_valid_date(self.header["H_CBDate"]),
                                number=self.header["H_CBNumber"],
                                resubmit_number=self.header["H_ResubNo"],
                                resubmit_description=self.header["H_ResubDesc"],
                                claim_subtotal=Decimal(self.header["H_SubClaimAmt"]),
                                claim_calculate=Decimal('0.00'),
                                claim_issue=Decimal('0.00'),
                                claim_adjustment=Decimal('0.00'),
                                total_line_count=int(self.header["H_TotalCONCount"]) if self.header[
                                    "H_TotalCONCount"] else None,
                                is_received_edi=True,
                                accounting_credit_memo_number='',
                                accounting_credit_memo_date=None,
                                accounting_credit_memo_amount=None,
                                is_export_849=False,
                                export_849_date=None,
                                original_chargeback_id=header_validations_results["original_chargeback_id"],
                                stage=STAGE_TYPE_IMPORTED,
                                substage=header_validations_results["substage"])
        chargeback.save()

        for dispute in header_validations_results["disputes"]:
            cb_dispute = ChargeBackDispute(chargeback_id=chargeback.id,
                                           dispute_code=dispute['code'],
                                           dispute_note=dispute['error'],
                                           field_name=dispute['field'],
                                           field_value=dispute['value'],
                                           is_active=True)
            cb_dispute.save()

        return chargeback

    def chargebacklines_import_instances(self, db, line_validations_results, chargeback, cbid_counter):

        line_disputes = line_validations_results["disputes"]

        chargebackline_id = generate_chargebackline_id(db)
        chargeback_line = ChargeBackLine(id=chargebackline_id,
                                         cblnid=cbid_counter,
                                         chargeback_id=chargeback.id,
                                         contract_id=line_validations_results["contract_id"],
                                         submitted_contract_no=self.line["L_ContractNo"],
                                         indirect_customer_id=line_validations_results["indirect_customer_id"],
                                         item_id=line_validations_results["item_id"],
                                         import844_id=self.get_id_str(),
                                         invoice_number=self.line["L_InvoiceNo"],
                                         invoice_date=is_valid_date(self.line["L_InvoiceDate"]),
                                         invoice_line_no=self.line["L_InvoiceLineNo"],
                                         invoice_note=self.line["L_InvoiceNote"],
                                         item_qty=int(self.line["L_ItemQty"]),
                                         item_uom=self.line["L_ItemUOM"],
                                         wac_submitted=Decimal(self.line["L_ItemWAC"]),
                                         contract_price_submitted=Decimal(self.line["L_ItemContractPrice"]),
                                         claim_amount_submitted=Decimal(self.line["L_ItemCreditAmt"]),
                                         wac_system=None,
                                         contract_price_system=None,
                                         claim_amount_system=None,
                                         claim_amount_issue=None,
                                         claim_amount_adjusment=None,
                                         line_status=LINE_STATUS_PENDING,
                                         # icket 737 - If line has any error on initial import should be marked with 1
                                         received_with_errors=1 if line_disputes else 0)
        cbline_disputes_instances = []
        for dispute in line_disputes:
            cbline_dispute = ChargeBackDispute(chargebackline_id=chargebackline_id,
                                               dispute_code=dispute['code'],
                                               dispute_note=dispute['error'],
                                               field_name=dispute['field'],
                                               field_value=dispute['value'],
                                               is_active=True)
            cbline_disputes_instances.append(cbline_dispute)

        return chargeback_line, cbline_disputes_instances

    def store_data_in_chargeback_line_table(self, chargeback, line_validations_results, database):

        # get lines disputes
        line_disputes = line_validations_results["disputes"]

        if chargeback.substage == SUBSTAGE_TYPE_NO_ERRORS and line_disputes:
            chargeback.substage = SUBSTAGE_TYPE_ERRORS
            chargeback.save()

        chargeback_line = ChargeBackLine(cblnid=get_next_cblnid(database),
                                         chargeback_id=chargeback.get_id_str(),
                                         contract_id=line_validations_results["contract_id"],
                                         submitted_contract_no=self.line["L_ContractNo"],
                                         indirect_customer_id=line_validations_results["indirect_customer_id"],
                                         item_id=line_validations_results["item_id"],
                                         import844_id=self.get_id_str(),
                                         invoice_number=self.line["L_InvoiceNo"],
                                         invoice_date=is_valid_date(self.line["L_InvoiceDate"]),
                                         invoice_line_no=self.line["L_InvoiceLineNo"],
                                         invoice_note=self.line["L_InvoiceNote"],
                                         item_qty=int(self.line["L_ItemQty"]),
                                         item_uom=self.line["L_ItemUOM"],
                                         wac_submitted=Decimal(self.line["L_ItemWAC"]),
                                         contract_price_submitted=Decimal(self.line["L_ItemContractPrice"]),
                                         claim_amount_submitted=Decimal(self.line["L_ItemCreditAmt"]),
                                         wac_system=None,
                                         contract_price_system=None,
                                         claim_amount_system=None,
                                         claim_amount_issue=None,
                                         claim_amount_adjusment=None,
                                         line_status=LINE_STATUS_PENDING)
        chargeback_line.save()

        for dispute in line_disputes:
            cb_dispute = ChargeBackDispute(chargebackline_id=chargeback_line.id,
                                           dispute_code=dispute['code'],
                                           dispute_note=dispute['error'],
                                           field_name=dispute['field'],
                                           field_value=dispute['value'],
                                           is_active=True)
            cb_dispute.save()

        return chargeback_line


class Import844History(BaseModel):
    """
    844 Import History model
    """
    header = JSONField(blank=True, null=True)
    line = JSONField(blank=True, null=True)
    file_name = models.CharField(max_length=200, blank=True, null=True)
    bulk_id = models.CharField(max_length=50, blank=True, null=True)  # for bulk process

    def __str__(self):
        return f"844 Import History: {self.id} ({self.created_at})"

    class Meta:
        verbose_name = '844 Import - History'
        verbose_name_plural = '844 Imports - History'
        db_table = "844_imports_history"
        ordering = ('-created_at',)

    def header_import_validations(self, data_handler):
        """
        844 Import Header Validations
        :param data_handler (map)
        :return:
        """

        distribution_centers = data_handler.dcenters
        direct_customers = data_handler.dcustomers
        open_chargebacks = data_handler.cbs_open
        history_chargebacks = data_handler.cbs_history
        credit_amt_total = data_handler.credit_amt_total

        # init results dict
        results = {
            "disputes": [],
            "substage": SUBSTAGE_TYPE_NO_ERRORS,
            "original_chargeback_id": "",
            "distribution_center_id": "",
            "direct_customer_id": "",
        }

        # Does H_DocType == 844 ?
        if not self.header['H_DocType'] == '844':
            results["disputes"].append({
                "code": "Z1",
                "error": f"Invalid DocType: {self.header['H_DocType']}",
                "field": "H_DocType",
                "value": self.header['H_DocType']
            })

        # Is H_CBDate valid?
        if not is_valid_date(self.header['H_CBDate']):
            results["disputes"].append({
                "code": "Z3",
                "error": f"Invalid CB date: {self.header['H_CBDate']}",
                "field": "H_CBDate",
                "value": self.header['H_CBDate']
            })

        # Is Distribution Center does not exist with DEA or Is DEA Number is associated with more than 1 address ?
        if not any(x['dea_number'] == self.header['H_DistID'] for x in distribution_centers):
            results["disputes"].append({
                "code": "JJ",
                "error": f"Invalid DistID: {self.header['H_DistID']}",
                "field": "H_DistID",
                "value": self.header['H_DistID']
            })
        else:
            dcenter_obj = [x for x in distribution_centers if x['dea_number'] == self.header['H_DistID']][0]
            results['distribution_center_id'] = dcenter_obj['id']
            # check if AccNo is empty, if so update header AccNo
            if not self.header['H_AcctNo'] and dcenter_obj['customer__account_number']:
                self.header['H_AcctNo'] = dcenter_obj['customer__account_number']
                self.save()

        # Is Direct Customer exist with AcctNo or Is Customer associated with only 1 account?
        if not any(x['account_number'] == self.header['H_AcctNo'] for x in direct_customers):
            results["disputes"].append({
                "code": "JJ",
                "error": f"Invalid AcctNo or multiple matches: {self.header['H_AcctNo']}",
                "field": "H_AcctNo",
                "value": self.header['H_AcctNo']
            })
        else:
            if self.header['H_AcctNo']:
                dcustomer_obj = [x for x in direct_customers if x['account_number'] == self.header['H_AcctNo']][0]
                results['direct_customer_id'] = dcustomer_obj['id']

        # Check is there any errors logged?
        if results["disputes"]:
            results["substage"] = SUBSTAGE_TYPE_ERRORS

        if Decimal(credit_amt_total).quantize(Decimal(10) ** -2) != Decimal(self.header['H_SubClaimAmt']).quantize(Decimal(10) ** -2):
            results["disputes"].append({
                "code": "ZC",
                "error": f"Submitted Claim Amt ({self.header['H_SubClaimAmt']}) != Sum of L_ItemCreditAmt ({credit_amt_total})",
                "field": "H_SubClaimAmt",
                "value": self.header['H_SubClaimAmt']
            })
            results["substage"] = SUBSTAGE_TYPE_INVALID

        # Does the CBNumber exist in processing Chargebacks or CBHistory tables?
        if self.header['H_CBType'] != '15':
            error_msg = ''
            if any(x['number'] == self.header['H_CBNumber'] for x in open_chargebacks):
                error_msg = f"Duplicate in Chargeback table: {self.header['H_CBNumber']}"
            if any(x['number'] == self.header['H_CBNumber'] for x in history_chargebacks):
                error_msg = f"Duplicate in ChargebackHistory table: {self.header['H_CBNumber']}"
            if error_msg:
                results["disputes"].append({
                    "code": "YY",
                    "error": error_msg,
                    "field": "H_CBNumber",
                    "value": self.header['H_CBNumber']
                })
                results["substage"] = SUBSTAGE_TYPE_DUPLICATES
        else: # Does H_CBType == 15 (Resubmission)
            try:
                results["original_chargeback_id"] = \
                    [x for x in history_chargebacks if x['number'] == self.header['H_CBNumber']][0]['cbid']
            except:
                results["original_chargeback_id"] = ''
            # if substage == 0 then assign 3
            if results["substage"] == SUBSTAGE_TYPE_NO_ERRORS:
                results["substage"] = SUBSTAGE_TYPE_RESUBMISSIONS

        return results

    def line_import_validations(self, db, data_handler, chargeback_line):
        results = {
            "disputes": [],
            "contract_id": "",
            "original_chargeback_id": "",
            "indirect_customer_id": "",
            "item_id": ""
        }
        # ticket EA-939 Add setting, to company settings to turn off auto add Indir Customer
        is_auto_add_new_indirect_customer = data_handler.is_auto_add_new_indirect_customer
        # ticket EA-1494
        is_cb_threshold_validation_enabled = data_handler.is_cb_threshold_validation_enabled
        cb_threshold_value = data_handler.cb_threshold_value

        contracts = data_handler.contracts
        contracts_aliases = data_handler.contracts_aliases
        items = data_handler.items
        is_for_import844 = data_handler.is_for_import844

        # Contract
        if is_for_import844:
            try:
                contract_id = [x['id'] for x in contracts if x['number'] == self.line['L_ContractNo']][0]
            except:
                try:
                    # 1004 - Contract Number Alias - If number is not in contract look up in alias
                    contract_id = [x['contract_id'] for x in contracts_aliases if x['alias'] == self.line['L_ContractNo']][0]
                except:
                    contract_id = None
        else:
            if chargeback_line.contract_ref_id:
                contract_id = chargeback_line.contract_ref_id
            else:
                try:
                    contract_id = [x['id'] for x in contracts if x['number'] == chargeback_line.submitted_contract_no][0]
                except:
                    try:
                        # 1004 - Contract Number Alias - If number is not in contract look up in alias
                        contract_id = [x['contract_id'] for x in contracts_aliases if x['alias'] == chargeback_line.submitted_contract_no][0]
                    except:
                        contract_id = ''
        if contract_id:
            results['contract_id'] = contract_id
        else:
            results["disputes"].append({
                "code": "BB",
                "error": f"Contract not found: {self.line['L_ContractNo']}",
                "field": "L_ContractNo",
                "value": self.line['L_ContractNo']
            })

        # Indirect Customer
        try:
            indirect_customer = IndirectCustomer.objects.using(db).filter(location_number=self.line['L_ShipToID'])
            if indirect_customer:
                    indirect_customer = IndirectCustomer.objects.using(db).get(location_number=self.line['L_ShipToID'])
                    indirect_customer.company_name = self.line['L_ShipToName']
                    indirect_customer.address1 = self.line['L_ShipToAddress']
                    indirect_customer.city = self.line['L_ShipToCity']
                    indirect_customer.state = self.line['L_ShipToState']
                    indirect_customer.zip_code = self.line['L_ShipToZipCode']
                    if not indirect_customer.gln_no:
                        indirect_customer.gln_no = self.line['L_ShipToGLN']
                    if not indirect_customer.bid_340:
                        indirect_customer.bid_340 = self.line['L_ShipTo340BID']
                    indirect_customer.save(using=db)
                    results['indirect_customer_id'] = indirect_customer.id
            else:
                if is_valid_location_number(self.line['L_ShipToID']):
                    indirect_customer = IndirectCustomer(location_number=self.line['L_ShipToID'],
                                                         company_name=self.line['L_ShipToName'],
                                                         address1=self.line['L_ShipToAddress'],
                                                         city=self.line['L_ShipToCity'],
                                                         state=self.line['L_ShipToState'],
                                                         zip_code=self.line['L_ShipToZipCode'],
                                                         gln_no=self.line['L_ShipToGLN'],
                                                         bid_340=self.line['L_ShipTo340BID'])
                    indirect_customer.save(using=db)
                    results['indirect_customer_id'] = indirect_customer.id
                else:
                    results["disputes"].append({
                        "code": "JJ",
                        "error": f"Data Error: Customer {self.line['L_ShipToID']} - Invalid UUID",
                        "field": "L_ShipToID",
                        "value": self.line['L_ShipToID']
                    })
                    results['indirect_customer_id'] = ''
        except ValueError:
            results["disputes"].append({
                "code": "JJ",
                "error": f"Data Error: Customer {self.line['L_ShipToID']} - Invalid UUID",
                "field": "L_ShipToID",
                "value": self.line['L_ShipToID']
            })
            results['indirect_customer_id'] = ''
        except:

            # ticket 1653 Add handling if Ind Cust DEA is invalid.
            indirect_customer = IndirectCustomer.objects.using(db).filter(location_number=self.line['L_ShipToID'])
            if not indirect_customer:
                # ticket 951 The IndCust should get created always.
                # ticket 1653 Add handling if Ind Cust DEA is invalid.
                if is_valid_location_number(self.line['L_ShipToID']):
                    indirect_customer = IndirectCustomer(location_number=self.line['L_ShipToID'],
                                                         company_name=self.line['L_ShipToName'],
                                                         address1=self.line['L_ShipToAddress'],
                                                         city=self.line['L_ShipToCity'],
                                                         state=self.line['L_ShipToState'],
                                                         zip_code=self.line['L_ShipToZipCode'],
                                                         gln_no=self.line['L_ShipToGLN'],
                                                         bid_340=self.line['L_ShipTo340BID'])
                    indirect_customer.save(using=db)
                    results['indirect_customer_id'] = indirect_customer.id
                else:
                    results["disputes"].append({
                        "code": "JJ",
                        "error": f"Data Error: Customer {self.line['L_ShipToID']} - Invalid UUID",
                        "field": "L_ShipToID",
                        "value": self.line['L_ShipToID']
                    })
                    results['indirect_customer_id'] = ''
            else:
                indirect_customer.company_name = self.line['L_ShipToName']
                indirect_customer.address1 = self.line['L_ShipToAddress']
                indirect_customer.city = self.line['L_ShipToCity']
                indirect_customer.state = self.line['L_ShipToState']
                indirect_customer.zip_code = self.line['L_ShipToZipCode']
                if not indirect_customer.gln_no:
                    indirect_customer.gln_no = self.line['L_ShipToGLN']
                if not indirect_customer.bid_340:
                    indirect_customer.bid_340 = self.line['L_ShipTo340BID']
                indirect_customer.save(using=db)
                results['indirect_customer_id'] = indirect_customer.id
            # ticket 951 If, setting OFF, create dispute, if ON, do not creaate dispute
            if not is_auto_add_new_indirect_customer:
                # ticket-939 If company settings is_auto_add_new_indirect_customer disabled,
                # create the dispute JJ - Customer Invalid and send to the exception grid
                results["disputes"].append({
                    "code": "JJ",
                    "error": f"Customer Invalid",
                    "field": "L_ShipToID",
                    "value": self.line['L_ShipToID']
                })

        # Item
        try:
            results['item_id'] = [x['id'] for x in items if x['ndc'] == self.line['L_ItemNDCNo']][0]
        except:
            results["disputes"].append({
                "code": "NN",
                "error": f"Item not found: {self.line['L_ItemNDCNo']}",
                "field": "L_ItemNDCNo",
                "value": self.line['L_ItemNDCNo']
            })

        # Is valid invoice date ?
        if not is_valid_date(self.line['L_InvoiceDate']):
            results["disputes"].append({
                "code": "EE",
                "error": f"Invalid invoice date: {self.line['L_InvoiceDate']}",
                "field": "L_InvoiceDate",
                "value": self.line['L_InvoiceDate']
            })
        # EA-1494 Expired CB Threshold validation
        if is_valid_date(self.line['L_InvoiceDate']) and is_cb_threshold_validation_enabled and cb_threshold_value !=None:
            dt = datetime.datetime.today()
            invoice_date = self.line['L_InvoiceDate'].split('/')
            to_date = datetime.datetime(dt.year, dt.month, dt.day)
            from_date = datetime.datetime(int(invoice_date[2]),int(invoice_date[0]), int(invoice_date[1]))
            delta = to_date - from_date
            if delta.days > cb_threshold_value:
                results["disputes"].append({
                    "code": "A2",
                    "error": f" Expired invoice date: {self.line['L_InvoiceDate']}",
                    "field": "L_InvoiceDate",
                    "value": self.line['L_InvoiceDate']
                })
        # Is WAC numeric value ?
        if not is_float(self.line['L_ItemWAC']):
            results["disputes"].append({
                "code": "UU",
                "error": f"Invalid WAC amount: {self.line['L_ItemWAC']}",
                "field": "L_ItemWAC",
                "value": self.line['L_ItemWAC']
            })

        # Is ItemContractPrice numeric value ?
        if not is_float(self.line['L_ItemContractPrice']):
            results["disputes"].append({
                "code": "SS",
                "error": f"Invalid ItemContractPrice amount: {self.line['L_ItemContractPrice']}",
                "field": "L_ItemContractPrice",
                "value": self.line['L_ItemContractPrice']
            })

        # Is Item CreditAmt numeric value ?
        if not is_float(self.line['L_ItemCreditAmt']):
            results["disputes"].append({
                "code": "UU",
                "error": f"Invalid L_ItemCreditAmt amount: {self.line['L_ItemCreditAmt']}",
                "field": "L_ItemCreditAmt",
                "value": self.line['L_ItemCreditAmt']
            })

        # Is Item Qty exist and is a numeric value ?
        if not self.line["L_ItemQty"] and not is_float(self.line['L_ItemQty']):
            results["disputes"].append({
                "code": "RR",
                "error": f"ItemQty is either None or not a valid number: {self.line['L_ItemQty']}",
                "field": "L_ItemQty",
                "value": self.line['L_ItemQty']
            })

        return results


class ChargeBackAbstract(BaseModel):
    cbid = models.IntegerField(blank=True, null=True)  # CB Numeric ID
    customer_id = models.CharField(max_length=100, blank=True, null=True)  # LOCAL DirectCustomer ID
    distribution_center_id = models.CharField(max_length=100, blank=True, null=True)  # LOCAL DistCenter ID
    import844_id = models.CharField(max_length=100, blank=True, null=True)  # Import844 ID

    # NEW FK fields
    customer_ref = models.ForeignKey(DirectCustomer, db_column='customer_ref', blank=True, null=True,
                                     on_delete=models.SET_NULL)
    distribution_center_ref = models.ForeignKey(DistributionCenter, db_column='distribution_center_ref', blank=True,
                                                null=True, on_delete=models.SET_NULL)
    import_844_ref = models.ForeignKey(Import844History, db_column='import_844_ref', blank=True, null=True,
                                       on_delete=models.SET_NULL)
    # end NEW FK fields

    document_type = models.CharField(max_length=5, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    type = models.CharField(max_length=5, blank=True, null=True)  # H_CBType
    number = models.CharField(max_length=20, blank=True, null=True)  # H_CBNumber
    resubmit_number = models.CharField(max_length=20, blank=True, null=True)  # H_ResubNo
    resubmit_description = models.CharField(max_length=80, blank=True, null=True)  # H_ResubDesc
    original_chargeback_id = models.CharField(max_length=100, blank=True, null=True)

    claim_subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # H_SubClaimAmt
    claim_calculate = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # TotalClaimAmtSys
    claim_issue = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # TotClaimIssue
    claim_adjustment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # TotalClaimAdj
    total_line_count = models.SmallIntegerField(blank=True, null=True)  # Total Line Count

    is_received_edi = models.BooleanField(default=True)
    accounting_credit_memo_number = models.CharField(max_length=20, blank=True, null=True)
    accounting_credit_memo_date = models.DateField(blank=True, null=True)
    accounting_credit_memo_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    is_export_849 = models.BooleanField(default=False)
    export_849_date = models.DateField(blank=True, null=True)

    stage = models.SmallIntegerField(choices=STAGES_TYPES, blank=True, null=True)
    substage = models.SmallIntegerField(choices=SUBSTAGES_TYPES, blank=True, null=True)

    class Meta:
        abstract = True

    @abstractmethod
    def get_my_chargeback_lines(self):
        pass

    @abstractmethod
    def get_my_chargeback_lines_by_db(self, db):
        pass

    @abstractmethod
    def get_my_disputes(self):
        pass

    def has_chargebacks_lines_with_pending_status(self):
        return self.get_my_chargeback_lines().filter(line_status=LINE_STATUS_PENDING).exists()

    def has_chargebacks_lines_with_disputed_status(self):
        return self.get_my_chargeback_lines().filter(line_status=LINE_STATUS_DISPUTED).exists()

    def has_all_approved_lines(self):
        return self.get_my_chargeback_lines_count() == self.get_my_approved_chargeback_lines().count()

    def get_my_pending_chargeback_lines(self):
        return self.get_my_chargeback_lines().filter(line_status=LINE_STATUS_PENDING)

    def get_my_approved_chargeback_lines(self):
        return self.get_my_chargeback_lines().filter(line_status=LINE_STATUS_APPROVED)

    def get_my_disputed_chargeback_lines(self):
        return self.get_my_chargeback_lines().filter(line_status=LINE_STATUS_DISPUTED)

    def get_my_pending_chargeback_lines_by_db(self, db):
        return self.get_my_chargeback_lines_by_db(db).filter(line_status=LINE_STATUS_PENDING)

    def get_my_chargeback_lines_count(self):
        return self.get_my_chargeback_lines().count()

    def get_my_chargeback_lines_count_db(self, db):
        return self.get_my_chargeback_lines_by_db(db).count()

    def get_my_active_disputes(self):
        return self.get_my_disputes().filter(is_active=True)

    def has_active_disputes(self):
        return self.get_my_active_disputes().exists()

    def has_active_disputes_lines(self):
        return any(cbline.has_active_disputes() for cbline in self.get_my_chargeback_lines())

    def get_my_chargeback_lines_sum_claim_amt(self):
        value = self.get_my_chargeback_lines().aggregate(sum=Sum('claim_amount_submitted'))['sum']
        return Decimal(value).quantize(Decimal(10) ** -2) if value else 0

    def calculate_total_item_quantity(self):
        chargeback_lines = self.get_my_chargeback_lines()
        total_item_qty = chargeback_lines.aggregate(sum=Sum('item_qty'))['sum']
        return total_item_qty if total_item_qty else 0

    def calculate_claim_amount_system(self):
        chargeback_lines = self.get_my_chargeback_lines()
        claim_calculate = chargeback_lines.aggregate(sum=Sum('claim_amount_system'))['sum']
        return claim_calculate if claim_calculate else 0

    def calculate_claim_amount_issue(self):
        chargeback_lines = self.get_my_chargeback_lines()
        claim_amount_issue = chargeback_lines.aggregate(sum=Sum('claim_amount_issue'))['sum']
        return claim_amount_issue if claim_amount_issue else 0

    def calculate_claim_amount_adjusment(self):
        chargeback_lines = self.get_my_chargeback_lines()
        claim_amount_adjusment = chargeback_lines.aggregate(sum=Sum('claim_amount_adjusment'))['sum']
        return claim_amount_adjusment if claim_amount_adjusment else 0

    def calculate_claim_totals(self):
        chargeback_lines = self.get_my_chargeback_lines()
        claim_calculate = chargeback_lines.aggregate(sum=Sum('claim_amount_system'))['sum']
        claim_issue = chargeback_lines.aggregate(sum=Sum('claim_amount_issue'))['sum']
        claim_adjustment = chargeback_lines.aggregate(sum=Sum('claim_amount_adjusment'))['sum']
        self.claim_calculate = claim_calculate if claim_calculate else Decimal('0.00')
        self.claim_issue = claim_issue if claim_issue else Decimal('0.00')
        self.claim_adjustment = claim_adjustment if claim_adjustment else Decimal('0.00')

    def get_my_distribution_center(self):
        return self.distribution_center_ref

    def get_my_distribution_center_name(self):
        return self.distribution_center_ref.name if self.distribution_center_ref else ''

    def get_my_customer(self):
        return self.customer_ref

    def get_my_customer_name(self):
        return self.customer_ref.name if self.customer_ref else ''

    def get_my_import844_obj(self):
        return self.import_844_ref

    def get_my_accounting_error_obj(self):
        accounting_errors = AccountingError.objects.filter(cbid=self.cbid).order_by('-created_at')
        return accounting_errors[0] if accounting_errors else None

    def get_my_accounting_error_text(self):
        accounting_error = self.get_my_accounting_error_obj()
        return accounting_error.error if accounting_error else ''

    def dict_for_datatable(self, is_summary=True):
        customer = self.get_my_customer()
        distributor = self.get_my_distribution_center()
        stage = self.get_stage_display()
        substage = self.get_substage_display()
        claim_subtotal = float(self.claim_subtotal) if self.claim_subtotal else ''
        claim_issue = float(self.claim_issue) if self.claim_issue else ''
        return {
            "DT_RowId": self.get_id_str(),
            'id': self.get_id_str(),
            'cbid': self.cbid,
            'cbnumber': self.number,
            'customer': customer.name if customer else '',
            'distributor': distributor.name if distributor else '',
            'type': self.type,
            'date': self.date.strftime('%m/%d/%Y'),
            'request': claim_subtotal,
            'issued': claim_issue,
            'stage': stage,
            'substage': substage,
            'accounting_error': self.get_my_accounting_error_text(),
            'imported': self.created_at.strftime('%m/%d/%Y'),
            'status': self.substage == SUBSTAGE_TYPE_NO_ERRORS
        }


class ChargeBack(ChargeBackAbstract):

    def __str__(self):
        return f"Chargeback {self.cbid}"

    class Meta:
        verbose_name = 'ChargeBack'
        verbose_name_plural = 'ChargeBacks'
        ordering = ('-created_at',)
        db_table = "chargebacks"

    def get_my_chargeback_lines(self):
        return self.chargebackline_set.order_by('cblnid')

    def get_my_chargeback_lines_by_db(self, db):
        return self.chargebackline_set.using(db).order_by('cblnid')

    def get_my_disputes(self):
        return self.chargebackdispute_set.all()

    def calculate_claim_totals_by_db(self, db):
        chargeback_lines = self.get_my_chargeback_lines_by_db(db)
        claim_calculate = chargeback_lines.aggregate(sum=Sum('claim_amount_system'))['sum']
        claim_issue = chargeback_lines.aggregate(sum=Sum('claim_amount_issue'))['sum']
        claim_adjustment = chargeback_lines.aggregate(sum=Sum('claim_amount_adjusment'))['sum']
        self.claim_calculate = claim_calculate if claim_calculate else Decimal('0.00')
        self.claim_issue = claim_issue if claim_issue else Decimal('0.00')
        self.claim_adjustment = claim_adjustment if claim_adjustment else Decimal('0.00')
        self.total_line_count = self.get_my_chargeback_lines_count_db(db)

    def get_my_items_dict_for_acumatica_or_ds365(self):
        my_items = {}
        for cbline in self.get_my_chargeback_lines():
            my_item = cbline.get_my_item()
            if my_item:
                my_item_accno = my_item.account_number

                if my_item_accno not in my_items.keys():
                    my_items[my_item_accno] = {
                        'item_sum_quantity': cbline.item_qty,
                        'item_sum_claim_amount_issue': cbline.claim_amount_issue,
                    }
                else:
                    my_items[my_item_accno]['item_sum_quantity'] += cbline.item_qty
                    my_items[my_item_accno]['item_sum_claim_amount_issue'] += cbline.claim_amount_issue

                my_items[my_item_accno]['item_unit_price'] = Decimal(my_items[my_item_accno]['item_sum_claim_amount_issue'] / my_items[my_item_accno]['item_sum_quantity']).quantize(Decimal(10) ** -2) if my_items[my_item_accno]['item_sum_quantity'] else 0

        return my_items


class ChargeBackHistory(ChargeBackAbstract):
    # TODO: remove later, because ID field contains the same value of the open CB after be moved
    chargeback_id = models.CharField(max_length=100, blank=True, null=True)

    # ticket EA-1035 Add additional field called processed_date to store the archived date
    processed_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Chargeback History: {self.cbid}"

    class Meta:
        verbose_name = 'ChargeBack History'
        verbose_name_plural = 'ChargeBacks History'
        db_table = "chargebacks_history"
        ordering = ('chargeback_id',)

    def get_my_chargeback_lines(self):
        return self.chargebacklinehistory_set.order_by('cblnid')

    def get_my_chargeback_lines_by_db(self, db):
        return self.chargebacklinehistory_set.using(db).order_by('cblnid')

    def get_my_disputes(self):
        return self.chargebackdisputehistory_set.all()


class ChargeBackLineAbstract(BaseModel):
    cblnid = models.IntegerField(blank=True, null=True)  # ChargebackLine Numeric ID
    chargeback_id = models.CharField(max_length=100, blank=True, null=True)  # Chargeback ID
    contract_id = models.CharField(max_length=100, blank=True, null=True)
    submitted_contract_no = models.CharField(max_length=100, blank=True, null=True)
    indirect_customer_id = models.CharField(max_length=100, blank=True, null=True)
    item_id = models.CharField(max_length=100, blank=True, null=True)
    import844_id = models.CharField(max_length=100, blank=True, null=True)

    # NEW FK fields
    contract_ref = models.ForeignKey(Contract, db_column='contract_ref', blank=True, null=True,
                                     on_delete=models.SET_NULL)
    indirect_customer_ref = models.ForeignKey(IndirectCustomer, db_column='indirect_customer_ref', blank=True,
                                              null=True, on_delete=models.SET_NULL)
    item_ref = models.ForeignKey(Item, db_column='item_ref', blank=True, null=True, on_delete=models.SET_NULL)
    import_844_ref = models.ForeignKey(Import844History, db_column='import_844_ref', blank=True, null=True,
                                       on_delete=models.SET_NULL)
    # end NEW FK fields

    # invoice
    invoice_number = models.CharField(max_length=50, blank=True, null=True)  # L_InvoiceNo
    invoice_date = models.DateField(blank=True, null=True)  # InvoiceDate
    invoice_line_no = models.CharField(max_length=30, blank=True, null=True)  # L_InvoiceLineNo
    invoice_note = models.CharField(max_length=80, blank=True, null=True)  # L_InvoiceNote

    # item
    item_qty = models.IntegerField(blank=True, null=True)  # L_ItemQty
    item_uom = models.CharField(max_length=5, blank=True, null=True)  # L_ItemUOM

    # original values
    wac_submitted = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # WACSub
    contract_price_submitted = models.DecimalField(max_digits=12, decimal_places=2, blank=True,
                                                   null=True)  # ContractPriceSub
    wac_system = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    contract_price_system = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # systems values
    claim_amount_submitted = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # ClaimAmtSub
    claim_amount_system = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # null
    claim_amount_issue = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # null
    claim_amount_adjusment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # null

    line_status = models.SmallIntegerField(choices=LINE_STATUSES, blank=True, null=True)
    approved_reason_id = models.CharField(max_length=100, blank=True, null=True)  # ApprovedReson ID (from master DB)
    user_dispute_note = models.CharField(max_length=80, blank=True, null=True)  # Use Dispute Note

    # Ticket EA-733 (new field to store Exception Action Taken)
    action_taken = models.CharField(max_length=1, choices=EXCEPTIONS_ACTIONS_TAKEN, blank=True, null=True)

    # Ticket EA-737 (new field to store erros in import)
    received_with_errors = models.SmallIntegerField(default=0)

    # Ticket EA-1263 EA-1304 (new fields to store disputes codes and notes)
    disputes_codes = models.CharField(max_length=250, blank=True, null=True)
    disputes_notes = models.CharField(max_length=300, blank=True, null=True)

    # Ticket EA-1418 - add contract_price_issued & wac_price_issued fields to CBL/CBLH table
    contract_price_issued = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    wac_price_issued = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # EA-1427 - Report Builder Enhancements - FEEDBACK: Feedback from Matt is to add additional fields to the chargeback_line and chargeback_line_history tables.
    submitted_wac_extended_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    submitted_contract_price_extended_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    system_wac_extended_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    system_contract_price_extended_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        abstract = True

    @abstractmethod
    def get_my_chargeback(self):
        pass

    @abstractmethod
    def get_my_chargeback_by_db(self, db):
        pass

    @abstractmethod
    def get_my_disputes(self):
        pass

    def get_my_contract(self):
        return self.contract_ref

    def get_my_contract_by_db(self, db):
        return self.contract_ref

    def get_my_item(self):
        return self.item_ref

    def get_my_item_ndc(self):
        if self.item_ref:
            return self.item_ref.ndc
        return ''

    def get_my_approved_reason(self):
        from ermm.models import ApprovedReason
        if self.approved_reason_id:
            my_approved_reason = ApprovedReason.objects.filter(id=self.approved_reason_id)
            if my_approved_reason.exists():
                return my_approved_reason[0]
        return None

    def get_my_indirect_customer(self):
        return self.indirect_customer_ref

    def get_my_indirect_customer_location_no(self):
        if self.indirect_customer_ref:
            return self.indirect_customer_ref.location_number
        return ''

    def get_my_indirect_customer_name(self):
        if self.indirect_customer_ref:
            return self.indirect_customer_ref.company_name
        return ''

    def get_my_indirect_customer_address1(self):
        if self.indirect_customer_ref:
            return self.indirect_customer_ref.address1
        return ''

    def get_my_indirect_customer_city(self):
        if self.indirect_customer_ref:
            return self.indirect_customer_ref.city
        return ''

    def get_my_indirect_customer_state(self):
        if self.indirect_customer_ref:
            return self.indirect_customer_ref.state
        return ''

    def get_my_indirect_customer_zipcode(self):
        if self.indirect_customer_ref:
            return self.indirect_customer_ref.zip_code
        return ''

    def get_my_indirect_customer_by_db(self, db):
        return self.indirect_customer_ref

    def get_my_customer(self):
        my_chargeback = self.get_my_chargeback()
        return my_chargeback.customer_ref if my_chargeback else None

    def get_my_distribution_center(self):
        my_chargeback = self.get_my_chargeback()
        return my_chargeback.get_my_distribution_center() if my_chargeback else None

    def get_my_import844_obj(self):
        return self.import_844_ref

    def get_my_dict_representation(self):
        from app.management.utilities.functions import model_to_dict_safe
        my_dict = model_to_dict_safe(self)

        try:
            contract = self.get_my_contract()
            contract_id = contract.get_id_str()
            contract_no = contract.number
        except:
            contract_id = ''
            contract_no = ''

        try:
            indirect_customer = self.get_my_indirect_customer()
            purchaser_id = indirect_customer.get_id_str()
            purchaser_dea = indirect_customer.location_number
            purchaser_name = indirect_customer.company_name
            purchaser_address1 = indirect_customer.address1
            purchaser_address2 = indirect_customer.address2
            purchaser_city = indirect_customer.city
            purchaser_state = indirect_customer.state
            purchaser_zipcode = indirect_customer.zip_code
        except:
            purchaser_id = ''
            purchaser_dea = ''
            purchaser_name = ''
            purchaser_address1 = ''
            purchaser_address2 = ''
            purchaser_city = ''
            purchaser_state = ''
            purchaser_zipcode = ''

        try:
            item = self.get_my_item()
            item_id = item.get_id_str()
            item_ndc = item.ndc
            item_description = item.description if item.description else ''
        except:
            item_id = ''
            item_ndc = ''
            item_description = ''

        my_dict.update({
            'contract_id':  contract_id,
            'contract_no':  contract_no,
            'purchaser_id': purchaser_id,
            'purchaser_dea': purchaser_dea,
            'purchaser_name': purchaser_name,
            'purchaser_address1': purchaser_address1,
            'purchaser_address2': purchaser_address2,
            'purchaser_city': purchaser_city,
            'purchaser_state': purchaser_state,
            'purchaser_zipcode': purchaser_zipcode,
            'item_id': item_id,
            'item_ndc':  item_ndc,
            'item_description': item_description,
        })
        return my_dict

    def get_extended_wholesaler_sales(self):
        if self.wac_system and self.item_qty:
            return Decimal(self.wac_system * self.item_qty).quantize(Decimal(10) ** -2)
        return 0

    def get_extended_contract_sales(self):
        if self.contract_price_system and self.item_qty:
            return Decimal(self.contract_price_system * self.item_qty).quantize(Decimal(10) ** -2)
        return 0

    def get_corrected_chargeback_amount(self):
        # L_WACSys - L_ContractPriceSys  (If WAC SYS is null replace with 0 before doing calculation. Do the same for contract price)
        wac = self.wac_system if self.wac_system else 0
        cp = self.contract_price_system if self.contract_price_system else 0
        return Decimal(wac - cp).quantize(Decimal(10) ** -2)

    def count_of_disputes(self):
        return self.get_my_disputes().count()

    def get_my_active_disputes(self):
        return self.get_my_disputes().filter(is_active=True)

    def has_active_disputes(self):
        return self.get_my_active_disputes().exists()

    def count_of_active_disputes(self):
        return self.get_my_active_disputes().count()

    def get_my_disputes_codes_list(self):
        return sorted([x.dispute_code for x in self.get_my_active_disputes()])

    def list_of_active_disputes_codes(self):
        my_active_disputes = self.get_my_active_disputes()
        if my_active_disputes:
            return '/'.join([x.dispute_code for x in my_active_disputes])
        return ''

    def list_of_active_disputes_notes(self):
        if self.user_dispute_note:
            return self.user_dispute_note
        else:
            my_active_disputes = self.get_my_active_disputes()
            if my_active_disputes:
                return '/'.join([x.dispute_note for x in my_active_disputes if x.dispute_note])
        return ''

    def get_my_cbid(self):
        cb = self.get_my_chargeback()
        if cb:
            return cb.cbid
        return None

    def get_my_cb_number(self):
        cb = self.get_my_chargeback()
        if cb:
            return cb.number
        return None

    def get_my_cb_date(self):
        cb = self.get_my_chargeback()
        if cb:
            return cb.date
        return None

    def get_my_cb_claim_subtotal(self):
        cb = self.get_my_chargeback()
        if cb:
            return cb.claim_subtotal
        return Decimal(0)

    def get_my_contract_number(self):
        if self.contract_ref:
            return self.contract_ref.number
        return ''

    def get_my_customer_name(self):
        cb = self.get_my_chargeback()
        if cb and cb.customer_ref:
            return cb.customer_ref.name
        return ''

    def get_my_distribution_center_name(self):
        cb = self.get_my_chargeback()
        if cb and cb.distribution_center_ref:
            return cb.distribution_center_ref.name
        return ''

    def get_my_distribution_center_address(self):
        cb = self.get_my_chargeback()
        if cb and cb.distribution_center_ref:
            return cb.distribution_center_ref.address1
        return ''

    def get_my_indirect_customer_location_number(self):
        if self.indirect_customer_ref:
            return self.indirect_customer_ref.location_number
        return ''

    def get_my_accounting_credit_memo_number(self):
        cb = self.get_my_chargeback()
        if cb and cb.accounting_credit_memo_number:
            return cb.accounting_credit_memo_number
        return ''

    def get_my_accounting_credit_memo_date(self):
        cb = self.get_my_chargeback()
        if cb and cb.accounting_credit_memo_date:
            return cb.accounting_credit_memo_date.strftime('%m/%d/%Y')
        return ''

    def get_my_accounting_credit_memo_amount(self):
        cb = self.get_my_chargeback()
        if cb and cb.accounting_credit_memo_amount:
            return cb.accounting_credit_memo_amount
        return Decimal(0)

    def get_my_accepted_status(self):
        cb = self.get_my_chargeback()
        if cb and cb.claim_issue:
            return 'Y'
        return 'N'

    def get_my_cp_system(self):
        if self.contract_price_system:
            return self.contract_price_system
        return Decimal(0)

    def get_my_wac_system(self):
        if self.wac_system:
            return self.wac_system
        return Decimal(0)

    def get_my_claim_amount_issue(self):
        if self.claim_amount_issue:
            return self.claim_amount_issue
        return Decimal(0)

    def get_my_invoice_number(self):
        if self.invoice_number:
            return self.invoice_number
        return ''

    def dict_for_datatable(self, is_summary=True):
        from ermm.models import Company
        cb = self.get_my_chargeback()
        cb_uuid = cb.get_id_str()

        try:
            cbid = cb.cbid
        except:
            cbid = ''

        try:
            cbtype = cb.type
        except:
            cbtype = ''

        try:
            cbnumber = cb.number
        except:
            cbnumber = ''

        try:
            cbdate = cb.date.strftime('%m/%d/%Y')
        except:
            cbdate = ''

        try:
            cb_cm_number = cb.accounting_credit_memo_number
        except:
            cb_cm_number = ''

        try:
            cb_cm_date = cb.accounting_credit_memo_date.strftime('%m/%d/%Y')
        except:
            cb_cm_date = ''

        try:
            cb_cm_amount = float(cb.accounting_credit_memo_amount)
        except:
            cb_cm_amount = ''

        try:
            cb_claim_subtotal = float(cb.claim_subtotal)
        except:
            cb_claim_subtotal = ''

        try:
            cb_claim_issue = float(cb.claim_issue)
            accepted_status = 'Y' if cb.claim_issue else 'N'
        except:
            cb_claim_issue = ''
            accepted_status = 'N'

        try:
            cb_processed_date = cb.processed_date.strftime('%m/%d/%Y')
        except:
            cb_processed_date = ''
        try:
            indirect_customer = self.get_my_indirect_customer()
        except:
            indirect_customer = None

        if indirect_customer:
            invalid_location_number = False
            indirect_customer_name = indirect_customer.company_name
            indirect_customer_location_no = indirect_customer.location_number
            indirect_customer_id_type = 'DEA'
            indirect_customer_address1 = indirect_customer.address1
            indirect_customer_address2 = indirect_customer.address2
            indirect_customer_complete_address = indirect_customer.get_complete_address()
            indirect_customer_city = indirect_customer.city
            indirect_customer_state = indirect_customer.state
            indirect_customer_zipcode = indirect_customer.zip_code
            indirect_customer_country = 'USA'
            try:
                indirect_customer_cot = indirect_customer.cot.trade_class
            except:
                indirect_customer_cot = ''
        else:
            import844_obj = self.get_my_import844_obj()
            invalid_location_number = True
            indirect_customer_name = import844_obj.line.get('L_ShipToName', '') if import844_obj else ''
            indirect_customer_location_no = import844_obj.line.get('L_ShipToID', '') if import844_obj else ''
            indirect_customer_id_type = 'DEA'
            indirect_customer_address1 = import844_obj.line.get('L_ShipToAddress', '') if import844_obj else ''
            indirect_customer_address2 = ''
            indirect_customer_city = import844_obj.line.get('L_ShipToCity', '') if import844_obj else ''
            indirect_customer_state = import844_obj.line.get('L_ShipToState', '') if import844_obj else ''
            indirect_customer_zipcode = import844_obj.line.get('L_ShipToZipCode', '') if import844_obj else ''
            indirect_customer_country = 'USA'
            indirect_customer_cot = ''
            indirect_customer_complete_address = f'{indirect_customer_address1}, {indirect_customer_address2}' if indirect_customer_address1 and indirect_customer_address2 else indirect_customer_address1


        try:
            customer = cb.get_my_customer()
            customer_name = customer.name
            customer_accno = customer.account_number
        except:
            customer_name = ''
            customer_accno = ''

        try:
            distributor = cb.get_my_distribution_center()
            distributor_name = distributor.name
            if distributor.dea_number:
                distributor_id = distributor.dea_number
                distributor_id_type = 'DEA'
            elif distributor.hin_number:
                distributor_id = distributor.hin_number
                distributor_id_type = 'HIN'
            else:
                distributor_id = '-'
                distributor_id_type = '-'
            distributor_address = distributor.get_complete_address()
            distributor_address1 = distributor.address1
            distributor_address2 = distributor.address2
            distributor_city = distributor.city
            distributor_state = distributor.state
            distributor_zipcode = distributor.zip_code
        except:
            distributor_name = ''
            distributor_id = '-'
            distributor_id_type = '-'
            distributor_address = '',
            distributor_address1 = ''
            distributor_address2 = ''
            distributor_city = ''
            distributor_state = ''
            distributor_zipcode = ''

        try:
            contract = self.get_my_contract()
            contract_no = contract.number
            contract_name = contract.description
            contract_cots = contract.cots
        except:
            contract_no = ''
            contract_name = ''
            contract_cots = ''

        try:
            item = self.get_my_item()
            item_ndc = item.get_formatted_ndc()
            item_brand = item.brand
            item_description = item.description
        except:
            item_ndc = ''
            item_brand = ''
            item_description = ''

        try:
            wac_submitted = float(self.wac_submitted)
        except:
            wac_submitted = ''

        try:
            wac_system = float(self.wac_system)
        except:
            wac_system = ''

        try:
            contract_price_submitted = float(self.contract_price_submitted)
        except:
            contract_price_submitted = ''

        try:
            contract_price_system = float(self.contract_price_system)
        except:
            contract_price_system = ''

        try:
            claim_amount_system = float(self.claim_amount_system)
        except:
            claim_amount_system = ''

        try:
            claim_amount_submitted = float(self.claim_amount_submitted)
        except:
            claim_amount_submitted = ''

        try:
            claim_amount_adjustment = float(self.claim_amount_adjusment)
        except:
            claim_amount_adjustment = ''

        try:
            cline_claim_amount_issue = float(self.claim_amount_issue)
        except:
            cline_claim_amount_issue = ''

        try:
            unit_cb_amount = float(self.claim_amount_issue / self.item_qty)
        except:
            unit_cb_amount = ''
        try:
            extended_wholesaler_sales = float(self.get_extended_wholesaler_sales())
        except:
            extended_wholesaler_sales = ''

        try:
            extended_contract_sales = float(self.get_extended_contract_sales())
        except:
            extended_contract_sales = ''

        try:
            company = Company.objects.get(database=db_ctx.get())
            company_name = company.name
        except:
            company_name = ''

        try:
            cline_corrected_chargeback_amount = float(self.get_corrected_chargeback_amount())
        except:
            cline_corrected_chargeback_amount = 0

        try:
            error_count = self.count_of_active_disputes()
        except:
            error_count = 0

        # response object
        return {
            "DT_RowId": self.get_id_str(),
            'id': self.get_id_str(),

            'company_name': company_name,
            'cbid': cbid,
            'cblnid': self.cblnid,
            'customer': customer_name,
            'customer_accno': customer_accno,
            'distributor': distributor_name,
            'cbnumber': cbnumber,
            'contract_no': contract_no,
            'submitted_contract_no': self.submitted_contract_no,
            'item_ndc': item_ndc,
            'item_description': item_description,
            'wac_submitted': wac_submitted,
            'wac_system': wac_system,
            'cp_submitted': contract_price_submitted,
            'cp_system': contract_price_system,
            'claim_amount_submitted': claim_amount_submitted,
            'claim_amount_system': claim_amount_system,
            'claim_amount_adjustment': claim_amount_adjustment,
            'cline_claim_amount_issue': cline_claim_amount_issue,
            'invoice_date': self.invoice_date.strftime('%m/%d/%Y') if self.invoice_date else '',
            'invoice_no': self.invoice_number,
            'invalid_location_number':invalid_location_number,
            'indirect_customer_location_no': indirect_customer_location_no,
            'indirect_customer_name': indirect_customer_name,
            'indirect_customer_address1': indirect_customer_address1,
            'indirect_customer_address2': indirect_customer_address2,
            'indirect_customer_complete_address': indirect_customer_complete_address,
            'indirect_customer_city': indirect_customer_city,
            'indirect_customer_state': indirect_customer_state,
            'indirect_customer_zipcode': indirect_customer_zipcode,
            'disputes_codes': self.disputes_codes,
            'disputes_notes': self.disputes_notes,
            'contract_cots': contract_cots,
            'error_count': error_count,
            'contract_id': self.contract_id,
            'cline_corrected_chargeback_amount': cline_corrected_chargeback_amount,
            'cb_uuid': cb_uuid,
            'cbtype': cbtype,
            'cbdate': cbdate,
            'cb_processed_date': cb_processed_date,
            'cb_claim_subtotal': cb_claim_subtotal,
            'cb_claim_issue': cb_claim_issue,
            'indicator': 'Y',
            'cb_cm_number': cb_cm_number,
            'cb_cm_date': cb_cm_date,
            'cb_cm_amount': cb_cm_amount,
            'accepted_status': accepted_status,
            'distributor_id': distributor_id,
            'distributor_id_type': distributor_id_type,
            'distributor_address': distributor_address,
            'distributor_address1': distributor_address1,
            'distributor_address2': distributor_address2,
            'distributor_city': distributor_city,
            'distributor_state': distributor_state,
            'distributor_zipcode': distributor_zipcode,
            'contract_name': contract_name,
            'item_brand': item_brand,
            'item_uom': self.item_uom,
            'item_qty': self.item_qty,
            'item_id_qualifier': 'NDC',
            'indirect_customer_id_type': indirect_customer_id_type,
            'indirect_customer_country': indirect_customer_country,
            'indirect_customer_id_qualifier': '11',
            'indirect_customer_cot': indirect_customer_cot,
            'extended_wholesaler_sales': extended_wholesaler_sales,
            'extended_contract_sales': extended_contract_sales,
            'edi_line_type': 'RA',
            'contract_or_sub_contract_no': contract_no if contract_no else self.submitted_contract_no,
            'unit_cb_amount': unit_cb_amount,
            'line_status': self.get_line_status_display()
        }


class ChargeBackLine(ChargeBackLineAbstract):
    chargeback_ref = models.ForeignKey(ChargeBack, db_column='chargeback_ref', blank=True, null=True,
                                       on_delete=models.SET_NULL)

    def __str__(self):
        return f"Chargeback Line: {self.cblnid}"

    class Meta:
        verbose_name = 'ChargeBack Line'
        verbose_name_plural = 'ChargeBacks Lines'
        db_table = "chargebacks_lines"
        ordering = ('-created_at',)

    def get_my_chargeback(self):
        if not self.chargeback_ref:
            self.chargeback_ref = ChargeBack.objects.get(id=self.chargeback_id)
            self.save()
        return self.chargeback_ref

    def get_my_chargeback_by_db(self, db):
        if not self.chargeback_ref:
            self.chargeback_ref = ChargeBack.objects.using(db).get(id=self.chargeback_id)
            self.save(using=db)
        return self.chargeback_ref

    # new method: using new fk fields
    def membership_validations(self, db, data_handler):

        disputes = []
        if self.contract_ref.member_eval:
            if not ContractMember.objects.using(db).filter(contract=self.contract_ref,
                                                           indirect_customer=self.indirect_customer_ref,
                                                           start_date__lte=self.invoice_date,
                                                           end_date__gte=self.invoice_date).exists():
                disputes.append({
                    "code": "FF",
                    "error": "Customer not covered ",
                    "field": "",
                    "value": ""
                })
        else:
            if data_handler.is_add_membership_validation and not self.contract_ref.cot_eval:

                # EA-1618 Duplication in table contracts_indirect_customers
                start_date = self.contract_ref.start_date
                end_date = datetime.datetime(2099, 12, 31).date()
                today = datetime.datetime.now().date()
                save_new_line = True
                existing_membership_lines = ContractMember.objects.using(db).filter(contract=self.contract_ref,
                                                                          indirect_customer=self.indirect_customer_ref)
                existing_cm = existing_membership_lines[0] if existing_membership_lines.exists() else None

                if existing_cm:
                    # 953 - Membership Issues (For same dates)
                    if (start_date == existing_cm.start_date and end_date == existing_cm.end_date) or (
                            start_date > existing_cm.start_date and end_date < existing_cm.end_date):
                        save_new_line = False

                    elif start_date > existing_cm.start_date and end_date >= existing_cm.end_date:
                        day_to_adjust = datetime.timedelta(1)
                        # Ending existing line one day prior new start date
                        existing_cm.end_date = start_date - day_to_adjust
                        existing_cm.status = STATUS_INACTIVE
                        # There can be multiple pending lines.
                        if today < existing_cm.start_date:
                            existing_cm.status = STATUS_PENDING

                        existing_cm.save()

                    elif start_date <= existing_cm.start_date and end_date < existing_cm.end_date:
                        day_to_adjust = datetime.timedelta(1)
                        # Moving existing start date to day after new end date
                        existing_cm.start_date = end_date + day_to_adjust
                        # There can be multiple pending lines.
                        if today < existing_cm.start_date:
                            existing_cm.status = STATUS_PENDING
                        elif today > existing_cm.end_date:
                            existing_cm.status = STATUS_INACTIVE

                        existing_cm.save()
                    # for complete inner overlap i.e. do not take any action
                    elif start_date < existing_cm.start_date and end_date > existing_cm.end_date:
                        # Extend the existing line
                        existing_cm.start_date = start_date
                        existing_cm.end_date = end_date
                        if today < existing_cm.start_date:
                            existing_cm.status = STATUS_PENDING
                        elif today > existing_cm.end_date:
                            existing_cm.status = STATUS_INACTIVE
                        else:
                            existing_cm.status = STATUS_ACTIVE
                        existing_cm.save()
                        save_new_line = False

                if save_new_line:
                    if today < start_date:
                        new_status = STATUS_PENDING
                    elif today > end_date:
                        new_status = STATUS_INACTIVE
                    else:
                        new_status = STATUS_ACTIVE

                    # create ManageMembership instance
                    ContractMember.objects.using(db).create(contract=self.contract_ref,
                                                        indirect_customer=self.indirect_customer_ref,
                                                        start_date=start_date,
                                                        end_date=end_date,
                                                        status=new_status)

        return disputes

    # new method: using new fk fields
    def cot_validations(self, db):

        disputes = []
        try:
            cot = self.indirect_customer_ref.cot
        except:
            cot = ''  # because issue with ClassOfTrade in IndirectCustomer

        if self.contract_ref and self.indirect_customer_ref and self.contract_ref.cot_eval and cot and not ContractCoT.objects.using(
                db).filter(contract_ref=self.contract_ref, cot_ref=cot).exists():
            disputes.append({
                "code": "FF",
                "error": "Customer not covered",
                "field": "",
                "value": ""
            })

        return disputes

    # new method using new fk fields
    def cb_validations(self, db):
        disputes = []

        wac_price = None
        if self.item_ref:
            # Get WACSys price (Direct Contract price) for item based on invoice date
            try:
                contract_line = ContractLine.objects.using(db).get(item=self.item_ref,
                                                                   # ticket EA-202 Change this to check the contract_customers table where contract = direct and contract_customers.customer_id = cb.customer_ref
                                                                   # contract__customer=self.get_my_customer(), # TODO: delete it once new condition is well tested
                                                                   contract__contractcustomer__customer=self.get_my_customer(),
                                                                   contract__type=CONTRACT_TYPE_DIRECT,
                                                                   # ticket EA-202 validation should check both the contract header, contract lines and server dates
                                                                   contract__start_date__lte=self.invoice_date,
                                                                   contract__end_date__gte=self.invoice_date,
                                                                   start_date__lte=self.invoice_date,
                                                                   end_date__gte=self.invoice_date,
                                                                   contract__contractcustomer__start_date__lte=self.invoice_date,
                                                                   contract__contractcustomer__end_date__gte=self.invoice_date)
                wac_price = contract_line.price
            # ticket EA-202 if there is more than one match fail CB validation with current WAC dispute code
            except MultipleObjectsReturned:
                disputes.append({
                    "code": "Z5",
                    "error": "WAC price not found",
                    "field": "wac_price",
                    "value": ""
                })
            # ticket EA-202 If no match is found, fail CB validation with current WAC dispute code
            except:
                disputes.append({
                    "code": "Z5",
                    "error": "WAC price not found",
                    "field": "wac_price",
                    "value": ""
                })
        else:
            disputes.append({
                "code": "NN",
                "error": f"Item not found: {self.import_844_ref.line['L_ItemNDCNo']}",
                "field": "L_ItemNDCNo",
                "value": self.import_844_ref.line['L_ItemNDCNo']
            })

        contract_price = None
        if self.item_ref and self.contract_ref:
            try:
                contract_line = ContractLine.objects.using(db).get(item=self.item_ref,
                                                                   contract=self.contract_ref,
                                                                   contract__type=CONTRACT_TYPE_INDIRECT,
                                                                   contract__start_date__lte=self.invoice_date,
                                                                   contract__end_date__gte=self.invoice_date,
                                                                   start_date__lte=self.invoice_date,
                                                                   end_date__gte=self.invoice_date)
                contract_price = contract_line.price
            except:
                disputes.append({
                    "code": "KK",
                    "error": "Contract price not found",
                    "field": "contract_price",
                    "value": ""
                })
        else:
            disputes.append({
                "code": "BB",
                "error": "Contract not found",
                "field": "submitted_contract_no",
                "value": self.submitted_contract_no
            })

        # If WACSys <> 0 and ContractPriceSys <> 0 and Error Found = False then: ClaimAmtSys = ItemQty * (WACSys - ContractPriceSys)
        claim_amount_sys = 0
        if wac_price and contract_price:
            claim_amount_sys = self.item_qty * (wac_price - contract_price)

        # @ClaimAmtAdj = @ClaimAmtSys ClaimAmtSub
        claim_amount_adjustment = claim_amount_sys - self.claim_amount_submitted

        # If WACSys <> WACSub and Error Found = False
        if self.item_ref and wac_price != self.wac_submitted:
            disputes.append({
                "code": "UU",
                "error": "WAC price does not match",
                "field": "wac_price",
                "value": wac_price
            })

        # If ContractPriceSys <> ContractPriceSub and Error Found = False
        if self.item_ref and contract_price != self.contract_price_submitted:
            disputes.append({
                "code": "SS",
                "error": "Contract price does not match",
                "field": "contract_price",
                "value": contract_price
            })

        # If ClaimAmtSys <> ClaimAmtSub and Error Found = False
        if self.item_ref and claim_amount_sys != self.claim_amount_submitted:
            disputes.append({
                "code": "WW",
                "error": "Claim Amounts does not match",
                "field": "claim_amount_sys",
                "value": claim_amount_sys
            })

        # Set ClaimAmtIssue = ClaimAmtSys
        claim_amount_issue = claim_amount_sys

        # Update ChargebackLine with: WACSys, ContractPriceSys, ClaimAmtSys, ClaimAmtAdjustment, ClaimAmtIssue. LineStatus and ApprovedReasonID (when no errors set linestatus = 2 and approvedreason id set id no errors)
        self.wac_system = wac_price
        self.contract_price_system = contract_price
        self.claim_amount_system = claim_amount_sys
        self.claim_amount_issue = claim_amount_issue
        self.claim_amount_adjusment = claim_amount_adjustment

        # EA - 1575 - HOTFIX: system_contract_price_extended_amount and system_wac_extended_amount are blank in CBLH
        # Whenever the wac_system or contract_system fields change the system_extended fields should get updated.
        if self.item_qty:
            if wac_price:
                self.system_wac_extended_amount = wac_price * self.item_qty
            else:
                self.system_wac_extended_amount = None
            if contract_price:
                self.system_contract_price_extended_amount = contract_price * self.item_qty
            else:
                self.system_contract_price_extended_amount = None

        # EA-1520 - If Chargeback passes all validation and is approved, contract/wac price issued fields are not getting filled in
        if not disputes:
            self.wac_price_issued = wac_price
            self.contract_price_issued = contract_price
            self.action_taken = EXCEPTION_ACTION_TAKEN_NONE
        self.save(using=db)




        return disputes

    def get_my_disputes(self):
        return self.chargebackdispute_set.order_by('-created_at')


class ChargeBackLineHistory(ChargeBackLineAbstract):
    # TODO: remove later because we are using the same ID of the open CBLine after moved it
    chargeback_line_id = models.CharField(max_length=100, blank=True, null=True)
    chargeback_ref = models.ForeignKey(ChargeBackHistory, db_column='chargeback_ref', blank=True, null=True,
                                       on_delete=models.SET_NULL)

    def __str__(self):
        return f"ChargebackLine History: {self.cblnid}"

    class Meta:
        verbose_name = 'ChargeBack Line History'
        verbose_name_plural = 'ChargeBacks Lines History'
        db_table = "chargebacks_lines_history"
        ordering = ('chargeback_id',)

    def get_my_chargeback(self):
        if not self.chargeback_ref:
            self.chargeback_ref = ChargeBackHistory.objects.get(id=self.chargeback_id)
            self.save()
        return self.chargeback_ref

    def get_my_chargeback_by_db(self, db):
        if not self.chargeback_ref:
            self.chargeback_ref = ChargeBackHistory.objects.using(db).get(id=self.chargeback_id)
            self.save(using=db)
        return self.chargeback_ref

    def get_my_disputes(self):
        return self.chargebackdisputehistory_set.order_by('-created_at')


class ChargeBackDispute(BaseModel):
    chargeback_id = models.CharField(max_length=100, blank=True, null=True)
    chargebackline_id = models.CharField(max_length=100, blank=True, null=True)
    # NEW FK fields
    chargeback_ref = models.ForeignKey(ChargeBack, db_column='chargeback_ref', blank=True, null=True,
                                       on_delete=models.SET_NULL)
    chargebackline_ref = models.ForeignKey(ChargeBackLine, db_column='chargebackline_ref', blank=True, null=True,
                                           on_delete=models.SET_NULL)
    # end NEW FK fields

    dispute_code = models.CharField(max_length=2, blank=True, null=True)
    dispute_note = models.TextField(blank=True, null=True)
    field_name = models.CharField(max_length=100, blank=True, null=True)
    field_value = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.dispute_code} {self.dispute_note}"

    class Meta:
        verbose_name = 'ChargeBackDispute - Open'
        verbose_name_plural = 'ChargeBacksDisputes - Open'
        db_table = "chargeback_disputes"
        ordering = ('-created_at',)


class ChargeBackDisputeHistory(BaseModel):
    chargeback_id = models.CharField(max_length=100, blank=True, null=True)
    chargebackline_id = models.CharField(max_length=100, blank=True, null=True)
    # NEW FK fields
    chargeback_ref = models.ForeignKey(ChargeBackHistory, db_column='chargeback_ref', blank=True, null=True, on_delete=models.SET_NULL)
    chargebackline_ref = models.ForeignKey(ChargeBackLineHistory, db_column='chargebackline_ref', blank=True, null=True, on_delete=models.SET_NULL)
    # end NEW FK fields
    dispute_code = models.CharField(max_length=2, blank=True, null=True)
    dispute_note = models.TextField(blank=True, null=True)
    field_name = models.CharField(max_length=100, blank=True, null=True)
    field_value = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.dispute_code} {self.dispute_note}"

    class Meta:
        verbose_name = 'ChargeBackDispute - History'
        verbose_name_plural = 'ChargeBacksDisputes - History'
        db_table = "chargeback_disputes_history"
        ordering = ('-created_at',)


# TODO: Remove this table is useless, ask Paul if proceed to remove it
class ChargeBackActionLog(BaseModel):
    """
    Chargeback Action Log table
    """
    chargeback_id = models.CharField(max_length=100)
    process_id = models.SmallIntegerField(choices=CB_ACTION_LOGS, default=CB_ACTION_LOG_COMPLETED)
    process_outcome = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.chargeback_id} {self.process_id} ({self.process_outcome})"

    class Meta:
        verbose_name = 'Chargeback Action Log'
        verbose_name_plural = 'Chargeback Actions Logs'
        db_table = "chargeback_action_logs"
        ordering = ('-created_at', 'chargeback_id')


class Contact(BaseModel):
    """
    Contact model
    """
    first_name = models.CharField(max_length=300)
    last_name = models.CharField(max_length=300, blank=True, null=True)
    email = models.CharField(max_length=300, blank=True, null=True)
    phone = models.CharField(max_length=300, blank=True, null=True)
    job_title = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.complete_name()} ({self.email})"

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        db_table = "contacts"
        ordering = ('first_name',)
        unique_together = ('email',)

    def complete_name(self):
        name = self.first_name
        if self.last_name:
            name = f"{self.first_name} {self.last_name}"
        return name

    def dict_for_datatable(self, is_summary=True):

        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'job_title': self.job_title,
        }


class DirectCustomerContact(BaseModel):
    direct_customer = models.ForeignKey(DirectCustomer, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.direct_customer} - {self.contact}"

    class Meta:
        verbose_name = 'Direct Customer - Contact'
        verbose_name_plural = 'Direct Customers - Contacts'
        db_table = "direct_customers_contacts"
        unique_together = ('direct_customer', 'contact')
        ordering = ('direct_customer',)


class IndirectCustomerContact(BaseModel):
    indirect_customer = models.ForeignKey(IndirectCustomer, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.indirect_customer} - {self.contact}"

    class Meta:
        verbose_name = 'Indirect Customer - Contact'
        verbose_name_plural = 'Indirect Customers - Contacts'
        db_table = "indirect_customers_contacts"
        unique_together = ('indirect_customer', 'contact')
        ordering = ('indirect_customer',)


class AuditTrail(BaseModel):
    """
    Audit Trail table to store user activities
    """
    username = models.CharField(max_length=200)
    action = models.CharField(max_length=200)
    ip_address = models.CharField(max_length=200)
    history = JSONField(blank=True, null=True)

    # TODO: remove later when new fields below have been tested
    entity = models.CharField(max_length=200)
    reference = models.CharField(max_length=300, blank=True, null=True)

    # new fields to have a better info for notifications
    entity1_name = models.CharField(max_length=200, blank=True, null=True)  # obj1 model name
    entity1_id = models.CharField(max_length=200, blank=True, null=True)  # obj1 id
    entity1_reference = models.CharField(max_length=200, blank=True, null=True)  # obj1 reference
    entity2_name = models.CharField(max_length=200, blank=True, null=True)  # obj2 model name
    entity2_id = models.CharField(max_length=200, blank=True, null=True)  # obj2 id
    entity2_reference = models.CharField(max_length=200, blank=True, null=True)  # obj2 reference

    # ticket 1090 add filename
    filename = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.username} {self.action} {self.entity} ({self.created_at}, {self.ip_address})"

    class Meta:
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
        db_table = "audit_trails"
        ordering = ('-created_at',)

    def message_time(self):

        now = datetime.datetime.now()
        diff_days = (now - self.created_at).days
        if diff_days < 0:
            diff_days = 0
        diff_secs = (now - self.created_at).seconds
        if diff_secs < 0:
            diff_secs = 0

        if diff_days:
            msg = f"at {self.created_at.strftime('%m/%d/%Y %H:%M:%S')}"

        else:
            # less than 1 min ago
            if diff_secs < 60:
                msg = "less than one minute ago"

            # less than 1 hr and more than 1 min
            elif 61 < diff_secs < 3600:
                msg = "less than one hour ago"

            # today and more than 1 hr ago
            else:
                msg = f"today at {self.created_at.strftime('%m/%d/%Y %H:%M:%S')}"

        return msg

    def dict_for_datatable(self, is_summary=True):
        message_time = self.message_time()
        created_at = self.created_at.strftime('%m-%d-%Y %H:%m')
        return {
            'id': self.get_id_str(),
            'entity': self.entity,
            'username': self.username,
            'action': self.action,
            'reference': self.reference,
            'message_time': message_time if message_time else created_at,
            'created_at': created_at
        }


class AccountingTransaction(BaseModel):
    status = models.IntegerField(choices=ACCOUNTING_TRANSACTION_STATUSES, default=ACCOUNTING_TRANSACTION_STATUS_PENDING)
    cbid = models.IntegerField(blank=True, null=True)  # CB Numeric ID
    cb_number = models.CharField(max_length=20, blank=True, null=True)  # CB Number
    cb_amount_issue = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # TotClaimIssue
    customer_accno = models.CharField(max_length=50, blank=True, null=True)  # Account Number
    post_date = models.DateField(blank=True, null=True)  # Post Date
    items = JSONField(blank=True, null=True)  # item_accno, item_qty, item_amount_issue
    cb_cm_number = models.CharField(max_length=20, blank=True, null=True)
    cb_cm_date = models.DateField(blank=True, null=True)
    cb_cm_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    integration_type = models.CharField(max_length=1, blank=True, null=True)  # Q - Quickbooks, A - Acumatica, D - DS365
    has_error = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.cbid} ({self.post_date}) [{self.get_status_display()}]"

    class Meta:
        verbose_name = 'Accounting - Transaction'
        verbose_name_plural = 'Accounting - Transactions'
        db_table = "accounting_transactions"
        ordering = ('-created_at', 'cbid')


class AccountingError(BaseModel):
    accounting_transaction = models.ForeignKey(AccountingTransaction, on_delete=models.CASCADE)
    cbid = models.IntegerField(blank=True, null=True)  # CB Numeric ID
    error = JSONField(blank=True, null=True)  # error
    cleared_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.cbid} (Error: {self.error})"

    class Meta:
        verbose_name = 'Accounting - Error'
        verbose_name_plural = 'Accounting - Errors'
        db_table = "accounting_errors"
        ordering = ('accounting_transaction', '-created_at')


class Recipient(BaseModel):
    email = models.CharField(max_length=200, blank=True, null=True)
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    is_processing = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.email} {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Recipient"
        verbose_name_plural = "Recipients"
        db_table = "recipients"
        ordering = ('email',)

# Ticket EA-875: Create a table called contract_members to store the relationship of members (Indirect Customers)
class ContractMember(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    indirect_customer = models.ForeignKey(IndirectCustomer, on_delete=models.CASCADE)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.SmallIntegerField(choices=STATUSES, blank=True, null=True)

    def __str__(self):
        return f"{self.contract} {self.indirect_customer}"

    class Meta:
        verbose_name = 'Contract - Indirect Customer'
        verbose_name_plural = 'Contracts - Indirect Customers'
        db_table = "contracts_indirect_customers"
        unique_together = ('contract', 'indirect_customer', 'created_at')
        ordering = ('contract',)

    def get_current_info_for_audit(self):
        return {
            'contract_id': self.contract_id.__str__(),
            'type': self.status,
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'status': self.get_status_display()
        }

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'number': self.contract.number,
            'company_name': self.indirect_customer.company_name,
            'location_number': self.indirect_customer.location_number,
            'bid_340': self.indirect_customer.bid_340,
            'start_date': self.start_date.strftime('%m/%d/%Y'),
            'end_date': self.end_date.strftime('%m/%d/%Y'),
            'status': self.get_status_display(),
            'status_id': self.status,
            'indirect_customer___complete_address': self.indirect_customer.get_complete_address() if self.indirect_customer else '',
            'indirect_customer__address1': self.indirect_customer.address1 if self.indirect_customer else '',
            'indirect_customer__address2': self.indirect_customer.address2 if self.indirect_customer else '',
            'indirect_customer__city': self.indirect_customer.city if self.indirect_customer else '',
            'indirect_customer__state': self.indirect_customer.state if self.indirect_customer else '',
            'indirect_customer__zip_code': self.indirect_customer.zip_code if self.indirect_customer else '',
            'indirect_customer__cot__trade_class': self.indirect_customer.cot.trade_class if self.indirect_customer and self.indirect_customer.cot else ''
        }


class ContractCoT(BaseModel):
    contract_id = models.CharField(max_length=50, blank=True, null=True)
    cot_id = models.CharField(max_length=50, blank=True, null=True)
    contract_ref = models.ForeignKey(Contract, blank=True, null=True, on_delete=models.CASCADE)
    cot_ref = models.ForeignKey(ClassOfTrade, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.contract_id} {self.cot_id}"

    class Meta:
        verbose_name = 'Contract - CoT'
        verbose_name_plural = 'Contracts - CoTs'
        db_table = "contracts_cots"
        unique_together = ('contract_id', 'cot_id')
        ordering = ('contract_id',)


class ContractAlias(BaseModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    alias = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.contract} - {self.alias}"

    class Meta:
        verbose_name = 'Contract - Alias'
        verbose_name_plural = 'Contracts - Aliases'
        db_table = "contracts_aliases"
        unique_together = ('contract', 'alias')
        ordering = ('contract',)

    def get_current_info_for_audit(self):
        return {
            'alias':self.alias
        }

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'alias': self.alias,
        }


class Report(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    root_model = models.CharField(max_length=100)
    distinct = models.BooleanField(default=False)
    report_file = models.FileField(upload_to="report_files", blank=True)
    report_file_creation = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Report Builder'
        verbose_name_plural = 'Reports Builder'
        db_table = "reports"
        ordering = ('name',)

    def __str__(self):
        return self.name

    def root_model_class(self):
        from django.apps import apps
        return apps.get_model(app_label='erms', model_name=self.root_model)

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'name': self.name,
            'description': self.description,
            'root_model': self.root_model,
            'created_at': self.created_at.strftime('%m/%d/%Y'),
            'updated_at': self.updated_at.strftime('%m/%d/%Y'),

        }


class ReportField(BaseModel):
    """ A display field to show in a report. Always belongs to a Report
    """
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)
    ref_path = models.CharField(max_length=300, blank=True, null=True)
    field = models.CharField(max_length=100)
    field_type = models.SmallIntegerField(choices=REPORT_FIELD_TYPES, default=REPORT_FIELD_SYSTEM)
    custom_value = models.CharField(max_length=300, blank=True, null=True)
    name = models.CharField(max_length=200)
    is_sortable = models.BooleanField(default=False)
    is_ascending = models.BooleanField(default=True)
    width = models.IntegerField(default=15)
    aggregate = models.CharField(
        max_length=5,
        choices=(
            ('Sum', 'Sum'),
            ('Count', 'Count'),
            ('Avg', 'Avg'),
            ('Max', 'Max'),
            ('Min', 'Min'),
        ),
        blank=True
    )
    is_total = models.BooleanField(default=False)
    is_group = models.BooleanField(default=False)

    # EA-1464 - Case statements in Report Builder
    case_is_custom_default = models.BooleanField(default=True)
    case_default_value = models.CharField(max_length=100, blank=True, null=True)

    # EA-1543 - Add the ability for users to format dates on the report
    field_data_type = models.CharField(max_length=50, blank=True, null=True)
    dateformat = models.CharField(max_length=100, default='%m/%d/%Y')
    is_currency = models.BooleanField(default=False)
    # display_format = models.ForeignKey(Format, blank=True, null=True, on_delete=models.SET_NULL)
    decimalformat = models.PositiveSmallIntegerField(default=0)
    class Meta:
        verbose_name = 'Report Builder - Field'
        verbose_name_plural = 'Report Builder - Fields'
        db_table = "reports_fields"
        ordering = ('order',)

    def get_choices(self, model, field_name):
        try:
            model_field = model._meta.get_field_by_name(field_name)[0]
        except:
            model_field = None
        if model_field and model_field.choices:
            return ((model_field.get_prep_value(key), val) for key, val in model_field.choices)

    def get_formatted_field(self):
        if self.ref_path:
            return self.ref_path.replace("__", ".") + self.field
        return self.field

    @property
    def choices_dict(self):
        choices = self.choices
        choices_dict = {}
        if choices:
            for choice in choices:
                choices_dict.update({choice[0]: choice[1]})
        return choices_dict

    def __str__(self):
        return self.name

    def get_my_cases_formatted(self):
        if self.field_type == REPORT_FIELD_CASE_STATEMENT:
            formatted_cases = ''
            cases = ReportCaseStatementField.objects.filter(report_field=self.id)
            for case in cases:
                action = '='
                if case.action == 'lt':
                    action = '<'
                elif case.action == 'gt':
                    action = '>'
                elif case.action == 'icontains':
                    action = 'LIKE'
                elif case.action == 'isnull' and case.case_then_value.startswith('1_'):
                    action = 'Is Null'
                    case.case_then_value = case.case_then_value[2:]
                elif case.action == 'isnull':
                    action = 'Is Null'
                formatted_cases += f"When {case.case_field_name}  {action}  {case.case_when_value} Then {case.case_then_value}\n"
            return formatted_cases
        else:
            return ''

    def dict_for_datatable(self, is_summary=True):

        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'name': self.name,
            'field': self.get_formatted_field(),
            'field_type': self.field_type,
            'custom_value': self.custom_value,
            'order': self.order,
            'is_sortable': self.is_sortable,
            'is_ascending': self.is_ascending,
            'width': self.width,
            'aggregate': self.aggregate,
            'is_total': self.is_total,
            'is_group': self.is_group,
            'case_is_custom_default': self.case_is_custom_default,
            'case_default_value': self.case_default_value,
            'case_statements': self.get_my_cases_formatted(),
            'is_currency': self.is_currency,
            'field_data_type': self.field_data_type,
            'dateformat': self.dateformat,
            'decimalformat':self.decimalformat
        }


class ReportFilter(BaseModel):
    """ A filter field to show in a report. Always belongs to a Report
    """
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    ref_path = models.CharField(max_length=300, blank=True, null=True)
    field = models.CharField(max_length=100)
    field_type = models.CharField(max_length=50)
    is_run_parameter = models.BooleanField(default=False)
    is_mapped_with_static_field = models.BooleanField(default=False)
    date_range = models.CharField(max_length=50, blank=True, null=True)
    is_exclude = models.BooleanField(default=False)
    action = models.CharField(max_length=10, blank=True, null=True)
    value1 = models.CharField(max_length=300, blank=True, null=True)
    value2 = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        verbose_name = 'Report Builder - Filter'
        verbose_name_plural = 'Report Builder - Filters'
        db_table = "reports_filters"
        ordering = ('field',)

    def __str__(self):
        return self.field

    def get_formatted_field(self):
        if self.ref_path:
            return self.ref_path.replace("__", ".") + self.field
        return self.field

    def get_range_values(self):
        if (self.field_type == "DateTimeField" or self.field_type == "DateField") and self.is_run_parameter:
            query = query_range(self.date_range)
            return get_dates_for_report_filter(query[0], query[1], self.value2)

        return ''

    def dict_for_datatable(self, is_summary=True):
        range_start_date = ''
        range_end_date = ''
        dyanamic_static_id = ''
        dynamic_parameter_attribute = ''
        dyanamic_static_id2 = ''
        dynamic_parameter_attribute2 = ''
        dynamic_static_date_format = ''
        dynamic_static_date_format2 = ''


        if (self.field_type == "DateTimeField" or self.field_type == "DateField") and self.is_run_parameter:
            range_start_date = self.get_range_values()[0].strftime('%m/%d/%Y') if self.get_range_values()[0] else ''
            range_end_date = self.get_range_values()[1].strftime('%m/%d/%Y') if self.get_range_values()[1] else ''

        if (self.field_type == "DateTimeField" or self.field_type == "DateField") and self.is_mapped_with_static_field:
            try:
                dyanamic_static_id_obj = ReportDynamicStaticField.objects.filter(parameter_field=self.id, parameter_attribute="SD")
                dyanamic_static_id = dyanamic_static_id_obj[0].static_field_id
                dynamic_parameter_attribute = dyanamic_static_id_obj[0].parameter_attribute
                dynamic_static_date_format = dyanamic_static_id_obj[0].static_dateformat
            except Exception as ex:
                print(ex.__str__())
                dyanamic_static_id = ''
                dynamic_parameter_attribute = ''
                dynamic_static_date_format = ''

            try:
                dyanamic_static_id_obj2 = ReportDynamicStaticField.objects.filter(parameter_field=self.id, parameter_attribute="ED")
                dyanamic_static_id2 = dyanamic_static_id_obj2[0].static_field_id
                dynamic_parameter_attribute2 = dyanamic_static_id_obj2[0].parameter_attribute
                dynamic_static_date_format2 = dyanamic_static_id_obj2[0].static_dateformat
            except Exception as ex:
                dyanamic_static_id2 = ''
                dynamic_parameter_attribute2 = ''
                dynamic_static_date_format2 = ''

        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'field': self.get_formatted_field(),
            'field_type': self.field_type,
            'is_run_parameter': self.is_run_parameter,
            'is_mapped_with_static_field': self.is_mapped_with_static_field,
            'date_range': self.date_range,
            'is_exclude': self.is_exclude,
            'action': self.action,
            'value1': self.value1,
            'value2': self.value2,
            'range_start_date': range_start_date,
            'range_end_date': range_end_date,
            'dyanamic_static_id': dyanamic_static_id,
            'dynamic_parameter_attribute': dynamic_parameter_attribute,
            'dynamic_static_date_format':dynamic_static_date_format,
            'dyanamic_static_id2': dyanamic_static_id2,
            'dynamic_parameter_attribute2': dynamic_parameter_attribute2,
            'dynamic_static_date_format2':dynamic_static_date_format2
        }


class ReportDynamicStaticField(BaseModel):
    """ A Dynamic static field to show in a run report.
    """
    static_field = models.ForeignKey(ReportField, on_delete=models.CASCADE)
    parameter_field = models.ForeignKey(ReportFilter, on_delete=models.CASCADE)
    parameter_attribute = models.CharField(max_length=10, blank=True, null=True)
    static_dateformat = models.CharField(max_length=100, default='%m/%d/%Y')
    class Meta:
        verbose_name = 'Report Builder - Dynamic Static Field'
        verbose_name_plural = 'Report Builder - Dynamic Static Fields'
        db_table = "reports_dynamic_static_fields"

    def __str__(self):
        return f"{self.static_field}"


class ScheduledReport(BaseModel):
    name = models.CharField(max_length=200, blank=True, null=True)
    report_type = models.SmallIntegerField(choices=REPORT_TYPES, blank=True, null=True)
    data_range = models.CharField(max_length=5, choices=DATA_RANGES, blank=True, null=True)
    last_sent = models.DateTimeField(blank=True, null=True)
    is_enabled = models.BooleanField(default=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, blank=True, null=True)

    # run schedule
    frequency = models.SmallIntegerField(choices=REPORT_SCHEDULE_FREQUENCIES, blank=True, null=True)
    minute = models.SmallIntegerField(blank=True, null=True)  # 0 - 59
    hour = models.SmallIntegerField(blank=True, null=True)  # 0 - 23
    monthday = models.SmallIntegerField(blank=True, null=True)  # 1 - 31
    month = models.SmallIntegerField(blank=True, null=True)  # 1 - 12
    weekday = models.SmallIntegerField(blank=True, null=True)  # 0 - 6 (sunday=0)
    recurring = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} {self.get_report_type_display()}"

    class Meta:
        verbose_name = 'Scheduled Report'
        verbose_name_plural = 'Scheduled Reports'
        db_table = "scheduled_reports"
        ordering = ('report_type', 'name')

    def get_schedule_representation(self):
        result = ''
        if self.hour is not None and 0 <= self.hour <= 23:
            # hour (0 - 23)
            result += f'{str(self.hour).zfill(2)}'
            # minute (0 - 59)
            if self.minute is not None and 0 <= self.minute <= 59:
                result += f':{str(self.minute).zfill(2)} '
            else:
                result += f':00 '
            # am or pm
            if self.hour < 12:
                result += 'AM '
            else:
                result += 'PM '

        if self.monthday:
            # monthday (1 - 31)
            if self.monthday == 1:
                value = f'{self.monthday}st'
            elif self.monthday == 2:
                value = f'{self.monthday}nd'
            elif self.monthday == 3:
                value = f'{self.monthday}rd'
            else:
                value = f'{self.monthday}th'
            result += f'on {value}'

        if self.month and 1 <= self.month <= 12:
            # month (1 - 12)
            value = MONTHS[self.month - 1][1]
            result += f'on month {value}'

        if self.weekday is not None and 0 <= self.weekday <= 6:
            # weekday (0 - 6) (sunday=0)
            value = WEEKDAYS[self.weekday][1]
            result += f'every {value}'

        return result

    def has_related_recipients(self):
        return self.scheduledreportrecipient_set.exists()

    def has_related_processing_recipients(self):
        return self.scheduledreportrecipient_set.filter(myrecipient__is_processing=True)

    def get_my_related_recipients(self):
        if not self.has_related_recipients():
            for recipient in Recipient.objects.all():
                scheduled_report_recipient, _ = ScheduledReportRecipient.objects.get_or_create(scheduled_report=self,
                                                                                               myrecipient=recipient)
        return [x.myrecipient for x in self.scheduledreportrecipient_set.all()]

    def get_my_related_processing_recipients(self):
        if not self.has_related_processing_recipients():
            for recipient in Recipient.objects.filter(is_processing=True):
                scheduled_report_processing_recipient, _ = ScheduledReportRecipient.objects.get_or_create(
                    scheduled_report=self,
                    myrecipient=recipient)
        return [x.myrecipient for x in self.scheduledreportrecipient_set.filter(myrecipient__is_processing=True)]

    def get_my_frequency(self):
        for a in REPORT_SCHEDULE_FREQUENCIES:
            if self.frequency == a[0]:
                return a[1]
        return ''

    def get_my_weekday(self):
        for a in WEEKDAYS:
            if self.weekday == a[0]:
                return a[1]
        return ''

    def get_my_monthday(self):
        for a in MONTHDAYS:
            if self.monthday == a[0]:
                return a[1]
        return ''

    def get_my_recipients_count(self):
        return self.scheduledreportrecipient_set.all().count()

    def get_schedule_rep(self):
        result = ''
        if self.hour is not None and 0 <= self.hour <= 23:
            result += f'{str(self.hour).zfill(2)}'
            # minute (0 - 59)
            if self.minute is not None and 0 <= self.minute <= 59:
                result += f':{str(self.minute).zfill(2)} '
            else:
                result += f':00 '

        if not self.frequency or self.frequency == REPORT_SCHEDULE_FREQUENCY_DAILY:
            return f'Daily : at {result}'
        elif self.frequency == REPORT_SCHEDULE_FREQUENCY_WEEKLY:
            return f'Weekly : on every {self.get_my_weekday()} at {result}'
        elif self.frequency == REPORT_SCHEDULE_FREQUENCY_MONTHLY:
            return f'Monthly : on every {self.get_my_monthday()} at {result}'
        elif self.frequency == REPORT_SCHEDULE_FREQUENCY_QUARTARLY:
            return f'Quartarly : at {result}'
        else:
            return f'at {result}'

    def report_schedule_handler(self, db, from_web, company_id,user_email=''):
        # Get report data from report to create file
        results = []

        report = self.report

        root_model = report.root_model
        is_distinct = report.distinct
        if not from_web:
            report_fields = report.reportfield_set.using(db).order_by('order')
        else:
            report_fields = report.reportfield_set.all().order_by('order')

        company = Company.objects.get(id=company_id)
        company_name = company.name

        fields_to_fetch = []
        display_headers = []
        order_by = []
        column_list = []
        annotate = {}
        format_dates_indexes = []
        is_currency_indexes = []
        field_date_formats = []
        keys_for_export = []
        headers_for_export = []
        is_decimal_indexes = []
        field_decimal_formats = []

        for rf in report_fields:
            display_name = rf.name if rf.name else rf.field
            col_field = rf.ref_path + rf.field
            headers_for_export.append(display_name)
            if col_field in keys_for_export:
                keys_for_export.append(f"{col_field}_2")
            else:
                keys_for_export.append(col_field)
            field_date_formats.append(rf.dateformat)
            field_decimal_formats.append(rf.decimalformat)

            if rf.field_data_type == "DateTimeField" or rf.field_data_type == "DateField":
                format_dates_indexes.append(rf.order)

            if rf.is_currency and (rf.field_data_type == "IntegerField" or rf.field_data_type == "DecimalField"):
                is_currency_indexes.append(rf.order)

            if rf.decimalformat and (rf.field_data_type == "IntegerField" or rf.field_data_type == "DecimalField" or rf.field_type == REPORT_FIELD_CALCULATED or rf.field_type == REPORT_FIELD_PERCENT):
                is_decimal_indexes.append(rf.order)

            if rf.field_type == REPORT_FIELD_SYSTEM:
                field = rf.ref_path + rf.field
                fields_to_fetch.append(field)
                display_headers.append(display_name)
                if col_field in column_list:
                    column_list.append(f"{col_field}_2")
                else:
                    column_list.append(col_field)
            elif rf.field_type == REPORT_FIELD_CALCULATED:
                f3 = ''
                fieldC = rf.field
                valueList = rf.custom_value.split('@@@')
                f1 = valueList[0]
                operand = valueList[1]
                f2 = valueList[2]
                if len(valueList) > 4:
                    operand2 = valueList[3]
                    f3 = float(valueList[4])
                if operand == '/':
                    if f3:
                        if operand2 == '/':
                            annotate[fieldC] = Sum(F(f1) / F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                            annotate[fieldC] = Sum(F(f1) / F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                            annotate[fieldC] = Sum(F(f1) / F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) / F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) / F(f2), output_field=DecimalField())
                elif operand == '-':
                    if f3:
                        if operand2 == '/':
                            annotate[fieldC] = Sum(F(f1) - F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                            annotate[fieldC] = Sum(F(f1) - F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                            annotate[fieldC] = Sum(F(f1) - F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) - F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) - F(f2), output_field=DecimalField())
                elif operand == '+':
                    if f3:
                        if operand2 == '/':
                            annotate[fieldC] = Sum(F(f1) + F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                            annotate[fieldC] = Sum(F(f1) + F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                            annotate[fieldC] = Sum(F(f1) + F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) + F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) + F(f2), output_field=DecimalField())
                else:
                    if f3:
                        if operand2 == '/':
                            annotate[fieldC] = Sum(F(f1) * F(f2) / f3, output_field=DecimalField())
                        elif operand2 == '-':
                            annotate[fieldC] = Sum(F(f1) * F(f2) - f3, output_field=DecimalField())
                        elif operand2 == '+':
                            annotate[fieldC] = Sum(F(f1) * F(f2) + f3, output_field=DecimalField())
                        else:
                            annotate[fieldC] = Sum(F(f1) * F(f2) * f3, output_field=DecimalField())
                    else:
                        annotate[fieldC] = Sum(F(f1) * F(f2), output_field=DecimalField())
            elif rf.field_type == REPORT_FIELD_PERCENT:
                fieldC = rf.field
                valueList = rf.custom_value.split('@@@')
                f1 = valueList[0]
                val = float(valueList[1])
                annotate[fieldC] = Sum(F(f1) * val / 100, output_field=DecimalField())
            elif rf.field_type == REPORT_FIELD_CASE_STATEMENT:
                fieldC = rf.field
                listOfWhen = []
                varNameDict = {}

                if not from_web:
                    report_case_statemets = ReportCaseStatementField.objects.using(db).filter(report_field=rf)
                else:
                    report_case_statemets = ReportCaseStatementField.objects.filter(report_field=rf)

                for caseField in report_case_statemets:
                    varKeyName = f"{caseField.case_field_name}__{caseField.action}"
                    varNameDict[varKeyName] = caseField.case_when_value
                    varVal = caseField.case_then_value
                    listOfWhen.append(When(**varNameDict, then=Value(varVal)))

                annotate[fieldC] = Case(*listOfWhen,
                                        default=F(rf.case_default_value) if not rf.case_is_custom_default else Value(
                                            rf.case_default_value),
                                        output_field=CharField()
                                        )

            if rf.is_sortable:
                if rf.is_ascending:
                    order_by.append(field)
                else:
                    order_by.append(f"-{field}")

        if fields_to_fetch:
            filterData = {}
            exclude = {}
            if not from_web:
                filter_fields = report.reportfilter_set.using(db)
            else:
                filter_fields = report.reportfilter_set.all()
            if filter_fields:
                for ff in filter_fields:
                    if ff.action:
                        field = ff.ref_path + ff.field + "__" + ff.action
                    else:
                        field = ff.ref_path + ff.field
                    if ff.field_type == "DateTimeField":
                        if ff.is_run_parameter:
                            query = query_range(ff.date_range)
                            date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                            field = ff.ref_path + ff.field + "__date__range"
                            value = date_range
                            # field = ff.ref_path + ff.field + "__date__" + ff.action
                        else:
                            value = ff.value1
                            if ff.action:
                                if ff.action == "range":
                                    field = ff.ref_path + ff.field + "__date__" + ff.action
                                else:
                                    field = ff.ref_path + ff.field + "__" + ff.action
                            else:
                                field = ff.ref_path + ff.field
                            if ff.action == "range":
                                value = [ff.value1, ff.value2]
                    elif ff.field_type == "DateField":
                        if ff.is_run_parameter:
                            query = query_range(ff.date_range)
                            date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                            field = ff.ref_path + ff.field + "__range"
                            value = date_range
                        else:
                            value = ff.value1
                            if ff.action == "range":
                                value = [ff.value1, ff.value2]
                    else:
                        if ff.action == "in":
                            if ff.value1:
                                value = ff.value1.split(',')
                            else:
                                value = []
                        else:
                            if ff.field_type == "IntegerField":
                                if not ff.value1:
                                    value = int(0)  # Because empty string for int datatype in mysql works like that
                                else:
                                    value = int(ff.value1)
                            else:
                                value = ff.value1
                    if ff.action and ff.action == 'exclude':
                        exclude_field = ff.ref_path + ff.field
                        exclude[exclude_field] = value
                    else:
                        filterData[field] = value

            model = apps.get_model(app_label='erms', model_name=root_model)
            # EA-1524 HOTFIX: Report Builder results are using Distinct.
            if annotate and is_distinct==0:
                Fieldname = model._meta.pk.name
                fields_to_fetch.insert(0, Fieldname)
            if filterData:
                queryset = model.objects.using(db).filter(**filterData).exclude(**exclude).values_list(*fields_to_fetch).order_by(*order_by)
            else:
                queryset = model.objects.using(db).exclude(**exclude).values_list(*fields_to_fetch).order_by(*order_by)

            if annotate:
                queryset = queryset.annotate(**annotate)
            # EA-1530 HOTFIX: Add the ability to distinct Report Builder results
            if is_distinct:
                queryset = queryset.distinct()

            total = queryset.count()
            total_filtered = total

        # Converting queryset into list to append custom fields
        report_data_list = list(queryset)

        for i in report_data_list:
            a = list(i)
            # Order annotate / Calulated fields as per requirement
            if annotate:
                if is_distinct == 0:
                    a.pop(0)  # EA-1524 HOTFIX: Report Builder results are using Distinct.
                annotateLength = len(annotate)
                # get those values from list
                calculatedValuesList = a[-annotateLength:]
                # remove those values from list as it will be at the end of the list always
                a = a[:-annotateLength]
                for index, calf in enumerate(report_fields.using(db).filter(field_type__in=[REPORT_FIELD_CALCULATED, REPORT_FIELD_PERCENT, REPORT_FIELD_CASE_STATEMENT])):
                    val = calculatedValuesList[index]
                    if calf.field_type != REPORT_FIELD_CASE_STATEMENT:
                        # EA - 1600 - HOTFIX: Do not round amounts when using the calculated field on Report Builder.
                        # val = Decimal(val).quantize(Decimal(10) ** -2) if val else Decimal('0.00')
                        val = Decimal(val) if val else Decimal('0.00')
                        if calf.decimalformat:
                            val = round(val,calf.decimalformat)
                    order = int(calf.order)
                    d_name = calf.name if calf.name else calf.field
                    col_field = calf.ref_path + calf.field
                    if d_name not in display_headers:
                        display_headers.insert(order, d_name)
                    if col_field not in column_list:
                        column_list.insert(order, col_field)
                    a.insert(order, val)
            for cf in report_fields.using(db).filter(field_type=REPORT_FIELD_STATIC):
                custom_field_value = cf.custom_value
                # If field is chosen for Start Date
                dynamic_static_field_obj = ReportDynamicStaticField.objects.using(db).filter(static_field=cf, parameter_attribute="SD")
                if dynamic_static_field_obj:
                    dynamic_static_field = dynamic_static_field_obj[0]
                    ff = ReportFilter.objects.using(db).get(id=dynamic_static_field.parameter_field_id)
                    if ff:
                        if ff.is_run_parameter:
                            query = query_range(ff.date_range)
                            date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                            custom_field_value = date_range[0].strftime(dynamic_static_field.static_dateformat)  # i.e. Start Date / SD
                # If field is chosen for End Date
                dynamic_static_field_obj = ReportDynamicStaticField.objects.using(db).filter(static_field=cf, parameter_attribute="ED")
                if dynamic_static_field_obj:
                    dynamic_static_field = dynamic_static_field_obj[0]
                    ff = ReportFilter.objects.using(db).get(id=dynamic_static_field.parameter_field_id)
                    if ff:
                        if ff.is_run_parameter:
                            query = query_range(ff.date_range)
                            date_range = get_dates_for_report_filter(query[0], query[1], ff.value2)
                            custom_field_value = date_range[1].strftime(dynamic_static_field.static_dateformat)
                order = int(cf.order)
                d_name = cf.name if cf.name else cf.field
                col_field = cf.ref_path + cf.field
                if d_name not in display_headers:
                    display_headers.insert(order, d_name)
                if col_field not in column_list:
                    column_list.insert(order, col_field)
                a.insert(order, custom_field_value)
                # Convert list into returnable json dataset where columns_list is json key and a is value
            a = dict(zip(column_list, a))
            results.append(a)

        file_path, file_name = export_report(report.name, headers_for_export, results, True, company_id, field_date_formats, format_dates_indexes, is_currency_indexes, keys_for_export,is_decimal_indexes,field_decimal_formats)

        if not results:
            is_empty_result = True
        else:
            is_empty_result = False

        recipient_emails_list = []

        for elem in self.scheduledreportrecipient_set.all():
            recipient_emails_list.append(elem.email)
        try:
            email = EmailMessage()
            email.subject = f"{company_name.upper()} : EmpowerRM {self.get_my_frequency()} {report.name} Report"
            email.body = render_to_string('emails/scheduled_reports.html', {'report': report, 'report_frequency': self.get_my_frequency(), 'company_name': company_name, 'is_empty_result': is_empty_result})
            email.from_email = EMAIL_HOST_USER
            email.to = recipient_emails_list
            email.content_subtype = "html"  # html content
            if not is_empty_result:
                email.attach_file(file_path)
            email.send()
        except Exception as e:
            print(e.message)

            self.last_sent = datetime.datetime.now()
            self.save(using=db)
            return {'excel_file_path': file_path, 'excel_file_name': file_name}

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'name': self.name,
            'last_sent': self.last_sent.strftime('%m/%d/%Y %H:%M:%S') if self.last_sent else '',
            'is_enabled': self.is_enabled,
            'report': self.report.name,
            'report_id': self.report.get_id_str(),
            'frequency': self.frequency,
            'minute': self.minute,
            'hour': self.hour,
            'monthday': self.monthday,
            'weekday': self.weekday,
            'schedule_representation': self.get_schedule_rep(),
            'recipients_count': self.get_my_recipients_count()

        }


class ScheduledReportRecipient(BaseModel):
    scheduled_report = models.ForeignKey(ScheduledReport, on_delete=models.CASCADE)
    myrecipient = models.ForeignKey(Recipient, blank=True, null=True, on_delete=models.CASCADE)
    email = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.scheduled_report.name}"

    class Meta:
        verbose_name = 'Scheduled Report - Recipient'
        verbose_name_plural = 'Scheduled Reports - Recipients'
        db_table = "scheduled_reports_recipients"
        ordering = ('scheduled_report', 'myrecipient')
        unique_together = ('scheduled_report', 'myrecipient')

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'email': self.email,
        }


class Data852(models.Model):
    # store the entire 852 document in json format
    document = JSONField(blank=True, null=True)

    # structure based on Ticket 682
    sender = models.CharField(max_length=50, blank=True, null=True)                         # ISA06
    receiver = models.CharField(max_length=50, blank=True, null=True)                       # ISA08

    H_thc = models.CharField(max_length=2, blank=True, null=True)                           # XQ01
    H_start_date = models.DateField(blank=True, null=True)                                  # XQ02
    H_end_date = models.DateField(blank=True, null=True)                                    # XQ03
    H_po_number = models.CharField(max_length=50, blank=True, null=True)                    # XPO01
    H_id_qualifier = models.CharField(max_length=10, blank=True, null=True)                 # XPO03

    H_ship_to_id_type = models.CharField(max_length=2, blank=True, null=True)               # N103 (ST loop)
    H_ship_to_id = models.CharField(max_length=100, blank=True, null=True)                  # N104 (ST loop)

    H_distributor_id_type = models.CharField(max_length=2, blank=True, null=True)           # N103 (DS loop)
    H_distributor_id = models.ForeignKey(DistributionCenter, db_column='H_distributor_id', to_field='dea_number', on_delete=models.SET_NULL, blank=True, null=True)

    H_reporting_location_id_type = models.CharField(max_length=2, blank=True, null=True)    # N103 (RL loop)
    H_reporting_location_id = models.CharField(max_length=100, blank=True, null=True)       # N104 (RL loop)

    L_line_item_identification = models.CharField(max_length=20, blank=True, null=True)     # LIN01
    L_item_id_qualifier = models.CharField(max_length=2, blank=True, null=True)             # LIN02
    L_item_id = models.CharField(max_length=20, blank=True, null=True)                      # LIN03

    L_BS = models.FloatField(blank=True, null=True)                                       # ZA (BS)
    L_TS = models.FloatField(blank=True, null=True)                                       # ZA (TS)
    L_QA = models.FloatField(blank=True, null=True)                                       # ZA (QA)
    L_QP = models.FloatField(blank=True, null=True)                                       # ZA (QP)
    L_QS = models.FloatField(blank=True, null=True)                                       # ZA (QS)
    L_QO = models.FloatField(blank=True, null=True)                                       # ZA (QO)
    L_QC = models.FloatField(blank=True, null=True)                                       # ZA (QC)
    L_QT = models.FloatField(blank=True, null=True)                                       # ZA (QT)
    L_QD = models.FloatField(blank=True, null=True)                                       # ZA (QD)
    L_QB = models.FloatField(blank=True, null=True)                                       # ZA (QB)
    L_Q1 = models.FloatField(blank=True, null=True)                                       # ZA (Q1)
    L_QW = models.FloatField(blank=True, null=True)                                       # ZA (QW)
    L_QR = models.FloatField(blank=True, null=True)                                       # ZA (QR)
    L_QI = models.FloatField(blank=True, null=True)                                       # ZA (QI)
    L_QZ = models.FloatField(blank=True, null=True)                                       # ZA (QZ)
    L_QH = models.FloatField(blank=True, null=True)                                       # ZA (QH)
    L_QU = models.FloatField(blank=True, null=True)                                       # ZA (QU)
    L_WQ = models.FloatField(blank=True, null=True)                                       # ZA (WQ)
    L_QE = models.FloatField(blank=True, null=True)                                           # ZA (QE)

    created_at = models.DateTimeField(auto_now_add=True)

    configuration_id = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)

    # EA-1475 - 852/867 Reports
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    wholesaler_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'XQ01: {self.H_thc}'

    class Meta:
        verbose_name = 'Data 852'
        verbose_name_plural = 'Data 852'
        db_table = 'data_852'
        ordering = ('-created_at', )


    def get_my_item_description(self):
        try:
            item = Item.objects.get(ndc=self.L_item_id)
            return item[0].description if item else ''
        except:
            return ''

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.id,
            'id': self.id,
            'document': self.document,
            'customer_name': self.customer_name,
            'wholesaler_name': self.wholesaler_name,
            'sender': self.sender,
            'receiver': self.receiver,
            'H_thc': self.H_thc,
            'H_start_date': self.H_start_date.strftime('%m/%d/%Y') if self.H_start_date else '',
            'H_end_date': self.H_end_date.strftime('%m/%d/%Y') if self.H_end_date else '',
            'H_po_number': self.H_po_number,
            'H_id_qualifier': self.H_id_qualifier,
            'H_ship_to_id_type': self.H_ship_to_id_type,
            'H_ship_to_id': self.H_ship_to_id,
            'H_distributor_id_type': self.H_distributor_id_type,
            'H_distributor_id__dea_number': self.H_distributor_id.dea_number if self.H_distributor_id else '',
            'H_distributor_id__name': self.H_distributor_id.name if self.H_distributor_id else '',
            'H_reporting_location_id_type': self.H_reporting_location_id_type,
            'H_reporting_location_id': self.H_reporting_location_id,
            'L_line_item_identification': self.L_line_item_identification,
            'L_item_id_qualifier': self.L_item_id_qualifier,
            'L_item_id': self.L_item_id,
            'L_item_id_description': self.get_my_item_description(),
            'L_BS': self.L_BS,
            'L_TS': self.L_TS,
            'L_QA': self.L_QA,
            'L_QP': self.L_QP,
            'L_QS': self.L_QS,
            'L_QO': self.L_QO,
            'L_QC': self.L_QC,
            'L_QT': self.L_QT,
            'L_QD': self.L_QD,
            'L_QB': self.L_QB,
            'L_Q1': self.L_Q1,
            'L_QW': self.L_QW,
            'L_QR': self.L_QR,
            'L_QI': self.L_QI,
            'L_QZ': self.L_QZ,
            'L_QH': self.L_QH,
            'L_QU': self.L_QU,
            'L_WQ': self.L_WQ,
            'L_QE': self.L_QE,
            'created_at': self.created_at.strftime('%m/%d/%Y') if self.H_start_date else '',
            'configuration_id': self.configuration_id,
            'transaction_id': self.transaction_id,

        }


class Data867(models.Model):
    # store the entire 867 document in json format
    document = JSONField(blank=True, null=True)

    # structure based on Ticket 683
    sender = models.CharField(max_length=50, blank=True, null=True)                     # ISA06
    receiver = models.CharField(max_length=50, blank=True, null=True)                   # ISA08

    transaction_spc = models.CharField(max_length=50, blank=True, null=True)            # BPT01
    reference_id = models.CharField(max_length=50, blank=True, null=True)               # BPT02
    report_run_date = models.DateField(blank=True, null=True)                           # BPT03
    report_type = models.CharField(max_length=50, blank=True, null=True)                # BPT04

    report_start_date = models.DateField(blank=True, null=True)                         # DTM02 (090)
    report_end_date = models.DateField(blank=True, null=True)                           # DTM02 (091)

    dist_name = models.CharField(max_length=100, blank=True, null=True)                 # N102 (DB)
    dist_dea_number = models.CharField(max_length=100, blank=True, null=True)           # N104 (DB)

    supplier_name = models.CharField(max_length=100, blank=True, null=True)
    supplier_dea_number = models.CharField(max_length=100, blank=True, null=True)

    transfer_type = models.CharField(max_length=10, blank=True, null=True)              # PDT01
    transfer_type_desc = models.CharField(max_length=100, blank=True, null=True)        # Inferred from PDT01

    invoice_no = models.CharField(max_length=100, blank=True, null=True)                # N902 (DI)
    invoice_date = models.DateField(blank=True, null=True)                              # N904 (DI)

    contract_number = models.CharField(max_length=100, blank=True, null=True)           # REF02 (CT)

    ship_to_name = models.CharField(max_length=100, blank=True, null=True)              # N102 (ST)
    ship_to_dea_number = models.CharField(max_length=100, blank=True, null=True)        # N104 (ST)
    ship_to_hin_number = models.CharField(max_length=100, blank=True, null=True)        # REF02 (H1)
    ship_to_address1 = models.CharField(max_length=100, blank=True, null=True)          # N301
    ship_to_address2 = models.CharField(max_length=100, blank=True, null=True)
    ship_to_city = models.CharField(max_length=50, blank=True, null=True)               # N401
    ship_to_state = models.CharField(max_length=50, blank=True, null=True)              # N402
    ship_to_zip = models.CharField(max_length=50, blank=True, null=True)                # N403

    quantity_type = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)                               # SII03
    quantity_uom = models.CharField(max_length=50, blank=True, null=True)               # C00101 (S1103)
    product_ndc = models.CharField(max_length=100, blank=True, null=True)               # SII02 (N4)

    purchaser_item_code = models.CharField(max_length=50, blank=True, null=True)
    mfg_part_number = models.CharField(max_length=50, blank=True, null=True)
    unit_price = models.FloatField(blank=True, null=True)                               # SII06
    unit_price_code = models.CharField(max_length=50, blank=True, null=True)
    extended_amount = models.FloatField(blank=True, null=True)                          # SII07

    product_description = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    configuration_id = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)

    # EA-1475 - 852/867 Reports
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    wholesaler_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.document} [{self.created_at.strftime("%m/%d/%Y")}]'

    class Meta:
        verbose_name = 'Data 867'
        verbose_name_plural = 'Data 867'
        db_table = 'data_867'
        ordering = ('-created_at', )

    def get_transfer_type_desc(self):
        switcher = {
            'BQ': 'Pre-Book',
            'DS': 'Drop Ship Sale',
            'IB': 'Inter-Company Transfer',
            'RV': 'Returns',
            'SD': 'Credit  Non-Return',
            'SH': 'Re-Bill',
            'SS': 'Stock Sale'
        }
        return switcher.get(self.transfer_type, "")

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.id,
            'id': self.id,
            'document': self.document,
            'wholesaler_name': self.wholesaler_name,
            'customer_name': self.customer_name,
            'sender': self.sender,
            'receiver': self.receiver,
            'transaction_spc': self.transaction_spc,
            'reference_id': self.reference_id,
            'report_type': self.report_type,
            'dist_name': self.dist_name,
            'dist_dea_number': self.dist_dea_number,
            'supplier_name': self.supplier_name,
            'supplier_dea_number': self.supplier_dea_number,
            'transfer_type': self.transfer_type,
            'transfer_type_desc': self.transfer_type_desc,
            'invoice_no': self.invoice_no,
            'contract_number': self.contract_number,
            'ship_to_name': self.ship_to_name,
            'ship_to_dea_number': self.ship_to_dea_number,
            'ship_to_hin_number': self.ship_to_hin_number,
            'ship_to_address1': self.ship_to_address1,
            'ship_to_address2': self.ship_to_address2,
            'ship_to_city': self.ship_to_city,
            'ship_to_state': self.ship_to_state,
            'ship_to_zip': self.ship_to_zip,
            'quantity_type': self.quantity_type,
            'quantity': self.quantity,
            'quantity_uom': self.quantity_uom,
            'product_ndc': self.product_ndc,
            'purchaser_item_code': self.purchaser_item_code,
            'mfg_part_number': self.mfg_part_number,
            'unit_price': self.unit_price,
            'unit_price_code': self.unit_price_code,
            'extended_amount': self.extended_amount,
            'product_description': self.product_description,
            'configuration_id': self.configuration_id,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.strftime('%m/%d/%Y') if self.created_at else '',
            'invoice_date': self.invoice_date.strftime('%m/%d/%Y') if self.invoice_date else '',
            'report_run_date': self.report_run_date.strftime('%m/%d/%Y') if self.report_run_date else '',
            'report_start_date': self.report_start_date.strftime('%m/%d/%Y') if self.report_start_date else '',
            'report_end_date': self.report_end_date.strftime('%m/%d/%Y') if self.report_end_date else '',
        }


class ReportCaseStatementField(BaseModel):
    """ A Case statement Field.
    """
    report_field = models.ForeignKey(ReportField, on_delete=models.CASCADE)
    case_field_name = models.CharField(max_length=300, blank=True, null=True)
    action = models.CharField(max_length=10, blank=True, null=True)
    case_when_value = models.CharField(max_length=100, blank=True, null=True)
    case_then_value = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Report Builder - Case Statement Field'
        verbose_name_plural = 'Report Builder - Case Statement Fields'
        db_table = "reports_case_statement_fields"

    def __str__(self):
        return f"{self.report_field}"


class ReportRunLog(BaseModel):
    """
    Report Run Log table to store Report log
    """
    email = models.CharField(max_length=200, blank=True, null=True)
    report_name = models.CharField(max_length=200, blank=True, null=True)
    company_name = models.CharField(max_length=140, blank=True, null=True)
    date_run = models.DateField(blank=True, null=True)
    time_run = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    tables_used = models.TextField(blank=True, null=True)
    result_lines = models.IntegerField(blank=True, null=True)
    time_to_create = models.IntegerField(blank=True, null=True)
    time_to_export = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Report Run Log'
        verbose_name_plural = 'Report Run Log'
        db_table = "report_run_log"
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['email', ]),
            models.Index(fields=['company_name', ]),
            models.Index(fields=['date_run', ]),]

    def __str__(self):
        return f"{self.email}"

class ContractAuditTrail(BaseModel):
    """
    Contract Audit Trail.
    """
    contract = models.ForeignKey(Contract, blank=True, null=True, on_delete=models.SET_NULL)
    user_email = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    change_type = models.CharField(max_length=10, blank=True, null=True)
    field_name = models.CharField(max_length=100, blank=True, null=True)
    product = models.ForeignKey(Item, blank=True, null=True, on_delete=models.SET_NULL)
    change_text = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        verbose_name = 'Contract Audit Trail'
        verbose_name_plural = 'Contract Audit Trails'
        db_table = "audit_contract"
        indexes = [
            models.Index(fields=['user_email', ], name="con_audit_user_email"),
            models.Index(fields=['date', ], name="con_audit_date"),
        ]

    def __str__(self):
        return f"{self.contract_id.number}"

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.get_id_str(),
            'id': self.get_id_str(),
            'contract__number': self.contract.number if self.contract else '',
            'user_email': self.user_email,
            'date': self.date.strftime('%m/%d/%Y') if self.date else '',
            'time': self.time if self.time else '',
            'change_type': self.change_type,
            'field_name': self.field_name,
            # 'product__ndc': self.product.get_formatted_ndc() if self.product else '',
            'product__ndc': self.product.ndc if self.product else '',
            'change_text': self.change_text
        }


class AuditChargeBack(BaseModel):
    """
    ChargeBack Audit Trail table to store user charge back activities
    """
    user_email = models.CharField(max_length=300, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    cbid = models.ForeignKey(ChargeBack, blank=True, null=True, on_delete=models.SET_NULL)
    cblnid = models.IntegerField(blank=True, null=True)
    change_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.cbid} {self.cblnid} {self.cblnid} ({self.created_at},{self.change_text})"

    class Meta:
        verbose_name = 'Chargeback Audit Trail'
        verbose_name_plural = 'Chargeback Audit Trails'
        db_table = "audit_chargeback"
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['date', ],name="cb_audit_date"),
            models.Index(fields=['cblnid', ],name="cb_audit_cblnid"),
            models.Index(fields=['user_email', ],name="cb_audit_user_email"),
        ]
    def get_cbid(self):
        try:
            chargeback = ChargeBack.objects.get(id=self.cbid_id)
            return chargeback.cbid if chargeback else ''
        except:
            return ''

    def dict_for_datatable(self, is_summary=True):
        return {
            'DT_RowId': self.id,
            'id': self.id,
            'date': self.date.strftime('%m/%d/%Y'),
            'time': self.time.strftime('%H:%M:%S'),
            'cbid': self.get_cbid(),
            'change_text': self.change_text,
            'created_at': self.created_at.strftime('%m/%d/%Y'),
            'updated_at': self.updated_at.strftime('%m/%d/%Y'),

        }

