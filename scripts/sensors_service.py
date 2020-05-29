import datetime
from gpiozero import Button
import time
import math
import influxdb

db_client = influxdb.InfluxDBClient(host='127.0.0.1', port=8086)
db_client.switch_database('meteo')

wind_count = 0     # Counts how many half-rotations
radius_cm = 9.0    # Radius of your anemometer
wait_interval = 60 # How often (secs) to report speed

wind_count = 0
rain_count = 0

def spin():
    global wind_count
    wind_count += 1

def bucket_tipped():
    global rain_count
    rain_count += 1

wind_speed_sensor = Button(5)
wind_speed_sensor.when_pressed = spin
rain_sensor = Button(6)
rain_sensor.when_pressed = bucket_tipped
BUCKET_SIZE = 0.47397


# Calculate the wind speed
def calculate_speed(time_sec):
    global wind_count

    CM_IN_A_KM= 100000.0
    SECS_IN_A_HOUR = 3600.0
    ADJUSTMENT = 1.18

    circumference_cm = (2 * math.pi) * radius_cm
    rotations = wind_count / 2.0

    # Calculate distance travelled by a cup in cm
    dist_cm = circumference_cm * rotations 
    dist_km = circumference_cm * rotations / CM_IN_A_KM

    km_per_sec = dist_km / time_sec
    km_per_hour = km_per_sec * SECS_IN_A_HOUR

    return km_per_hour * ADJUSTMENT


while True:
    time.sleep(wait_interval)
    value = calculate_speed(wait_interval)
    date = datetime.datetime.utcnow()
    json_body = {
        "measurement": "sensores",
        "time": date.strftime('%Y-%m-%d %H:%M:%SZ'),
        "fields": {
            'viento_vel': value,
            'lluvia': rain_count * BUCKET_SIZE
        }
    }
    wind_count = 0
    rain_count = 0
    db_client.write_points([json_body])

