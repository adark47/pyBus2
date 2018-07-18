#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from subprocess import Popen, PIPE
sys.path.append('/root/pyBus/lib')
#from __future__ import absolute_import, print_function, unicode_literals
import dbus
import dbus.service
import dbus.mainloop.glib
import bluezutils
import bluetool
import logging
import time

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject


BLUETOOTH = False # systemctl disable bluetooth-agent
btMp = None
btMo = None
btMacLast = None

# Temp file for mac addr
btMacAddr = '/root/pyBus/lib/bt_mac'

btCtl = bluetool.Bluetooth()

BUS_NAME = 'org.bluez'
MEDIA_PLAYER_INTERFACE = 'org.bluez.MediaPlayer1'


def find_media_player():
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
    mo = manager.GetManagedObjects()

    for path, ifaces in mo.iteritems():
        mp = ifaces.get(MEDIA_PLAYER_INTERFACE)
        if mp is None:
            continue
        obj = bus.get_object('org.bluez', path)
        return dbus.Interface(obj, MEDIA_PLAYER_INTERFACE)
    raise Exception("Bluetooth MediaPlayer no found")

############################################################################
# FUNCTIONS CONNECTION BLUETOOTH
############################################################################

def init():
    btReadMac()
    disconnect()
    logging.info('Initialized: Bluetooth ')



def connect():
    global btMp
    global btMo
    global btMacLast

    btCtl.get_available_devices()
    if btCtl.connect(btMacLast) == True:
        time.sleep(1)
        btMp = find_media_player()
        btMo = bluezutils.get_managed_objects()
        logging.info('Connection to the Bluetooth device: Connected - %s' % btMacLast)

        return True
    elif btCtl.connect(btMacLast) == False:
        logging.info('Connection to the Bluetooth device: Device is disabled - %s' % btMacLast)
        return False
    else:
        logging.error('Connection to the Bluetooth device: Unknown error')


def end():
    logging.info('End: Bluetooth')
    btCtl.disconnect()



def disconnect():
    global btMacLast
    btReadMac()
    btCtl.disconnect(btMacLast)
    logging.debug('Disabled bluetooth device: %s' % btMacLast)


def disconnectMac(mac):
    btCtl.disconnect(mac)
    logging.debug('Disabled bluetooth device: %s' % mac)


def newConnect(mac):
    global btMacLast
    disconnect()
    if btCtl.connect(mac) == True:
        time.sleep(1)
        btWriteMac(mac)
        logging.info('Connect to a new Bluetooth device: Connected - %s' % mac)
        return True
    elif btCtl.connect(mac) == False:
        logging.info('Connect to a new Bluetooth device: Device is disabled - %s' % mac)
        return False
    else:
        logging.error('Connect to a new Bluetooth device: Unknown error')


def btReadMac():
    global btMacLast
    btMac = open(btMacAddr, 'r+')
    btMacLast = btMac.read()
    btMac.close()


def btWriteMac(mac):
    btMac = open(btMacAddr, 'r+')
    btMac.write(mac)
    btMac.close()


def pairedDevices():     # Trust devices
    return btCtl.get_paired_devices()


def connectedDevices():
    return btCtl.get_connected_devices()


def scanDevices():
    btCtl.scan()
    #btCtl.start_scanning(30)
    return btCtl.get_available_devices()


def removeMac(mac):
    btCtl.remove(mac)
    logging.debug('Removed bluetooth device: %s' % mac)

############################################################################
# FUNCTIONS PLAYER
############################################################################

def Play():
    btMp.Play()

def Pause():
    btMp.Pause()

def Stop():
    btMp.Stop()

def Next():
    btMp.Next()

def Prev():
    btMp.Previous()

def RewindPrev():
    btMp.Rewind()

def RewindNext():
    btMp.FastFoward()

def getTrackInfo():
    dictTrack = {}
    for path, ifaces in btMo.iteritems():
        if MEDIA_PLAYER_INTERFACE not in ifaces:
            continue
        props = ifaces[MEDIA_PLAYER_INTERFACE]
        for key, value in props.items():
            if key == 'Track':
                for k, v in value.items():
                    dictTrack[k] = v
            else:
                dictTrack[key] = value

    return dictTrack

############################################################################
# SERVICE MANAGEMENT BLUETOOTH-AGENT
############################################################################

def serviceBluetoothStatus():
    p = Popen(['ps', '-A'], stdout=PIPE)    # ps -A for TEST
    stdout, stderr = p.communicate()
    if 'bluetooth-agent' in str(stdout):
        logging.info('Service bluetooth-agent started')
        return True
    else:
        logging.info('Service bluetooth-agent not started')
        return False


def serviceBluetooth():
    service = 'bluetooth-agent'
    global BLUETOOTH

    if not BLUETOOTH:
        logging.info('Starting bluetooth-agent process...')
        p = Popen(['sudo', 'systemctl', 'start', service], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        errcode = p.returncode

        if errcode != 0:
            logging.error('Error while starting bluetooth-agent')
            logging.error(' - stderr : %s' %stderr)
            logging.error(' - stdout : %s' %stdout)

        logging.info('Starting bluetooth-agent process... OK')
        BLUETOOTH = True
        return True

    else:
        logging.info('Stopping bluetooth-agent process...')
        p = Popen(['sudo', 'systemctl', 'stop', service], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        errcode = p.returncode

        if errcode != 0:
            logging.error('Error while stopping bluetooth-agent')
            logging.error(' - stderr : %s' %stderr)
            logging.error(' - stdout : %s' %stdout)

        logging.info('Stopping bluetooth-agent process... OK')
        BLUETOOTH = False
        return False

############################################################################