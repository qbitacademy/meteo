import influxdb
import json

db_client = influxdb.InfluxDBClient(host='127.0.0.1', port=8086)
db_client.switch_database('meteo')

fields = ['humedad', 'temperatura', 'presion', 'viento_dir', 'viento_vel', 'uv']
query = ",".join([f"mean({x})" for x in fields])
values = db_client.query(
    f'SELECT {query} FROM sensores WHERE time > now() - 1h;'
).raw['series'][0]['values']

print(values)
# convertir a la cadena de envio para los sensores
