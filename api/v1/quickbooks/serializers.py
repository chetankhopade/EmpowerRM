from rest_framework import serializers

from ermm.models import Company, QuickbooksConfigurations
from erms.models import AccountingTransaction


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = ['id', 'name']


class QuickbooksConfigurationsSerializer(serializers.ModelSerializer):
    company = CompanySerializer()

    class Meta:
        model = QuickbooksConfigurations
        fields = ['company', 'token', 'path', 'interval']


class QuickbooksTransactionsSerializer(serializers.ModelSerializer):
    transaction_id = serializers.SerializerMethodField()
    status_id = serializers.SerializerMethodField()
    status_name = serializers.SerializerMethodField()

    class Meta:
        model = AccountingTransaction
        fields = ['transaction_id', 'cbid', 'cb_number', 'cb_amount_issue', 'customer_accno',
                  'post_date', 'items', 'status_id', 'status_name', 'integration_type']

    @staticmethod
    def get_transaction_id(obj):
        return obj.id

    @staticmethod
    def get_status_id(obj):
        return obj.status

    @staticmethod
    def get_status_name(obj):
        return obj.get_status_display()
