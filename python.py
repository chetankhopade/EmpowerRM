python3 -m venv virtualENV
source virtualENV/bin/activate
pip3 install -r requirements.txt
python manage.py erm_migrate
python manage.py migrate
python manage.py test
