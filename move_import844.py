import os
import sys
import django
import time

from django.db import transaction

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.split(BASE_DIR)[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'empowerb.settings'

# init django
django.setup()

from empowerb.settings import DATABASES
from erms.models import Import844, Import844History
from app.management.utilities.functions import move_import844_to_import844_history_table


if __name__ == '__main__':

    """
        Ticket: 854
        When looking at the detail for an archived CB, the detail errors out because of the change we made to move import_844 to import_844_history.  
        However, we are going to make a change to the import_844 flow first, then fix this issue.
        Change the import flow so that the import_844 data is moved to import_844_history table immediately upon creating the chargeback in the db.  
        Remove it from the Archive action.
        
        Based on these modifications we created this script to move existing import844 objects into import844history table
        this should runs once, because the system is updated now to move import844 rigth after the cbs are created as part of the import process validations
    """

    for db_name in [x for x in DATABASES.keys() if x != 'default']:
        try:
            with transaction.atomic():
                print(f"\n<<< Checking existing Import844 objects for: {db_name} >>>")
                time.sleep(0.5)
                existing_844_objects = Import844.objects.using(db_name).all()
                print(f"Got {existing_844_objects.count()} records")
                if existing_844_objects.exists():
                    for import844 in existing_844_objects.iterator():
                        print(f"Moving to history table import844_id: {import844.id}")
                        import844_history, _ = Import844History.objects.using(db_name).get_or_create(id=import844.id)
                        import844_history.header = import844.header
                        import844_history.line = import844.line
                        import844_history.file_name = import844.file_name
                        import844_history.save(using=db_name)
                        import844.delete(using=db_name)
                        print("Sucessfuly moved")
                else:
                    print("There are not any open Import844 obj for this company")

        except Exception as ex:
            print(ex.__str__())
