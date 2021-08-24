import os

from django.contrib.auth.models import User
from django.db import models
from django_mysql.models import Model, JSONField

from app.management.utilities.basemodel import BaseModel
from app.management.utilities.constants import (SUBSCRIPTION_TYPES, DISPUTE_TYPES, RATINGS, CUSTOMER_TYPES,
                                                COT_GROUPS, MODULE_ADMINISTRATION_ID, MODULE_CHARGEBACK_ID,
                                                MODULE_EDI_ID, EDI_MAPPING_TYPES, EDI_MAPPING_STATUS_STATUSES,
                                                EDI_MAPPING_STATUS_COMPLETE, ACCOUNTING_TRANSACTION_STATUS_PENDING,
                                                ACCOUNTING_TRANSACTION_STATUSES, INTEGRATION_SYSTEM_MANUAL_ID,
                                                INTEGRATION_SYSTEM_ACUMATICA_ID, INTEGRATION_SYSTEM_QUICKBOOKS_ID,
                                                INTEGRATION_SYSTEM_NONE_ID, PROCESSING_OPTIONS,
                                                PROCESSING_OPTION_ORIGINAL_ID, INTEGRATION_SYSTEM_DYNAMICS365_ID)
from app.management.utilities.functions import strip_segment_name_which_contains_digits
from empowerb.settings import MEDIA_ROOT


class Subscription(BaseModel):
    """
    Subscription model
    """
    type = models.SmallIntegerField(choices=SUBSCRIPTION_TYPES)
    start_date = models.DateField(auto_now_add=True, blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.type}"

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        db_table = "subscriptions"
        ordering = ('type', 'start_date')
        unique_together = ('type', 'start_date', 'end_date')


class Dispute(BaseModel):
    type = models.CharField(choices=DISPUTE_TYPES, max_length=1, blank=True, null=True)
    code = models.CharField(max_length=10, blank=True, null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.code} - {self.description} ({self.type})"

    class Meta:
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'
        db_table = "disputes"
        ordering = ('code', )

    def short_name(self):
        return f"{self.code} ({self.type})"

    def save(self, force_insert=False, force_update=False, using=None, **kwargs):
        if self.code:
            self.code = self.code.upper()
        if self.type:
            self.type = self.type.upper()
        BaseModel.save(self)


class ApprovedReason(BaseModel):
    description = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.description}"

    class Meta:
        verbose_name = 'Approved Reason'
        verbose_name_plural = 'Approved Reasons'
        db_table = "approved_reasons"
        ordering = ('description', )


