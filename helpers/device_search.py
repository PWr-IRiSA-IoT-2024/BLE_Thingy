import asyncio
from bleak import BleakScanner
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def scan_ble_devices():
    logging.info("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        logging.info(f"Device Name: {device.name}, MAC Address: {device.address}")

asyncio.run(scan_ble_devices())
