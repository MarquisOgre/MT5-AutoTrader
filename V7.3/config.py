import os
from dotenv import load_dotenv
load_dotenv()

LOGIN_RAW=os.getenv("MT5_LOGIN","").strip()
LOGIN=int(LOGIN_RAW) if LOGIN_RAW.isdigit() else None
PASSWORD=os.getenv("MT5_PASSWORD","").strip() or None
SERVER=os.getenv("MT5_SERVER","").strip() or None
TIMEFRAME=os.getenv("TIMEFRAME","M15").upper()
BARS=int(os.getenv("BARS","10000"))
