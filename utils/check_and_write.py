from enum import Enum
from connect_with_db import write_data_to_db
from send_led_warn import control_led

class SensorType(Enum):
    CO2 = "CO2"
    EVOC = "VOC"
    TEMPERATURE = "Temperature"
    HUMIDITY = "Humidity"