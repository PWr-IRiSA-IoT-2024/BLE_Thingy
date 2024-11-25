import os
import sys
import asyncio
import logging
from bleak import BleakClient, BleakGATTCharacteristic
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load env before loading module
load_dotenv()

required_vars = ["THINGY_MAC_ADDRESS"]

for var in required_vars:
    if not os.getenv(var):
        sys.exit(f"Error: Environment variable {var} is not set.")
      
BLE_MAC_ADDRESS = os.getenv("THINGY_MAC_ADDRESS")

async def check_characteristics(client: BleakClient):
    services = await client.get_services()
    for service in services:
        logging.info(f"Service: {service.uuid}")
        for char in service.characteristics:
            logging.info(f"  Characteristic: {char.description}, {char.uuid}")
            logging.info(f"    Properties: {char.properties}")


async def main():
    try:
        async with BleakClient(BLE_MAC_ADDRESS) as client:
            # Check if the client is connected
            if client.is_connected:
                logging.info(f"Connected to {BLE_MAC_ADDRESS}")

                await check_characteristics(client)
            else:
                logging.error(f"Failed to connect to {BLE_MAC_ADDRESS}")
    except Exception as e:
        logging.error(f"Error: {e}")

# Run the main function
asyncio.run(main())