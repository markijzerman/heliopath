'''this script gets the current position of the sun, the heading of the mirrorbase and turns the mirror towards it, 
then it will track the position of the sun by updating periodically according to it's interval arguement (optional argument, it defaults to 60s)
NOTE: It will keep the mirror aimed at the sun.
By calling this script with the --heading option the user can bypass the compass reading and supply a custom heading.
This can be useful in case where the compass doesn't give an accurate reading.


'''

import MirrorGPS
import liblo
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, get_sun
from astropy.time import Time
import astropy.units as u
from astropy.utils import iers
import time as t
import argparse

import wmm2015 as wmm


parser = argparse.ArgumentParser(description="Fruitstepper stepper control")
parser.add_argument('--heading', metavar="heading", type=int, nargs=1, default=[None], required=False, help="heading of the sun tracker, 0 is due north")
parser.add_argument('--interval', metavar="interval", type=int, narg=1, default=[60], required=False, help="interval in seconds between sun position updates")
argHeading = parser.parse_args().heading[0]
trackingInterval = parser.parse_args().interval[0]


#max age of astropy data in days
iers.conf.auto_max_age = 365


motionCtrlAddress = liblo.Address("127.0.0.1", 8000)
       
gps = MirrorGPS.getGPSinfo()
print(gps)
date = gps[0]
time = gps[1]
suntime = Time(date + " " + time)
lon = float(gps[2]) / 100
lat = float(gps[4]) / 100
print("lon: %f" % lon)
print("lat: %f" % lat)
print("suntime: %s" % suntime)
sunPos = get_sun(suntime)
print("sunra: %s" % sunPos.ra)
magDecl = wmm.wmm(lat, lon, 0, 2019)
print("magDecl: %s" % (magDecl.decl.item(),))

location = EarthLocation.from_geodetic(lat=lat, lon=lon, height=0)
altaz = sunPos.transform_to(AltAz(obstime=suntime, location=location))
sunalt = 90 - altaz.alt.deg
sunaz = altaz.az.deg
print(sunalt, sunaz)

if(argHeading == None):
    import berryIMU
    orientation = berryIMU.getValues()
    print("pitch: %s , roll: %s , heading: %s" % orientation)
    heading = orientation[2] - magDecl.decl.item()
    print("corrected heading %f" % heading)
else:
    heading = argHeading

'''if(heading < 180):
    northComp = 90 - heading
else:
    northComp = 90 + (360 - heading)'''
    
if(heading < 180):
    northComp = 90  - heading
else:
    northComp = 90 + (360 - heading)
    
print("northComp: %f" % northComp)
    
sunYaw = sunaz
print("sunYaw: %f" % sunYaw)
sunPitch = sunalt
print("sunPitch: %f" % sunPitch)
liblo.send(motionCtrlAddress, "/angleYaw", northComp, 1)
t.sleep(10)
liblo.send(motionCtrlAddress, "/zeroYaw", 1)
liblo.send(motionCtrlAddress, "/angleYaw", sunaz - 180, 1)
t.sleep(0.5)
liblo.send(motionCtrlAddress,"/anglePitch", sunalt * -1, 1)
liblo.send(motionCtrlAddress, "/autoreleasePitch", 0)
t.sleep(trackingInterval)

while(True):
    #update the current time after the interval
    gps = MirrorGPS.getGPSinfo()
    time = gps[1]
    suntime = Time(date + " " + time)
    #get new sun position
    sunPos = get_sun(suntime)
    #convert to altaz system
    altaz = sunPos.transform_to(AltAz(obstime=suntime, location=location))
    sunalt = 90 - altaz.alt.deg
    sunaz = altaz.az.deg
    #send new position to fruitstepper4.py
    liblo.send(motionCtrlAddress, "/angleYaw", sunaz - 180, 1)
    liblo.send(motionCtrlAddress,"/anglePitch", sunalt * -1, 1)
    t.sleep(trackingInterval)

