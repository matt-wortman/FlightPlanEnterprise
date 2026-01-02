import os
import logging

# Try to import dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Set up basic logging
logging.basicConfig(level=logging.WARNING)

# Only load .env.local if running locally and dotenv is available
flightplan_env = os.environ.get('FLIGHTPLAN_ENV', 'local')
if flightplan_env == 'local' and load_dotenv:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))
else:
    if flightplan_env == 'local' and not load_dotenv:
        logging.warning("python-dotenv is not installed; .env.local will not be loaded.")

appName = 'Flight Plan'
appVersion = 'v3.3.0'
postVersion = '.4'

encryption_key = os.environ.get('ENCRYPTION_KEY')
chatbot_url = os.environ.get('CHATBOT_URL') 


databaseConnect = { 
  'Interface': 'SQLSERVER',
  'Server': os.environ.get('DB_SERVER'),
  'Database': os.environ.get('DB_NAME'),
  'User': os.environ.get('DB_USER'),
  'Password':  os.environ.get('DB_PASSWORD'),
}

sqlDatabaseConnectLocal = { 
  'Interface': 'SQLSERVER',
  'Server': os.environ.get('DB_SERVER'),
  'Database': os.environ.get('DB_NAME'),
  'User': os.environ.get('DB_USER'),
  'Password': os.environ.get('DB_PASSWORD'),
} 



blobStorageConnectCCH = { 'Connect': os.environ.get('BLOB_STORAGE_CONNECT'),
                          'Container': os.environ.get('CONTAINER_NAME', 'devreports')
                        }

sqlDatabaseConnect = databaseConnect  
blobStorageConnect = blobStorageConnectCCH

patients_per_page = int(os.environ.get('PATIENTS_PER_PAGE', 20))

# Import local admin override env vars only if running locally
if flightplan_env == 'local':
    fp_local_user = os.environ.get('FP_LOCAL_USER')
    fp_local_creds = os.environ.get('FP_LOCAL_CREDS')
    fp_local_occupation = os.environ.get('FP_LOCAL_OCCUPATION')
else:
    fp_local_user = None
    fp_local_creds = None
    fp_local_occupation = None