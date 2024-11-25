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
    
    if sender.uuid.lower() == TEMPERATURE_UUID.lower():
        # Convert temperature data (2 bytes)
        # Read the temperature data
        integer_part = int.from_bytes(data[0:1], byteorder="little", signed=True)  # First byte as int8_t
        decimal_part = int.from_bytes(data[1:2], byteorder="little")  # Second byte as uint8_t
        
        temperature = integer_part + (decimal_part / 100.0)  # Combine integer and decimal parts
        logging.info(f"Temperature: {temperature:.2f} °C")

    elif sender.uuid.lower() == HUMIDITY_UUID.lower():
        # Convert humidity data (1 byte, integer percentage)
        humidity = int.from_bytes(data, byteorder="little")
        logging.info(f"Humidity: {humidity}%")

    elif sender.uuid.lower() == AIR_QUALITY_UUID.lower():
        # Convert air quality data (4 byte)
        air_eCO2 = int.from_bytes(data[0:2], byteorder="little")  # First 2 bytes for eCO2
        air_TVOC = int.from_bytes(data[2:4], byteorder="little")  # Next 2 bytes for TVOC
        
        logging.info(f"eCO2: {air_eCO2} ppm, TVOC: {air_TVOC} ppb")

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
    data = bytearray([
        0x20, 0x4E,  # Temperature interval (20s)
        0x60, 0xEA,  # Pressure interval (60s)
        0x20, 0x4E,  # Humidity interval (20s)
        0x60, 0xEA,  # Color interval (60s)
        0x02,        # Gas mode (10s)
        0x00, 0x00, 0x00  # Color LED min intensity (Red, Green, Blue)
    ])
    await client.write_gatt_char(CONFIG_UUID, data)
    logging.info("Set environment configuration")
    # Optional: Verify by reading the characteristic value back
    # response = await client.read_gatt_char(CONFIG_UUID)

async def set_connection_params(client: BleakClient):
    #SET CONNECTION PARAMETERS
    # uint16_t - Minimum connection interval in 1.25 ms units.
        # min 6 -> 7.5 ms
        # max 3200 -> 4 s
    # uint16_t - Maximum connection interval in 1.25 ms units.
        # min 6 -> 7.5 ms
        # max 3200 -> 4 s
    # uint16_t - Slave latency in number of connection events (0-499 events).
    # uint16_t - Supervision timeout in 10 ms units.
        # min 10 -> 100 ms
        # max 3200 -> 32 s
    # The following constraint applies: 
        # conn_sup_timeout * 4 > (1 + slave_latency) * max_conn_interval 
        # that corresponds to the following Bluetooth Spec requirement: 
        # The Supervision_Timeout in milliseconds must be larger than (1 + Conn_Latency) * Conn_Interval_Max * 2, 
        # where Conn_Interval_Max is given in milliseconds.
    data = bytearray([
        0x06, 0x00,  # Minimum connection interval (6 units = 7.5ms)
        0x80, 0x0C,  # Maximum connection interval (3200 units = 4s)
        0x00, 0x00,  # Slave latency (0)
        0x80, 0x0C   # Supervision timeout (32 s)
    ])
    await client.write_gatt_char(CONN_PARAM_UUID, data)
    logging.info("Set connection parameters")

async def main():
    try:
        logging.info("start")
        async with BleakClient(THINGY_MAC_ADDRESS) as client:
            logging.info("Connecting to Nordic Thingy:52")
            await asyncio.sleep(4)
            # Check if the client is connected
            if client.is_connected:
                logging.info("Connected to Nordic Thingy:52")

                await asyncio.sleep(4)
                await set_connection_params(client)
                await asyncio.sleep(4)
                await set_config(client)

                # Start receiving notifications
                await client.start_notify(TEMPERATURE_UUID, notification_handler)
                await client.start_notify(HUMIDITY_UUID, notification_handler)
                await client.start_notify(AIR_QUALITY_UUID, notification_handler)
            else:
                logging.error(f"Failed to connect to {THINGY_MAC_ADDRESS}")
    except Exception as e:
        logging.error(f"Error: {e}")

# Run the main function
asyncio.run(main())
