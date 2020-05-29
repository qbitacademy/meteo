import os
import csv
import smbus2
import bme280
import influxdb
import datetime
import time
import struct
import aqi
from gpiozero import MCP3008
from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE

db_client = influxdb.InfluxDBClient(host='127.0.0.1', port=8086)
db_client.switch_database('meteo')

def get_particle_measure():
    port = "/dev/ttyS0" # Set this to your serial port.
    baudrate = 9600

    # Prepare serial connection.
    ser = Serial(port, baudrate=baudrate, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE)
    ser.flushInput()
    HEADER_BYTE = b"\xAA"
    COMMANDER_BYTE = b"\xC0"
    TAIL_BYTE = b"\xAB"
    byte, previousbyte = b"\x00", b"\x00"
    for i in range(10):
        previousbyte = byte
        byte = ser.read(size=1)
        # We got a valid packet header.
        if previousbyte == HEADER_BYTE and byte == COMMANDER_BYTE:
            packet = ser.read(size=8) # Read 8 more bytes
            # Decode the packet - little endian, 2 shorts for pm2.5 and pm10, 2 ID bytes, checksum.
            readings = struct.unpack('<HHcccc', packet)
        
            # Measurements.
            pm_25 = readings[0]/10.0
            pm_10 = readings[1]/10.0

            # ID
            id = packet[4:6]
            # Prepare checksums.
            checksum = readings[4][0]
            calculated_checksum = sum(packet[:6]) & 0xFF
            checksum_verified = (calculated_checksum == checksum)
                
            # Message tail.
            tail = readings[5]
        
            if tail == TAIL_BYTE and checksum_verified:
                aqi_2_5 = aqi.to_iaqi(aqi.POLLUTANT_PM25, str(pm_25))
                aqi_10 = aqi.to_iaqi(aqi.POLLUTANT_PM10, str(pm_10))
                return [(pm_25, aqi_2_5), (pm_10, aqi_10)]
    return [(None, None), (None, None)]

# temperature, pressure and humidity
port = 1
address = 0x76
bus = smbus2.SMBus(port)
calibration_params = bme280.load_calibration_params(bus, address)
d = bme280.sample(bus, address, calibration_params)

# wind direction
volts = {
    0.84: 112.5,
    1.02: 67.5,
    1.10: 90.0,
    1.36: 157.5,
    1.73: 135.0,
    2.02: 202.5,
    2.18: 180.0,
    2.53: 22.5,
    2.65: 45.0,
    2.89: 247.5,
    2.93: 225.0,
    3.02: 337.5,
    3.11: 0.0,
    3.15: 292.5,
    3.20: 315.0,
    3.25: 270.0,
}
adc_0 = MCP3008(channel=0)
wind = round(adc_0.value*3.3, 2)
if wind < 0.7 and wind >= 3.3:
    wind_dir = None
else:
    wind_dir = volts.get(wind) or volts[min(volts.keys(), key=lambda k: abs(k-wind))]

adc_1 = MCP3008(channel=1)
uv = adc_1.value*3.3

(pm25, aqi25), (pm10, aqi10) = get_particle_measure()

date = datetime.datetime.utcnow()
json_body = {
    "measurement": "sensores",
    "time": date.strftime('%Y-%m-%d %H:%M:%SZ'),
    "fields": {
        'humedad': d.humidity,
        'temperatura': d.temperature,
        'presion': d.pressure,
        'viento_dir': wind_dir,
        'uv': uv,
        'pm25': pm25,
        # 'aqi25': aqi25,
        'pm10': pm10,
        # 'aqi10': aqi10
    }
}
print(json_body)
db_client.write_points([json_body])

