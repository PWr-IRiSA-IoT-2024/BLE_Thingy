import os
import sys
import asyncio
import logging
from bleak import BleakClient
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

required_vars = ["NORDIC_MAC_ADDRESS"]

for var in required_vars:
    if not os.getenv(var):
        sys.exit(f"Error: Environment variable {var} is not set.")
      
NORDIC_MAC_ADDRESS = os.getenv("NORDIC_MAC_ADDRESS")

# Replace with your characteristic UUID for LED control
LED_CONTROL_UUID = "ABCD1234-5678-5678-5678-1234567890AB"

# Command values to control LEDs
# These should match the protocol defined on your Nordic device
class LedCommand(Enum):
    LED1_ON = bytearray([0x01])  # Command to turn on LED 1
    LED2_ON = bytearray([0x02])  # Command to turn on LED 2
    LED3_ON = bytearray([0x03])  # Command to turn on LED 3
    LED4_ON = bytearray([0x04])  # Command to turn on LED 4
    LED1_OFF = bytearray([0x05])  # Command to turn off LED 1
    LED2_OFF = bytearray([0x06])  # Command to turn off LED 2
    LED3_OFF = bytearray([0x07])  # Command to turn off LED 3
    LED4_OFF = bytearray([0x08])  # Command to turn off LED 4
    ALL_OFF = bytearray([0x00])   # Command to turn off all LEDs

async def control_led(command: LedCommand):
    async with BleakClient(NORDIC_MAC_ADDRESS) as client:
        # Check if connected
        if client.is_connected:
            logging.info(f"Connected to {NORDIC_MAC_ADDRESS}")
            
            # Send command to LED control characteristic
            try:
                await client.write_gatt_char(LED_CONTROL_UUID, command.value)
                logging.info("Command sent successfully")
            except Exception as e:
                logging.error(f"Failed to send command: {e}")
        else:
            logging.error(f"Failed to connect to {NORDIC_MAC_ADDRESS}")

# Main function to send a command to light up LED 1
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    await control_led(LedCommand.ALL_OFF)
    # Send a command to turn on LED 1
    await control_led(LedCommand.LED1_ON)

    await asyncio.sleep(2)  # Wait for 5 seconds
    await control_led(LedCommand.LED2_ON)

# Run the script
asyncio.run(main())
