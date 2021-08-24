import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '<SEC_RET_KET>'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.admin',
    'django_mysql',
    'rest_framework',
    'debug_toolbar',
    'pympler',
    'app',
    'ermm',
    'erms',
    'cuser'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'empowerb.middleware.WhichDatabaseIsTOUseMIddleware',
    'cuser.middleware.CuserMiddleware'
]

ROOT_URLCONF = 'empowerb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'empowerb.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'erm_master',
        'USER': "chetan",
        'PASSWORD': "*NA}pJDc3?",
        'HOST': "localhost",
        'PORT': "3306",
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        }
    },
    'precisiondose': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'precisiondose',
        'USER': "chetan",
        'PASSWORD': "*NA}pJDc3?",
        'HOST': "localhost",
        'PORT': '3306',
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
  
        }
    },
}

DATABASE_ROUTERS = [
    'empowerb.routers.erms.ERMSRouter',
    'empowerb.routers.ermm.ERMMRouter',
    #'empowerb.routers.app.APPRouter'
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# STATIC FILES
STATIC_URL = '/static/'
#STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'), )
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
#STATIC_ROOT = ''

# MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# VARIABLES - SERVICE 844
CLIENTS_DIRECTORY = "".join(os.path.join('/', 'efs/chetantest/'))

CSV_DELIMITER = "|"

FILE_HEADER = 'H_DocType|H_ControlNo|H_AcctNo|H_CBType|H_CBDate|H_CBNumber|H_ResubNo|H_ResubDesc|' \
              'H_SuppName|H_SuppIDType|H_SuppID|H_DistName|H_DistIDType|H_DistID|H_SubClaimAmt|' \
              'H_TotalCONCount|L_ContractNo|L_ContractStatus|L_ShipToIDType|L_ShipToID|L_ShipToName|' \
              'L_ShipToAddress|L_ShipToCity|L_ShipToState|L_ShipToZipCode|L_ShipToHIN|L_InvoiceNo|' \
              'L_InvoiceDate|L_InvoiceLineNo|L_InvoiceNote|L_ItemNDCNo|L_ItemUPCNo|L_ItemQty|' \
              'L_ItemUOM|L_ItemWAC|L_ItemContractPrice|L_ItemCreditAmt|L_ShipTo340BID|L_ShipToGLN\n'


# EMAIL CONFIG
EMAIL_ACTIVE = True
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'support@empowerrm.com'
EMAIL_HOST_PASSWORD = 'Supp0rt@34!'
EMAIL_USE_TLS = True

# SESSION TIMEOUT
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True      # Expire the session when the user closes their b$
SESSION_COOKIE_AGE = 120 * 60                # 30 Minutes activity

# SESSIONS (USER ACTIVITY)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True              # Expire the session when the user closes t$
TIMEOUT_TO_CLOSE_USER_SESSION = 1800                # timeout (in seconds) to close inactivity $
TIMEOUT_TO_ALERT_USER_SESSION = 1500                # timeout (in seconds) to close inactivity $
DELTA_TO_CHECK_USER_SESSION = 60000                 # delta (in miliseconds) to check user sess$

# FOLDER SETTINGS
#844
DIR_NAME_844_ERM_INTAKE = '844_ERM_intake'
DIR_NAME_844_ERM_HISTORY = '844_ERM_history'
DIR_NAME_844_ERM_ERROR = '844_ERM_errors'
DIR_NAME_844_PROCESSED = '844_ERM_history'

# 849 FOLDERS
DIR_NAME_849_ERM_OUT = '849_ERM_out'
DIR_NAME_849_ERM_MANUAL = '849_manual'
DIR_NAME_FILES_STORAGE = 'file_storage'
DIR_NAME_USER_REPORTS = 'reports'
DIR_NAME_USER_REPORTS_SCHEDULE = 'report_schedules'
# we may need 849_history
DIR_NAME_849_ERM_HISTORY = '849_ERM_processed'

FOLDERS_STRUCTURE = {
    DIR_NAME_844_ERM_INTAKE:  "844s Waiting for Import",
    DIR_NAME_844_PROCESSED: "844s Received / Processed",
    DIR_NAME_844_ERM_ERROR:   "844s Unable to be processed",
    DIR_NAME_849_ERM_OUT:     "849s Waiting for Pickup",
    DIR_NAME_849_ERM_HISTORY: "849s History",
    DIR_NAME_FILES_STORAGE:   "User Uploads",
    DIR_NAME_849_ERM_MANUAL: "849 Excel Files",
    DIR_NAME_USER_REPORTS: "Reports",
    DIR_NAME_USER_REPORTS_SCHEDULE: 'Reports Schedule'
}

# ACCUMATICA APIs (endpoint url excluding base_url path)
ACCUMATICA_API_LOGIN = '/entity/auth/login'
ACCUMATICA_API_LOGOUT = '/entity/auth/logout'
ACCUMATICA_API_CUSTOMERS = '/entity/Default/17.200.001/Customer'
ACCUMATICA_API_ITEMS = '/entity/Default/17.200.001/NonStockItem'
ACCUMATICA_API_INVOICES = '/entity/Default/17.200.001/Invoice'

# EDI API URL
EDI_API_URL = "http://localhost:8025/api"
DELTA_TO_CHECK_API_STATUS = 30000                 # delta (in miliseconds) to check user session activity (each 1m)
EDI_API_TOKEN = "180E843A545143D384C24D1135D5D567"

# ZOHO Config
ZOHO_AUTH_BASE_URI = "https://accounts.zoho.com/oauth/v2"
ZOHO_CLIENT_ID = "1000.6OQSNX4G0DOFR9EGK8JW9S3FA5YQ1H"
ZOHO_CLIENT_SECRET = "df4fb57aa04c0048e0486113cac8cc0382948d067c"
ZOHO_SCOPE = "Desk.tickets.ALL,Desk.settings.ALL"
ZOHO_MDH_ORG_ID = '695040783'

#REDIS_HOST = 'localhost'
#REDIS_PORT = 6379
#REDIS_CELERY_DB = 0
#CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}'


# DEBUG TOOLBAR PANELS
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
    # 3rd party panel
    'debug_toolbar.panels.request_history.RequestHistoryPanel',
    'debug_toolbar.panels.template_profiler.TemplateProfilerPanel',
    'pympler.panels.MemoryPanel',
]

# stored requests size
DEBUG_TOOLBAR_CONFIG = {
    'RESULTS_STORE_SIZE': 100,
}

# DEBUG TOOLBAR IPs
INTERNAL_IPS = ['127.0.0.1', ]
#
# ERM REPORT API URL
ERM_REPORT_API_URL = "http://172.31.73.145:8004/api"
DELTA_TO_CHECK_API_STATUS = 30000
ERM_REPORT_API_TOKEN = "180E843A545143D384C24D1135D5D567"

IMPORT_SERVICE_URL = "http://172.31.0.255:8006"