class Account(BaseModel):
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    subscription = models.ForeignKey(Subscription, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        db_table = "accounts"
        ordering = ('name', )

    def get_my_users(self):
        return User.objects.filter(usercompany__company__account=self).distinct()


class IntegrationSystem(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Integration System'
        verbose_name_plural = 'Integration Systems'
        db_table = "integration_systems"
        ordering = ('name', )
        unique_together = ('name', )


class Company(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    database = models.CharField(max_length=50)
    # Address
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)
    # File
    last_quickbook_file = models.FileField(upload_to='qb', blank=True)
    # Integration Configuration
    integration_system = models.ForeignKey(IntegrationSystem, blank=True, null=True, on_delete=models.CASCADE)
    integration_config = JSONField(blank=True, null=True)
    # True it means that we generate and send credit memo number based on cbid else get the credit memo number from acumatica
    generate_transaction_number = models.BooleanField(default=False)
    # True it means that the 849 file will only have disputed lines else it will has all lines (excluding pending lines)
    show_only_disputed_lines_in_849 = models.BooleanField(default=True)
    # new fields to help with import process and have cbid and cblnid counters
    cbid_counter = models.IntegerField(blank=True, null=True)
    cblnid_counter = models.IntegerField(blank=True, null=True)
    # new field for Processing Options
    processing_option = models.SmallIntegerField(choices=PROCESSING_OPTIONS, default=PROCESSING_OPTION_ORIGINAL_ID)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        db_table = "companies"
        ordering = ('name', )
        unique_together = ('database', )

    def user_has_access(self, user):
        if self.account.owner == user:
            return True
        return self.usercompany_set.filter(user=user).exists()

    def has_contracts(self):
        from erms.models import Contract
        return Contract.objects.using(self.database).exists()

    def total_contracts(self):
        from erms.models import Contract
        return Contract.objects.using(self.database).count()

    def has_items(self):
        from erms.models import Item
        return Item.objects.using(self.database).exists()

    def total_products(self):
        from erms.models import Item
        return Item.objects.using(self.database).count()

    def has_direct_customers(self):
        from erms.models import DirectCustomer
        return DirectCustomer.objects.using(self.database).exists()

    def total_direct_customers(self):
        from erms.models import DirectCustomer
        return DirectCustomer.objects.using(self.database).count()

    def has_indirect_customers(self):
        from erms.models import IndirectCustomer
        return IndirectCustomer.objects.using(self.database).exists()

    def total_indirect_customers(self):
        from erms.models import IndirectCustomer
        return IndirectCustomer.objects.using(self.database).count()

    def download_quickbook_file(self):
        return self.last_quickbook_file.url if self.last_quickbook_file else ''

    def is_none_integration(self):
        return not self.integration_system or self.integration_system.get_id_str() == INTEGRATION_SYSTEM_NONE_ID

    def is_manual_integration(self):
        return not self.integration_system or self.integration_system.get_id_str() == INTEGRATION_SYSTEM_MANUAL_ID

    def is_acumatica_integration(self):
        return self.integration_system and self.integration_system.get_id_str() == INTEGRATION_SYSTEM_ACUMATICA_ID

    def is_quickbooks_integration(self):
        return self.integration_system and self.integration_system.get_id_str() == INTEGRATION_SYSTEM_QUICKBOOKS_ID

    def is_dynamics365_integration(self):
        return self.integration_system and self.integration_system.get_id_str() == INTEGRATION_SYSTEM_DYNAMICS365_ID

    def get_my_quickbooks_configuration(self):
        qb_config, _ = QuickbooksConfigurations.objects.get_or_create(company=self)
        return qb_config

    def my_company_settings(self):
        company_settings, _ = self.companysetting_set.get_or_create()
        return company_settings

    def is_auto_chargeback_reports_enable(self):
        return self.my_company_settings().auto_chargeback_reports_enable


class QuickbooksConfigurations(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    token = models.CharField(max_length=50, blank=True, null=True)
    path = models.CharField(max_length=300, blank=True, null=True)
    interval = models.SmallIntegerField(blank=True, null=True, verbose_name='Interval (sec)')

    def __str__(self):
        return f"{self.company} ({self.token})"

    class Meta:
        verbose_name = 'Quickbooks - Configuration'
        verbose_name_plural = 'Quickbooks - Configuration'
        db_table = "quickbooks_configurations"
        ordering = ('token', 'company')
        unique_together = ('company', 'token')


class CompanySetting(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    auto_contact_notifications = models.BooleanField(default=False)
    auto_chargeback_reports_enable = models.BooleanField(default=False)
    enable_daily_report = models.BooleanField(default=False)
    default_wac_enable = models.BooleanField(default=False)
    auto_assign_big_3_as_contract_servers = models.BooleanField(default=False)
    global_customer_list_updates_overrides_local_changes = models.BooleanField(default=False)
    alert_enabled = models.BooleanField(default=False)
    alert_sent_in_single_daily_digest = models.BooleanField(default=False)
    membership_validation_enable = models.BooleanField(default=False)
    proactive_membership_validation = models.BooleanField(default=False)
    auto_contract_notification_enabled = models.BooleanField(default=False)
    class_of_trade_validation_enabled = models.BooleanField(default=False)
    automatic_chargeback_processing = models.BooleanField(default=False)
    automate_import = models.BooleanField(default=False)
    quickbooks_api_integration = models.BooleanField(default=False)
    # ticket EA-939 Auto Add New Indirect Customers
    auto_add_new_indirect_customer = models.BooleanField(default=False)
    # ticket EA-723 Add a way to show experimental settings for a company
    allow_experimental = models.BooleanField(default=False)
    # ticket EA-1494 Add Invoice Age checking to CB Validation
    enable_expired_cb_threshold = models.BooleanField(default=False)
    expired_cb_threshold = models.SmallIntegerField(blank=True, null=True)
    # EA-1576 Add a company setting to set the start page
    cb_start_page = models.CharField(max_length=100, default='/chargebacks')
    # EA-597 Add Setting to set expiration alert range for expiring contracts
    enable_contract_expiration_threshold = models.BooleanField(default=False)
    contract_expiration_threshold = models.SmallIntegerField(blank=True, null=True)

    def __str__(self):
        return "Company Settings"

    class Meta:
        verbose_name = 'Company - Setting'
        verbose_name_plural = 'Companies - Settings'
        db_table = "companies_settings"
        ordering = ('company', )
        unique_together = ('company', )


class UserCompany(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} {self.company}"

    class Meta:
        verbose_name = 'User Company'
        verbose_name_plural = 'Users Companies'
        db_table = "users_companies"
        ordering = ('company', 'user')
        unique_together = ('user', 'company')


# User extension (more data for Users)
class UserProfile(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Avatar
    avatar = models.FileField(upload_to='avatars/', blank=True, null=True)

    # Contact
    phone = models.CharField(max_length=100, blank=True, null=True)

    # About
    title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)

    # Token (could be useful for reset password, securities actions and other functionalities)
    token = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profile'
        db_table = "user_profiles"
        ordering = ('user', )
        unique_together = ('user', )

    def download_avatar(self):
        if self.avatar:
            return self.avatar.url
        return ''

    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"


class UserFeedback(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.SmallIntegerField(choices=RATINGS, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedback'
        db_table = "user_feedbacks"
        ordering = ('-created_at', )


# Customers
class DirectCustomer(BaseModel):
    """
        Direct Customers
    """
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.SmallIntegerField(choices=CUSTOMER_TYPES, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Direct Customer'
        verbose_name_plural = 'Direct Customers'
        db_table = "direct_customers"
        ordering = ('name', )

    def get_complete_address(self):
        address1 = self.address1
        address2 = self.address2
        complete_address = f'{address1}'
        if address2:
            complete_address += f' | {address2}'
        return complete_address


class DistributionCenter(BaseModel):
    customer = models.ForeignKey(DirectCustomer, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=300, blank=True, null=True)
    dea_number = models.CharField(max_length=20, blank=True, null=True)
    hin_number = models.CharField(max_length=20, blank=True, null=True)
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.customer} {self.dea_number}"

    class Meta:
        verbose_name = 'Distribution Center'
        verbose_name_plural = 'Distribution Centers'
        db_table = "distribution_centers"
        ordering = ('-created_at', )


class IndirectCustomer(BaseModel):
    """
        Indirect Customers
    """
    account_number = models.CharField(max_length=20, blank=True, null=True)                 # AcctNo
    name = models.CharField(max_length=200, blank=True, null=True)                          # CompanyName
    email = models.CharField(max_length=200, blank=True, null=True)                         # MainEmail
    phone = models.CharField(max_length=100, blank=True, null=True)                         # MainPhone
    # Address
    address1 = models.CharField(max_length=300, blank=True, null=True)
    address2 = models.CharField(max_length=300, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.account_number}"

    class Meta:
        verbose_name = 'Indirect Customer'
        verbose_name_plural = 'Indirect Customers'
        db_table = "indirect_customers"
        ordering = ('name', )


class ClassOfTrade(BaseModel):
    """
    Class of Trade model (CoT)
    """
    group = models.SmallIntegerField(choices=COT_GROUPS, blank=True, null=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_group_display()} - {self.value}"

    class Meta:
        verbose_name = 'Class of Trade'
        verbose_name_plural = 'Classes of Trades'
        db_table = "class_of_trade"
        ordering = ('group', 'value')
        unique_together = ('group', 'value')


# New models Roles and UserRole (Ticket EA-668)
class Role(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        db_table = "roles"
        ordering = ('name', )
        unique_together = ('name', )


class UserRole(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.role}"

    class Meta:
        verbose_name = 'User Role'
        verbose_name_plural = 'Users Roles'
        db_table = "users_roles"
        ordering = ('role', 'user')
        unique_together = ('user', 'role')


# New models Module, Views and CompanyModule (Ticket EA-669)
class Module(BaseModel):
    name = models.CharField(max_length=100)
    order = models.SmallIntegerField(default=0)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'
        db_table = "modules"
        ordering = ('order', )
        unique_together = ('name', )

    def is_administration(self):
        return self.get_id_str() == MODULE_ADMINISTRATION_ID

    def is_chargeback(self):
        return self.get_id_str() == MODULE_CHARGEBACK_ID

    def get_my_views(self):
        return self.view_set.all()

    def is_edi(self):
        return self.get_id_str() == MODULE_EDI_ID

    def save(self, force_insert=False, force_update=False, using=None, **kwargs):
        self.name = self.name.upper()
        if using:
            BaseModel.save(self, using=using)
        else:
            BaseModel.save(self)


class View(BaseModel):
    name = models.CharField(max_length=100)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    order = models.SmallIntegerField(default=0)
    # options for menu
    icon = models.CharField(max_length=100, blank=True, null=True)
    link = models.CharField(max_length=100, blank=True, null=True)
    option = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.module})"

    class Meta:
        verbose_name = 'View'
        verbose_name_plural = 'Views'
        db_table = "views"
        ordering = ('module', 'order')
        unique_together = ('module', 'name')


class CompanyModule(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.company} {self.module} ({self.enabled})"

    class Meta:
        verbose_name = 'Company - Module'
        verbose_name_plural = 'Companies - Modules'
        db_table = "companies_modules"
        ordering = ('company', 'module')
        unique_together = ('company', 'module')


class EDIMappingTemplate(BaseModel):
    name = models.CharField(max_length=300)
    document_type = models.CharField(max_length=10, blank=True, null=True)
    output_format = models.CharField(max_length=10, blank=True, null=True)
    mapping_type = models.SmallIntegerField(choices=EDI_MAPPING_TYPES, blank=True, null=True)
    delimiter = models.CharField(max_length=2, blank=True, null=True)
    show_header = models.BooleanField(default=False)
    main_loop_segment = models.CharField(max_length=10, blank=True, null=True)
    nested_loop_segment = models.CharField(max_length=10, blank=True, null=True)
    end_loop_segment = models.CharField(max_length=10, blank=True, null=True)
    status = models.SmallIntegerField(choices=EDI_MAPPING_STATUS_STATUSES, blank=True, null=True)

    def __str__(self):
        return f"{self.name} (DocT: {self.document_type}, Fmt: {self.output_format})"

    class Meta:
        verbose_name = 'EDI Mapping Template'
        verbose_name_plural = 'EDI Mappings Templates'
        db_table = "edi_mapping_templates"
        ordering = ('-created_at', )
        unique_together = ('name', 'document_type')

    def get_my_details(self):
        return self.edimappingtemplatedetail_set.order_by('created_at')

    def get_map_names_list(self):
        return self.get_my_details().values_list('map_name', flat=True)

    def get_map_descriptors_list(self):
        descriptors = self.get_my_details().values_list('map_descriptor', flat=True)
        return list(set(list(filter(None, descriptors))))

    def get_segment_name_and_descriptor_based_on_map_name(self, map_name):
        try:
            obj = self.get_my_details().get(map_name=map_name)
            seg_name, seg_descriptor = obj.map_segment, obj.map_descriptor
        except:
            seg_name = ''
            seg_descriptor = ''
        return seg_name, seg_descriptor

    def get_map_name_based_on_map_segment(self, map_segment):
        try:
            map_name = self.get_my_details().get(map_segment=map_segment, map_descriptor=self).map_name
        except:
            map_name = ''
        return map_name

    def get_my_details_count(self):
        return self.get_my_details().count()

    def get_my_current_status(self):
        if self.status:
            return self.get_status_display()
        return ''

    def is_complete(self):
        return self.status == EDI_MAPPING_STATUS_COMPLETE

    def create_destination_file(self, edi_fh):

        show_header = self.show_header
        delimiter = self.delimiter
        ext = 'txt' if self.output_format == 'text' else 'csv'

        # get map names (Header row)
        map_names_list = self.get_map_names_list()

        # Get Segments List (from file content)
        source_segments_list = edi_fh.get_segment_list()

        # derive loops structure (ml, nl)
        loops_distribution = []
        current_ml = None
        on_loop = False
        for pos, item in enumerate(source_segments_list):

            if item['id'] == self.main_loop_segment:
                on_loop = True
                current_ml = {
                    'ml_id': item['id'],
                    'ml_pos': pos,
                    'nl_id': '',
                    'nl_pos': '',
                    'el_id': '',
                    'el_pos': '',
                    'ml_included_segments': [],
                    'data': [],
                }

            elif item['id'] == self.nested_loop_segment:
                if not current_ml['nl_id']:
                    current_ml['nl_id'] = item['id']
                    current_ml['nl_pos'] = pos
                    loops_distribution.append(current_ml)
                else:
                    clone_current_ml = {
                        'ml_id': current_ml['ml_id'],
                        'ml_pos': current_ml['ml_pos'],
                        'nl_id': item['id'],
                        'nl_pos': pos,
                        'el_id': '',
                        'el_pos': '',
                        'ml_included_segments': current_ml['ml_included_segments'],
                        'data': [],
                    }
                    loops_distribution.append(clone_current_ml)

            elif item['id'] == self.end_loop_segment:
                for l in loops_distribution:
                    if not l['el_id']:
                        l['el_id'] = item['id']
                        l['el_pos'] = pos

            else:
                if on_loop and item['id'].startswith('N'):  # analyze later if is the same for other doctypes
                    if loops_distribution and not loops_distribution[-1]['ml_included_segments']:
                        loops_distribution[-1]['ml_included_segments'].append({
                            'id': item['id'],
                            'pos': pos
                        })
                    else:
                        current_ml['ml_included_segments'].append({
                            'id': item['id'],
                            'pos': pos
                        })
        # header row
        header_data = f"{delimiter}".join(x for x in map_names_list)

        common_list = []
        on_loop = False
        for detail in self.get_my_details():

            # get s_name and descriptor based on map_name
            s_name, s_descriptor = self.get_segment_name_and_descriptor_based_on_map_name(detail.map_name)

            # get s_id and index based on seg_name
            s_id, s_index = strip_segment_name_which_contains_digits(s_name)

            # Exclude loops for now (get mapped value)
            if not on_loop and s_id != self.main_loop_segment and s_id != self.nested_loop_segment and s_id != self.end_loop_segment:
                if s_descriptor:
                    value = [e['elements'][s_index - 1]['value'] for e in source_segments_list if e['id'] == s_id and e['elements'][0]['value'] == s_descriptor][0]
                else:
                    value = [e['elements'][s_index - 1]['value'] for e in source_segments_list if e['id'] == s_id][0]
                common_list.append(value)

            # LOOPS
            else:
                if s_id == self.main_loop_segment:
                    on_loop = True
                    for item in loops_distribution:
                        item['data'].append(source_segments_list[item['ml_pos']]['elements'][s_index - 1]['value'])

                elif s_id == self.nested_loop_segment:
                    for item in loops_distribution:
                        item['data'].append(source_segments_list[item['nl_pos']]['elements'][s_index - 1]['value'])

                elif s_id == self.end_loop_segment:
                    for item in loops_distribution:
                        item['data'].append(source_segments_list[item['el_pos']]['elements'][s_index - 1]['value'])

                else:
                    for item in loops_distribution:
                        included_segment = next((x for x in item['ml_included_segments'] if x['id'] == s_id), None)
                        if included_segment:
                            item['data'].append(source_segments_list[included_segment['pos']]['elements'][s_index - 1]['value'])

        lines_data = ''
        for elem in loops_distribution:
            lines_data += "\n" + f"{delimiter}".join(common_list + elem['data'])

        # Create a file and write content
        result_filename = f"{edi_fh.filename.split('.')[0]}_(MAP).{ext}"
        result_file = os.path.join(MEDIA_ROOT, result_filename)
        with open(result_file, 'w+') as file:
            if show_header:
                # header
                file.write(header_data)
                file.write(lines_data)

        return result_file, result_filename


class EDIMappingTemplateDetail(BaseModel):
    emt = models.ForeignKey(EDIMappingTemplate, on_delete=models.CASCADE)
    map_name = models.CharField(max_length=50)
    map_segment = models.CharField(max_length=50)
    map_descriptor = models.CharField(max_length=50, default='')
    fw_row = models.CharField(max_length=50, blank=True, null=True)
    fw_char = models.CharField(max_length=50, blank=True, null=True)
    fw_length = models.CharField(max_length=50, blank=True, null=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.map_name} - {self.map_segment} ({self.emt})"

    class Meta:
        verbose_name = 'EDI Mapping Template - Detail'
        verbose_name_plural = 'EDI Mappings Templates - Details'
        db_table = "edi_mapping_templates_details"
        ordering = ('-created_at', )
        unique_together = ('emt', 'map_name', 'map_segment')


# TODO: Ticket 741 -> Analyze to remove models in the next release
class QuickbooksTransactions(BaseModel):
    status = models.IntegerField(choices=ACCOUNTING_TRANSACTION_STATUSES, default=ACCOUNTING_TRANSACTION_STATUS_PENDING)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)                                      # Company
    cbid = models.IntegerField(blank=True, null=True)                                                   # CB Numeric ID
    cb_number = models.CharField(max_length=20, blank=True, null=True)                                  # CB Number
    cb_amount_issue = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)       # TotClaimIssue
    customer_accno = models.CharField(max_length=50, blank=True, null=True)                             # Account Number
    post_date = models.DateField(blank=True, null=True)                                                 # Post Date
    items = JSONField(blank=True, null=True)                                # item_accno, item_qty, item_amount_issue
    # CM fields as crossed reference with CB CM updates
    cb_cm_number = models.CharField(max_length=20, blank=True, null=True)
    cb_cm_date = models.DateField(blank=True, null=True)
    cb_cm_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.cbid} ({self.post_date}) [{self.get_status_display()}]"

    class Meta:
        verbose_name = 'Quickbooks - Transaction'
        verbose_name_plural = 'Quickbooks - Transactions'
        db_table = "quickbooks_transactions"
        ordering = ('status', 'company', 'cbid')


class QuickbooksErrors(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)                                      # Company
    cbid = models.IntegerField(blank=True, null=True)                                                   # CB Numeric ID
    error = models.CharField(max_length=300, blank=True, null=True)                                     # error

    def __str__(self):
        return f"{self.cbid} (Error: {self.error})"

    class Meta:
        verbose_name = 'Quickbooks - Error'
        verbose_name_plural = 'Quickbooks - Errors'
        db_table = "quickbooks_errors"
        ordering = ('company', 'cbid')
