''' module to get GPS position and set the system clock using the GPS time code
    It assumes a NMEA2 standard GPS string
    The script will wait (and block) untill it has proper location (4 satellites) and time information  
    While running it will set the system time and upon completion return the current location and current time as a tuple
    (date, time, longitude, longitude direction (east / west from 0), latitude, latutide direction (norht / south from 0), elevation)
    Note: elevation doesn't seem to be very accurate

    First implentation by Léon Spek in May 2019
'''


import os
import sys
import time
import datetime

import serial
import pynmea2

def getGPSinfo():
    "returns a tuple with GPS info: gpsDate, gpsTime, gpsLong, gpsLongDir, gpsLat, gpsLatDir, gpsElev"
    print("Getting GPS info")
    print("")
    gpsDate =""
    gpsTimestamp= ""
    gpsNumSats = 0
    timeSet = False
    gpsInput = 0
    gpsLong = ""
    gpsLongDir = ""
    gpsLat = ""
    gpsLatDir =""
    gpsElev = ""
    serialData =""
    waitingForGPS = True
    port = "/dev/serial0"

    
    def parseGPS(str):
        nonlocal gpsDate
        nonlocal gpsTimestamp
        nonlocal gpsInput
        nonlocal gpsNumSats
        nonlocal gpsLong
        nonlocal gpsLongDir
        nonlocal gpsLat
        nonlocal gpsLatDir
        nonlocal gpsElev
        
        if str.find('GGA') > 0:
            msg = pynmea2.parse(str)
            #print ("Timestamp: %s -- Lat: %s %s -- Lon: %s %s -- Altitude: %s %s -- Satellites: %s" % (msg.timestamp,msg.lat,msg.lat_dir,msg.lon,msg.lon_dir,msg.altitude,msg.altitude_units,msg.num_sats))
            gpsTimestamp = msg.timestamp
            gpsNumSats = int(msg.num_sats)
            gpsLong = msg.lon
            gpsLongDir = msg.lon_dir
            gpsLat = msg.lat
            gpsLatDir = msg.lat_dir
            gpsElev = msg.altitude
           
            #print(gpsTimestamp)
            #print(gpsNumSats)
            return msg
        if str.find('ZDA') > 0:
            msg = pynmea2.parse(str)
            gpsDate = msg.datestamp
            #print(gpsDate)
            #exit()
            return msg
    
    #setSystimeWithGPS(date, time) as datetime objects from GPS msg (this sudo trickery only works on a raspberry pi...)
    def setSystimeWithGPS(gpsDate, gpsTime):
            print("Setting system time")
            date = gpsDate.isoformat()
            time = gpsTime.isoformat()
            nonlocal timeSet
            timeString = date + " " + time
            os.system('sudo date -u --set="%s"' % timeString)
            print("")
            timeSet = True
            
    
    ''' open serial port and set up gps receiver to also output datestamp ('ZDA') strings'''
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    intervalMsg = bytearray(("$PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0").encode('utf8'))
    #calculate checksum of string after $
    checksum = 0
    for i in range(1, len(intervalMsg)):
        checksum ^= intervalMsg[i]
    #extend string with * checksum and <CR><LF>    
    intervalMsg.extend(("*").encode('utf8'))
    intervalMsg.extend(hex(checksum).encode('utf8')[2:4])
    intervalMsg.extend(("\r\n").encode('utf8'))
    #send command to gps receiver
    serialPort.write(intervalMsg)
    #print(intervalMsg)
    #os.system('sudo date -u --set="20190511 12:35:00"')
    
    
    while waitingForGPS:
        	 
        serialData = serialPort.readline()
        ##print(serialData)
        try:
            
            string = serialData.decode('utf8')
           
        except UnicodeDecodeError:
            print("unicode decode error! Ignoring serialport message...")
        else:
            ##print(serialData)
            gpsData = parseGPS(string)
        if timeSet == False and gpsNumSats >= 3:
            dStr = ""
            try:
                gpsDate.isoformat()
            except:
                #print("isoformat error...moving along")
                pass
            else:
                dStr = gpsDate.isoformat()
            tStr = ""
            try:
                gpsDate.isoformat()
            except:
                pass
                #print("isoformat error ... moving along")
            else:
                tStr = gpsTimestamp.isoformat()
            if(len(dStr) != 0 and len(tStr) != 0):
                setSystimeWithGPS(gpsDate, gpsTimestamp)
        if timeSet == True and gpsNumSats >= 4:
           waitingForGPS = False
           returnDate = gpsDate.isoformat()
           returnTime = gpsTimestamp.isoformat()
           if(len(gpsLong) != 0 and len(gpsLongDir) != 0 and len(gpsLat) != 0 and len(gpsLatDir) != 0):
                return (returnDate, returnTime, gpsLong, gpsLongDir, gpsLat, gpsLatDir, gpsElev)
    
    
    
