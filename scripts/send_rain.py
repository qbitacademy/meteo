import influxdb
import json

db_client = influxdb.InfluxDBClient(host='127.0.0.1', port=8086)
db_client.switch_database('meteo')

values = db_client.query(
    f'SELECT sum(lluvia) FROM sensores WHERE time > now() - 5m;'
).raw['series'][0]['values'][0]

if values[1] != 0.0:
    print(values)
    # convertir a la cadena de envio para lluvia
