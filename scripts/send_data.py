import json
import pathlib
from datetime import datetime, timedelta, timezone

import influxdb

import requests

stamp_file = pathlib.Path(__file__).parent.resolve() / '.sensors_last_sent'

try:
    last_sent = datetime.strptime(
        stamp_file.read_text().split()[0], '%Y-%m-%dT%H:%M:%SZ'
    )
except Exception:
    last_sent = datetime.utcnow() - timedelta(hours=1)

diff = int((datetime.utcnow() - last_sent).total_seconds() // 3600)

if diff == 0:
    print('Nothing to do')
    exit(0)


db_client = influxdb.InfluxDBClient(host='127.0.0.1', port=8086)
db_client.switch_database('meteo')

fields = ['humedad', 'temperatura', 'presion', 'viento_dir', 'viento_vel', 'uv']
query = ",".join([f"mean({x})" for x in fields])
values = db_client.query(
    f'SELECT {query} FROM sensores WHERE time > now() - {diff}h GROUP BY time(1h);'
).raw['series'][0]['values']

for v in values[1:]:
    timestamp = datetime.strptime(v[0], '%Y-%m-%dT%H:%M:%SZ')
    t = timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)
    humedad, temperatura, presion, vdir, vvel, uv = [v if v is not None else 9999 for v in v[1:]]

    params = {
        'Fecha': t.strftime('%d/%m/%Y-%H:%M:%S'),
        'ID': 'QBITACADEMY',
        'Temp': round(temperatura, 2),
        'Pres': round(presion * 100, 2),
        'Hum': round(humedad, 2),
        'RadUV': round((uv-0.99)*8.28, 2),
        'WindU': round(vvel, 2),
        'WindD': round(float(vdir), 2),
    }
    r = requests.get(
        'http://cambiocli.uclm.es/rawdata/otros.php',
        params=params
    )
    r.raise_for_status()
    stamp_file.write_text(f'{v[0]}\n{params}')
