#!/usr/bin/env python
# -*- coding: utf-8 -*-

Registries = {
    '00': '',
    '01': 'Device status request',
    '02': 'Device status ready',
    '03': 'Bus status request',
    '04': 'Bus status',
    '05': '',
    '06': 'DIAG read memory',
    '07': 'DIAG write memory',
    '08': 'DIAG read coding data',
    '09': 'DIAG write coding data',
    '0A': '',
    '0B': '',
    '0C': 'Vehicle control',
    '0D': '',
    '0E': '',
    '0F': '',
    '10': 'Ignition status request',
    '11': 'Ignition status',
    '12': 'IKE sensor status request',
    '13': 'IKE sensor status',
    '14': 'Country coding status request',
    '15': 'Country coding status',
    '16': 'Odometer request',
    '17': 'Odometer',
    '18': 'Speed/RPM',
    '19': 'Temperature',
    '1A': 'IKE text display/Gong',
    '1B': 'IKE text status',
    '1C': 'Gong',
    '1D': 'Temperature request',
    '1E': '',
    '1F': 'UTC time and date',
    '20': '',
    '21': 'Radio Short cuts',
    '22': 'Text display confirmation',
    '23': 'Display Text',
    '24': 'Update ANZV',
    '25': '',
    '26': '',
    '27': '',
    '28': '',
    '29': '',
    '2A': 'On-Board Computer State Update',
    '2B': 'Phone LEDs',
    '2C': 'Phone symbol',
    '2D': '',
    '2E': '',
    '2F': '',
    '30': '',
    '31': 'Select screen item',
    '32': 'MFL volume buttons',
    '33': '',
    '34': 'DSP Equalizer Button',
    '35': '',
    '36': '',
    '37': '',
    '38': 'CD status request',
    '39': 'CD status',
    '3A': '',
    '3B': 'MFL media buttons',
    '3C': '',
    '3D': 'SDRS status request',
    '3E': 'SDRS status',
    '3F': '',
    '40': 'Set On-Board Computer Data',
    '41': 'On-Board Computer Data Request',
    '42': '',
    '43': '',
    '44': '',
    '45': '',
    '46': 'LCD Clear',
    '47': 'BMBT buttons',
    '48': 'BMBT buttons',
    '49': 'KNOB button',
    '4A': 'Monitor CD/Tape control',
    '4B': 'Monitor CD/Tape status',
    '4C': '',
    '4D': '',
    '4E': '',
    '4F': 'Monitor Control',
    '50': '',
    '51': '',
    '52': '',
    '53': 'Vehicle data request',
    '54': 'Vehicle data status',
    '55': '',
    '56': '',
    '57': '',
    '58': '',
    '59': '',
    '5A': 'Lamp status request',
    '5B': 'Lamp status',
    '5C': 'Instrument cluster lighting status',
    '5D': '',
    '5E': '',
    '5F': '',
    '60': '',
    '61': '',
    '62': '',
    '63': '',
    '64': '',
    '65': '',
    '66': '',
    '67': '',
    '68': '',
    '69': '',
    '6A': '',
    '6B': '',
    '6C': '',
    '6D': 'Sideview Mirror',
    '6E': '',
    '6F': '',
    '70': '',
    '71': 'Rain sensor status request',
    '72': 'Remote Key buttons',
    '73': '',
    '74': 'EWS key status',
    '75': '',
    '76': 'External lights',
    '77': '',
    '78': '',
    '79': 'Doors/windows status request',
    '7A': 'Doors/windows status',
    '7B': '',
    '7C': 'SHD status',
    '7D': '',
    '7E': '',
    '7F': '',
    '80': '',
    '81': '',
    '82': '',
    '83': '',
    '84': '',
    '85': '',
    '86': '',
    '87': '',
    '88': '',
    '89': '',
    '8A': '',
    '8B': '',
    '8C': '',
    '8D': '',
    '8E': '',
    '8F': '',
    '90': '',
    '91': '',
    '92': '',
    '93': '',
    '94': '',
    '95': '',
    '96': '',
    '97': '',
    '98': '',
    '99': '',
    '9A': '',
    '9B': '',
    '9C': '',
    '9D': '',
    '9E': '',
    '9F': '',
    'A0': 'DIAG data',
    'A1': '',
    'A2': 'Current position and time',
    'A3': '',
    'A4': 'Current location',
    'A5': 'Screen text',
    'A6': '',
    'A7': 'TMC status request',
    'A8': '',
    'A9': '',
    'AA': 'Navigation Control',
    'AB': '',
    'AC': '',
    'AD': '',
    'AE': '',
    'AF': '',
    'B0': '',
    'B1': '',
    'B2': '',
    'B3': '',
    'B4': '',
    'B5': '',
    'B6': '',
    'B7': '',
    'B8': '',
    'B9': '',
    'BA': '',
    'BB': '',
    'BC': '',
    'BD': '',
    'BE': '',
    'BF': '',
    'C0': '',
    'C1': '',
    'C2': '',
    'C3': '',
    'C4': '',
    'C5': '',
    'C6': '',
    'C7': '',
    'C8': '',
    'C9': '',
    'CA': '',
    'CB': '',
    'CC': '',
    'CD': '',
    'CE': '',
    'CF': '',
    'D0': '',
    'D1': '',
    'D2': '',
    'D3': '',
    'D4': 'RDS channel list',
    'D5': '',
    'D6': '',
    'D7': '',
    'D8': '',
    'D9': '',
    'DA': '',
    'DB': '',
    'DC': '',
    'DD': '',
    'DE': '',
    'DF': '',
    'E0': '',
    'E1': '',
    'E2': '',
    'E3': '',
    'E4': '',
    'E5': '',
    'E6': '',
    'E7': '',
    'E8': '',
    'E9': '',
    'EA': '',
    'EB': '',
    'EC': '',
    'ED': '',
    'EE': '',
    'EF': '',
    'F0': '',
    'F1': '',
    'F2': '',
    'F3': '',
    'F4': '',
    'F5': '',
    'F6': '',
    'F7': '',
    'F8': '',
    'F9': '',
    'FA': '',
    'FB': '',
    'FD': '',
    'FE': '',
    'FF': ''
}