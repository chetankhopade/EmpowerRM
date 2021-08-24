# empower Backend

```bash
# clone the project
git clone https://mdhinsightinc.visualstudio.com/EmpowerRM%20SaaS/_git/EmpowerRM%20SaaS

# make virtual environment
virtualenv venv -p python3

# activate the environment
source venv/bin/activate

cd empowerb

# install dependencies
pip install -r requirements.txt

# login to mysql and create databases per company (ex. user=root, passw=root)
mysql -u root -p
root~~~~~~~~

# master database
create database default;  

# database per company  
create database company1;   
create database company2;
create database company3;

company_settings.py
'companyN': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'companyN',
    'USER': "<mysql_root_user>",
    'PASSWORD': "<mysql_root_password>",
    'PORT': '3306',
    'ATOMIC_REQUESTS': True
},
    
# run migrations
python manage.py makemigrations

# apply migrations per database (use our custom migrate command)
python manage.py erm_migrate

# create superuser
python manage.py createsuperuser

# run command to populate the master database 
python manage.py populate_db 

# Notes: master database will be populated with following data so far:
- USA's States
- USA's Cities
- Disputes
- Direct Customers
# Keep in mind this populate_db is only once (first time you create the db)

# run the server
python manage.py runserver

# django admin per company 
# http://localhost:8000/<COMPANY_NAME>/admin/
# only in the master db, to see users thru django admin:
# http://localhost:8000/default/admin/users/

```

##### Services (mapping and chargeback):
```
# we should have a crobjob on production to be running this daemon service all time)
# run this command
python manage.py service_844.py <CLIENTS_DIRECTORY_PATH>


```

##### Notes:
```
1) I added the settings.py file now for help but we will remove it
from github once all developers have their local environments working well.

2) I added the csv files for populate command but that dataset folder 
with the csv files inside will be removed as well from github in the future 
once we migrate in our local environments and/or on production.

