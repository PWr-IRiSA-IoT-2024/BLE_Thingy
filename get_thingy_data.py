import os
import sys
import asyncio
import logging
from bleak import BleakClient, BleakGATTCharacteristic
from dotenv import load_dotenv
from utils.convert_data import convert_data
from utils.connect_with_db import write_data_to_db
from utils.enums import MEASURMENT_TYPES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load env before loading module
load_dotenv()

required_vars = ["THINGY_MAC_ADDRESS"]

for var in required_vars:
    if not os.getenv(var):
        sys.exit(f"Error: Environment variable {var} is not set.")
      
THINGY_MAC_ADDRESS = os.getenv("THINGY_MAC_ADDRESS")

# UUIDs for the sensors
# see https://nordicsemiconductor.github.io/Nordic-Thingy52-FW/documentation/firmware_architecture.html
TEMPERATURE_UUID = "EF680201-9B35-4933-9B10-52FFA9740042"
HUMIDITY_UUID = "EF680203-9B35-4933-9B10-52FFA9740042"
AIR_QUALITY_UUID = "EF680204-9B35-4933-9B10-52FFA9740042"
CONFIG_UUID = "EF680206-9B35-4933-9B10-52FFA9740042"
CONN_PARAM_UUID = "EF680104-9B35-4933-9B10-52FFA9740042"


# Notification handler to process incoming data
def notification_handler(sender: BleakGATTCharacteristic, data: bytearray):
    logging.info(f"{sender.description} data: {list(data)}")

    if sender.uuid.lower() == AIR_QUALITY_UUID.lower():
        # Convert air quality data (4 byte)
        air_eCO2 = int.from_bytes(data[0:2], byteorder="little")  # First 2 bytes for eCO2
        air_TVOC = int.from_bytes(data[2:4], byteorder="little")  # Next 2 bytes for TVOC
        
        logging.info(f"eCO2: {air_eCO2} ppm, TVOC: {air_TVOC} ppb")
        write_data_to_db(convert_data(air_eCO2, MEASURMENT_TYPES[0]))
        write_data_to_db(convert_data(air_TVOC, MEASURMENT_TYPES[1]))
        
    elif sender.uuid.lower() == TEMPERATURE_UUID.lower():
        # Convert temperature data (2 bytes)
        # Read the temperature data
        integer_part = int.from_bytes(data[0:1], byteorder="little", signed=True)  # First byte as int8_t
        decimal_part = int.from_bytes(data[1:2], byteorder="little")  # Second byte as uint8_t
        
        temperature = integer_part + (decimal_part / 100.0)  # Combine integer and decimal parts
        logging.info(f"Temperature: {temperature:.2f} °C")
        write_data_to_db(convert_data(temperature, MEASURMENT_TYPES[2]))

    elif sender.uuid.lower() == HUMIDITY_UUID.lower():
        # Convert humidity data (1 byte, integer percentage)
        humidity = int.from_bytes(data, byteorder="little")
        logging.info(f"Humidity: {humidity}%")
        write_data_to_db(convert_data(humidity, MEASURMENT_TYPES[3]))


async def set_config(client: BleakClient):

    #SET CONFIGURATION
    # uint16_t - Temperature interval in ms (100 ms - 60 s).
    # uint16_t - Pressure interval in ms (50 ms - 60 s).
    # uint16_t - Humidity interval in ms (100 ms - 60 s).
    # uint16_t - Color interval in ms (200 ms - 60 s).
    # uint8_t - Gas mode
        # 1 = 1 s interval
        # 2 = 10 s interval
        # 3 = 60 s interval
    # Color sensor LED calibration:
    # uint8_t - Red intensity [0 - 255]
    # uint8_t - Green intensity [0 - 255]
    # uint8_t - Blue intensity [0 - 255]
    try:
        async with BleakClient(THINGY_MAC_ADDRESS) as client:
            if client.is_connected:
                data = bytearray([
                    0xE8, 0x03,  # Temperature interval (1000ms = 1s)
                    0x60, 0xEA,  # Pressure interval (60s)
                    0xE8, 0x03,  # Humidity interval (1s)
                    0x60, 0xEA,  # Color interval (60s)
                    0x01,        # Gas mode (1s)
                    0x00, 0x00, 0x00  # Color LED min intensity (Red, Green, Blue)
                ])
                await client.write_gatt_char(CONFIG_UUID, data)
                logging.info("Set environment configuration")
                # Optional: Verify by reading the characteristic value back
                # response = await client.read_gatt_char(CONFIG_UUID)
            else:
                logging.error(f"Failed to connect to {THINGY_MAC_ADDRESS}")
    except Exception as e:
        logging.error(f"Error: {e}")

async def main_loop():
    try:
        async with BleakClient(THINGY_MAC_ADDRESS) as client:
            if client.is_connected:
                # Start receiving notifications
                await client.start_notify(TEMPERATURE_UUID, notification_handler)
                await client.start_notify(HUMIDITY_UUID, notification_handler)
                await client.start_notify(AIR_QUALITY_UUID, notification_handler)

                await asyncio.sleep(8)

                # Stop receiving notifications
                await client.stop_notify(TEMPERATURE_UUID)
                await client.stop_notify(HUMIDITY_UUID)
                await client.stop_notify(AIR_QUALITY_UUID)
            else:
                logging.error(f"Failed to connect to {THINGY_MAC_ADDRESS}")
    except Exception as e:
        logging.error(f"Error: {e}")

async def main():
    try:
        await set_config()

        while True:
            await main_loop()
            await asyncio.sleep(120)
    except Exception as e:
        logging.error(f"Error: {e}")

# Run the main function
asyncio.run(main())
