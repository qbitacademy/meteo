import influxdb
import pathlib
import json
import requests
from datetime import datetime, timedelta, timezone


stamp_file = pathlib.Path(__file__).parent.resolve() / '.rain_last_sent'
utc_now = datetime.utcnow()

try:
    last_sent = datetime.strptime(
        stamp_file.read_text().split()[0], '%Y-%m-%dT%H:%M:%SZ'
    )
    last_value = float(stamp_file.read_text().split()[1])
except Exception:
    last_sent = utc_now - timedelta(minutes=10)
    last_value = 0.0

diff = int((utc_now - timedelta(minutes=5) - last_sent).total_seconds() // 300)

if diff == 0:
    print('Nothing to do')
    exit(0)

db_client = influxdb.InfluxDBClient(host='127.0.0.1', port=8086)
db_client.switch_database('meteo')

values = db_client.query(
    f'SELECT sum(lluvia) FROM sensores WHERE time > now() - {diff * 5}m GROUP BY time(5m);'
).raw['series'][0]['values']

local_now = utc_now.replace(tzinfo=timezone.utc).astimezone(tz=None)

for v in values[:-1]:
    lluvia = v[1]
    if lluvia == 0.0:
        stamp_file.write_text(f'{v[0]}\n{last_value}')
        continue

    if lluvia is None:
        continue

    timestamp = datetime.strptime(v[0], '%Y-%m-%dT%H:%M:%SZ')
    t = timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)

    last_value += lluvia
    params = {
        'Fecha': local_now.strftime('%d/%m/%Y-%H:%M:%S'),
        'ID': 'QBITACADEMY',
        'Vacum': round(last_value, 2)
    }
    r = requests.get(
        'http://cambiocli.uclm.es/rawdata/lluvia.php',
        params=params
    )
    r.raise_for_status()
    stamp_file.write_text(f'{v[0]}\n{last_value}\n{params}')
