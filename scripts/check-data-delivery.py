#!/usr/bin/env python3

# Script for testing the connection with CCAyA project. Just needs
# "requests" as a dependency. Connection details must be provided once
# you have been accepted to the project


import argparse
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='server IP/hostname')
    parser.add_argument('station_name', help='your assigned station name')
    args = parser.parse_args()

    print('Testing rain data delivery...')
    path = 'rawdata/lluvia.php'
    params = {
        'Fecha': '7/2/2020-15:15:15',
        'ID': args.station_name,
        'Vacum': 111.111
    }

    r = requests.get(f'http://{args.host}/{path}', params=params)
    print(f'Reply: {r.text}')

    print('Testing general data delivery...')
    path = 'rawdata/otros.php'
    params = {
        'Fecha': '7/2/2020-15:15:15',
        'ID': args.station_name,
        'Temp': 22.22,
        'Pres': 99999.99,
        'Hum': 33.33,
        'RadUV': 0.888,
        'WindU': 44.444,
        'WindD': 55.555,
    }
    r = requests.get(f'http://{args.host}/{path}', params=params)
    print(f'Reply: {r.text}')
    print('Check the output of both tests and confirm everything is fine!')
    return 0


if __name__ == '__main__':
    exit(main())
