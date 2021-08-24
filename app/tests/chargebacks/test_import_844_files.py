from django.test import TestCase

from app.chargebacks.cb_import_844 import import_data_into_844_table
from app.management.utilities.functions import create_client_dir

from empowerb.routers.mixins import MultiDBMixin

from erms.models import Import844, ChargeBack, ChargeBackLine
from ermm.models import Company, Account

from django.contrib.auth.models import User
from django.conf import settings


class Import844Test(MultiDBMixin, TestCase):

    """
    TEST BASE LINE:
    Company use to test has no data and it just related to the Import and their DBs
    """

    @classmethod
    def setUpTestData(cls):
        cls.user, _ = User.objects.get_or_create(username='john', email='lennon@thebeatles.com')
        cls.user.set_password('123')
        cls.user.save()

        cls.import844, _ = Import844.objects.get_or_create(header={'k': 2}, line={'k': 10}, file_name='pp.txt')

        # Creating and account and relating to the user
        cls.account, _ = Account.objects.get_or_create(owner=cls.user, name='andres')

        # Creating test company
        cls.company, _ = Company.objects.get_or_create(account=cls.account, name='andres_company', database='qa')

        # Create company directory
        create_client_dir(str(cls.company.id))
        cls.root_client = f"{settings.CLIENTS_DIRECTORY}/{str(cls.company.id)}/{settings.DIR_NAME_844_ERM_INTAKE}"

        # sample file information string
        sample_one_field_each_missing_str = """H_DocType|H_ControlNo|H_AcctNo|H_CBType|H_CBDate|H_CBNumber|H_ResubNo|H_ResubDesc|H_SuppName|H_SuppIDType|H_SuppID|H_DistName|H_DistIDType|H_DistID|H_SubClaimAmt|H_TotalCONCount|L_ContractNo|L_ContractStatus|L_ShipToIDType|L_ShipToID|L_ShipToName|L_ShipToAddress|L_ShipToCity|L_ShipToState|L_ShipToZipCode|L_ShipToHIN|L_InvoiceNo|L_InvoiceDate|L_InvoiceLineNo|L_InvoiceNote|L_ItemNDCNo|L_ItemUPCNo|L_ItemQty|L_ItemUOM|L_ItemWAC|L_ItemContractPrice|L_ItemCreditAmt|L_ShipTo340BID|L_ShipToGLN
        |2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844||QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497||00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000||8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00||TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT|||||079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11||ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH|||26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056||3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26||QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3||VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1||21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA||6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11||ST JOHN'S PHARMACY Z|2980 KENNEDY BLVD|JERSEY CITY|NJ|07306||1000001|8/6/2018|L1>3743211138000421||11111222243||1|EA|20|16|4||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11||VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962||669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA||CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE||NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013|||8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001||L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303|||EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1||100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA||80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100||20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|||
        844|2497|QAABC000|00|2018/8/7|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|7/8/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||"""
        sample_cb_line_missing_one_each_field_str = """H_DocType|H_ControlNo|H_AcctNo|H_CBType|H_CBDate|H_CBNumber|H_ResubNo|H_ResubDesc|H_SuppName|H_SuppIDType|H_SuppID|H_DistName|H_DistIDType|H_DistID|H_SubClaimAmt|H_TotalCONCount|L_ContractNo|L_ContractStatus|L_ShipToIDType|L_ShipToID|L_ShipToName|L_ShipToAddress|L_ShipToCity|L_ShipToState|L_ShipToZipCode|L_ShipToHIN|L_InvoiceNo|L_InvoiceDate|L_InvoiceLineNo|L_InvoiceNote|L_ItemNDCNo|L_ItemUPCNo|L_ItemQty|L_ItemUOM|L_ItemWAC|L_ItemContractPrice|L_ItemCreditAmt|L_ShipTo340BID|L_ShipToGLN
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21||MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1||271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN||SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012||MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD||01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104|||8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001||L1>3743137392000250||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|||11111222203||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||||1|EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203|||EA|10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1||10|8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA||8|2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10||2||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|||
        844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
                """
        sample_cb_missing_one_each_field_str = """H_DocType|H_ControlNo|H_AcctNo|H_CBType|H_CBDate|H_CBNumber|H_ResubNo|H_ResubDesc|H_SuppName|H_SuppIDType|H_SuppID|H_DistName|H_DistIDType|H_DistID|H_SubClaimAmt|H_TotalCONCount|L_ContractNo|L_ContractStatus|L_ShipToIDType|L_ShipToID|L_ShipToName|L_ShipToAddress|L_ShipToCity|L_ShipToState|L_ShipToZipCode|L_ShipToHIN|L_InvoiceNo|L_InvoiceDate|L_InvoiceLineNo|L_InvoiceNote|L_ItemNDCNo|L_ItemUPCNo|L_ItemQty|L_ItemUOM|L_ItemWAC|L_ItemContractPrice|L_ItemCreditAmt|L_ShipTo340BID|L_ShipToGLN
|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
844||QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|AS2106537|ST JOHN'S PHARMACY Z|2980 KENNEDY BLVD|JERSEY CITY|NJ|07306||1000001|8/6/2018|L1>3743211138000421||11111222243||1|EA|20|16|4||
844|2497||00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000||8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00||TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT|||||079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11||ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH|||26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056||3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26||QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3||VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1||11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA||BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11||VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
844|2497|QAABC000|00|8/7/2018|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
"""
        sample_cb_date_format_yyy_mm_dd_str = """H_DocType|H_ControlNo|H_AcctNo|H_CBType|H_CBDate|H_CBNumber|H_ResubNo|H_ResubDesc|H_SuppName|H_SuppIDType|H_SuppID|H_DistName|H_DistIDType|H_DistID|H_SubClaimAmt|H_TotalCONCount|L_ContractNo|L_ContractStatus|L_ShipToIDType|L_ShipToID|L_ShipToName|L_ShipToAddress|L_ShipToCity|L_ShipToState|L_ShipToZipCode|L_ShipToHIN|L_InvoiceNo|L_InvoiceDate|L_InvoiceLineNo|L_InvoiceNote|L_ItemNDCNo|L_ItemUPCNo|L_ItemQty|L_ItemUOM|L_ItemWAC|L_ItemContractPrice|L_ItemCreditAmt|L_ShipTo340BID|L_ShipToGLN
844|2497|QAABC000|00|2018/8/7|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|21|6BJ0TRKF1|MERCY HOSP INC. 340B MAIN|271 CAREW ST P.O. BOX 9012|SPRINGFIELD|MA|01104||1000001|8/6/2018|L1>3743137392000250||11111222203||1|EA|10|8|2||
844|2497|QAABC000|00|2018/8/7|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|AS2106537|ST JOHN'S PHARMACY Z|2980 KENNEDY BLVD|JERSEY CITY|NJ|07306||1000001|8/6/2018|L1>3743211138000421||11111222243||1|EA|20|16|4||
844|2497|QAABC000|00|2018/8/7|TESTCORRECT||||11|079200795|ABC DC NEWBURGH||RA0522056|26|3|QACVS1|VA|11|BV3368962|VAN HOUTEN PHARMACYZ     CPA|669 VAN HOUTEN AVENUE|CLIFTON|NJ|07013||1000001|8/6/2018|L1>3743221002000260||11111223303||1|EA|100|80|20||
"""
        sample_strings = [
            {
                'name': 'sample_one_field_each_missing_str.txt',
                'text': sample_one_field_each_missing_str,
                'location': f"{cls.root_client}/sample_one_field_each_missing_str.txt"
            },
            {
                'name': 'sample_cb_missing_one_each_field_str.txt',
                'text': sample_cb_missing_one_each_field_str,
                'location': f"{cls.root_client}/sample_cb_missing_one_each_field_str.txt"
            },
            {
                'name': 'sample_cb_line_missing_one_each_field_str.txt',
                'text': sample_cb_line_missing_one_each_field_str,
                'location': f"{cls.root_client}/sample_cb_line_missing_one_each_field_str.txt"
            },
            {
                'name': 'sample_cb_date_format_yyy_mm_dd_str.txt',
                'text': sample_cb_date_format_yyy_mm_dd_str,
                'location': f"{cls.root_client}/sample_cb_date_format_yyy_mm_dd_str.txt"
            },
        ]
        for sample_string in sample_strings:
            sample_file = open(sample_string['location'], 'w')
            sample_file.write(sample_string['text'])
            sample_file.close()

        cls.sample_file_list = sample_strings

    def test_user_is_instance(self):
        """
        Checks we create a valid user for the company
        :return: None
        """
        self.assertIsInstance(self.user, User)

    def test_import_844_header(self):
        """
        Checks import844 objects is create properly and headers is add.
        :return: None
        """
        self.assertIsNotNone(self.import844.header)

    def test_company_is_instance(self):
        """
        Checks if Company object is created
        :return: None
        """
        self.assertIsInstance(self.company, Company)

    def test_import_data_into_844_table_each_field_missing_function(self):
        """
        Using file create in the setUpTestData see if import_data_into_844_table adds the imports to the DB missing any field
        :return: None
        """
        file_dir = self.sample_file_list[0]
        import_data_into_844_table(file_dir['location'], file_dir['name'])
        test_import844 = Import844.objects.first()
        self.assertIsInstance(test_import844, Import844)

    def test_import_data_into_844_table_cb_missing_one_each_field(self):
        """
        Using file create in the setUpTestData see if import_data_into_844_table adds the imports to the DB missing any
        Charge Back field
        :return: None
        """
        file_dir = self.sample_file_list[1]
        import_data_into_844_table(file_dir['location'], file_dir['name'])
        test_import844 = Import844.objects.first()
        self.assertIsInstance(test_import844, Import844)

    def test_import_data_into_844_table_cb_line_missing_one_each_field(self):
        """
        Using file create in the setUpTestData see if import_data_into_844_table adds the imports to the DB missing any
        Charge Line Back field
        :return: None
        """
        file_dir = self.sample_file_list[2]
        import_data_into_844_table(file_dir['location'], file_dir['name'])
        test_import844 = Import844.objects.first()
        self.assertIsInstance(test_import844, Import844)

    def test_import_data_into_844_table_date_format_yy_mm_dd(self):
        """
        Using file create in the setUpTestData see if import_data_into_844_table adds the imports to the DB missing any
        Charge Line Back field
        :return: None
        """
        file_dir = self.sample_file_list[3]
        import_data_into_844_table(file_dir['location'], file_dir['name'])
        test_import844 = Import844.objects.first()
        self.assertIsInstance(test_import844, Import844)
