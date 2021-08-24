from decimal import Decimal

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response

from api.v1.permissions import IsAuthorized, IsValidToken
from api.v1.quickbooks.filters import QuickbooksConfigurationsFilterBackend
from api.v1.quickbooks.serializers import QuickbooksTransactionsSerializer, QuickbooksConfigurationsSerializer
from app.management.utilities.constants import (SUBSTAGE_TYPE_NO_ERRORS,
                                                ACCOUNTING_TRANSACTION_STATUS_RECEIVED,
                                                ACCOUNTING_TRANSACTION_STATUS_SENT, SUBSTAGE_TYPE_ERRORS)
from app.management.utilities.functions import convert_string_to_date
from ermm.models import Company, QuickbooksConfigurations
from erms.models import ChargeBack, AccountingTransaction, AccountingError


class QuickbooksConfigurationsViewSet(viewsets.ModelViewSet):

    queryset = QuickbooksConfigurations.objects.all()
    serializer_class = QuickbooksConfigurationsSerializer
    permission_classes = (IsValidToken, )
    filter_backends = (QuickbooksConfigurationsFilterBackend, )


class QuickbooksTransactionsViewSet(viewsets.GenericViewSet):

    serializer_class = QuickbooksTransactionsSerializer
    permission_classes = (IsValidToken, IsAuthorized)
    database = ''

    def get_queryset(self):
        self.database = Company.objects.get(id=self.request.data['company_id']).database
        queryset = AccountingTransaction.objects.using(self.database).exclude(status=ACCOUNTING_TRANSACTION_STATUS_RECEIVED)
        return queryset

    def list(self, request):
        try:
            queryset = self.get_queryset()
            with transaction.atomic(using=self.database):
                for qbcb in queryset:
                    # update status == sent
                    qbcb.status = ACCOUNTING_TRANSACTION_STATUS_SENT
                    qbcb.save(using=self.database)

                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

        except Exception as ex:
            print(ex.__str__())
            return Response({'message': 'error', 'detail': ex.__str__()}, status=status.HTTP_406_NOT_ACCEPTABLE)

    # POST
    def create(self, request, *args, **kwargs):
        database = Company.objects.get(id=request.data['company_id']).database
        try:
            with transaction.atomic(using=database):

                for item in request.data.get('transactions', []):
                    # get Accountintg Transaction object
                    acct_transaction = AccountingTransaction.objects.using(database).get(id=item['transaction_id'])
                    acct_transaction.status = ACCOUNTING_TRANSACTION_STATUS_RECEIVED
                    acct_transaction.save(using=database)

                    # get Chargeback from QBTransaction obj
                    chargeback = ChargeBack.objects.using(database).get(cbid=acct_transaction.cbid)

                    # error attr (valid or invalids transactions)
                    qb_error = item.get('error', '')

                    # Valid Transactions
                    if not qb_error:

                        # CM data
                        cm_number = item['cm_number']
                        cm_amount = Decimal(item['cm_amount'])
                        cm_date = convert_string_to_date(item['cm_date'])

                        # update Chargebacks CM fields, stage and substage
                        chargeback.accounting_credit_memo_number = cm_number
                        chargeback.accounting_credit_memo_amount = cm_amount
                        chargeback.accounting_credit_memo_date = cm_date
                        chargeback.substage = SUBSTAGE_TYPE_NO_ERRORS
                        chargeback.save(using=database)

                        # update QBTransaction status == received
                        acct_transaction.cb_cm_number = cm_number
                        acct_transaction.cb_cm_amount = cm_amount
                        acct_transaction.cb_cm_date = cm_date
                        acct_transaction.save(using=database)

                    # invalid Transactions
                    else:
                        # Change the substage to 1 (with Errors) for that CB
                        chargeback.substage = SUBSTAGE_TYPE_ERRORS
                        chargeback.save(using=database)

                        # Record the error in a table with a reference to the CBID
                        acct_error = AccountingError(accounting_transaction=acct_transaction,
                                                     cbid=chargeback.cbid,
                                                     error=qb_error)
                        acct_error.save(using=database)

                        # update acct transaction
                        acct_transaction.has_error = True
                        acct_transaction.save(using=database)

                return Response({'message': 'success'}, status=status.HTTP_200_OK)

        except Exception as ex:
            print(ex.__str__())
            return Response({'message': 'error', 'detail': ex.__str__()}, status=status.HTTP_406_NOT_ACCEPTABLE)
