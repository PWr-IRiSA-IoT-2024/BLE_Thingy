
import datetime
import os
import sys


required_vars = ["THINGY_MAC_ADDRESS"]

for var in required_vars:
    if not os.getenv(var):
        sys.exit(f"Error: Environment variable {var} is not set.")
      
THINGY_MAC_ADDRESS = os.getenv("THINGY_MAC_ADDRESS")

def convert_data(value, measurement):
    """
    Convert data from one format to another
    """
    measurement = measurement
    tags = {"device": "BLE_Thingy_" + THINGY_MAC_ADDRESS}
    time = f'{datetime.datetime.now().isoformat()}Z'
    fields = {"value": value}

    return measurement, tags, time, fields
    
    