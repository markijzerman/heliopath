'''
control 2 stepper motors via OSC
supported OSC commands
/angleYaw angle (float) stepmode (float) [example /angleYaw 45.0 0.0]
    angle in degrees positive turns right, negative left
    stepmode:   0 -> auto (controller decides when to switch to microstepping (default for angles < 10))
                1 -> single step mode (with microstepping when required to reach angle
                4 -> micro stepping mode single step / 16 stepsize
/anglePitch angle (float) stepmode(float)

/angleMaxYaw None 
    sets the max yaw angle to the current yaw angle
/angleMinYaw None
    sets the min yaw angle to the current yaw angle
/angleMaxPitch
/angleMinPitch
    like min and max for yaw
/zeroYaw
    set the new zero degrees position for the yaw stepper to the current yaw angle
/zeroPith
    like /zeroYaw but for pitch
/autoReleaseYaw
    turn the autorelease (auto power off) to on or off for the yaw stepper
/autoReleasePitch
    like the autorelease for yaw

fruitStepper4 takes 1 optional argument --port 
--port sets the UDP port for receiving OSC messages
'''


from __future__ import print_function
import liblo
import time

#from micropython import const
import _thread
import argparse
import signal


from adafruit_motorkit import MotorKit
from stepperControl import StepperControl



#initialize an adafruit Motorkit and pass its steppers to the StepperControl class
steppers = MotorKit()
stepperYaw = StepperControl(steppers.stepper1, 0)
stepperPitch = StepperControl(steppers.stepper2, 1)
#make sure they start with no power applied so it is still possible to make manual adjustments
stepperYaw.stepperRelease()
stepperPitch.stepperRelease()

#parse the CLI arguments
parser = argparse.ArgumentParser(description="Fruitstepper stepper control")
parser.add_argument('--port', metavar="port", type=int, nargs=1, default=[8000], required=False, help="port for receiving osc messages")
port = parser.parse_args().port[0]
#print(port)


#rudimentary ctrl-c catch to release the steppers when quiting
def userCancel:
    stepperYaw.stepperRelease()
    stepperPitch.stepperRelease()
    sys.exit(130) # 130 is standard exit code for ctrl-c

signal.signal(signal.SIGINT, userCancel)


#start a liblo OSC server thread so we don't have to block this thread
st = liblo.ServerThread(port)
print("Created Server Thread on Port", st.port)



def angleYaw_cb(path, args, types):
    '''OSC callback function for setting the yaw (horizontal) angle'''
    #print("angleYaw")
    stepperYaw.updateAngle(args[0])
    stepperYaw.setStepMode(args[1])


def anglePitch_cb(path, args, types):
    '''OSC callback function for setting the pitch (vertical) angle'''
    #print("anglePitch")
    stepperPitch.updateAngle(args[0])
    stepperPitch.setStepMode(args[1])


def setMaxYaw_cb(path, args, types):
    '''set maximum degrees for the yaw stepper'''
    #print("setMaxYaw")
    stepperYaw.setMax()
   

def setMinYaw_cb(path, args, types):
    '''set minimum degrees for the yaw stepper '''
    #print("setMinYaw")
    stepperYaw.setMin()


def setMaxPitch_cb(path, args, types):
    '''set maximum degrees for the pitch stepper'''
    stepperPitch.setMax()


def setMinPitch_cb(path, args, types):
    '''set minimum degrees for the pitch stepper'''
    stepperPitch.setMin()


def zeroYaw_cb(path, args, types):
    '''set a new zero degrees position for the yaw stepper'''
    stepperYaw.setZero()
  

def zeroPitch_cb(path, args, types):
    '''set a new zero degrees position for the pitch stepper'''   
    stepperPitch.setZero()
 

def releaseYaw_cb(path, args, types):
    '''turn the autorelease (auto power off) to on or off for the yaw stepper ''' 
    print("autoreleaseYaw %i" % args[0])
    if(args[0] == 1):
        stepperYaw.setAutorelease(True)
    elif(args[0] == 0):
        stepperYaw.setAutorelease(False)

 
def releasePitch_cb(path, args, types):
    '''turn the autorelease (power off) to on or off for the pitch stepper  '''   
    print("autoreleasePitch %i" % args[0])
    if(args[0] == 1):
        stepperPitch.setAutorelease(True)
    elif(args[0] == 0):
        stepperPitch.setAutorelease(False)

def deltaYaw_cb(path, args, types):
    '''set the delta angle of the light source for the mirror to compensate for its movement'''
    stepperYaw.setSourceDelta(args[0])

def deltaPitch_cb(path, args, types):
    '''set the delta angle of the light source for the mirror to compensate for its movement'''
    stepperPitch.setSourceDelta(args[0])
 
def fallback_cb(path, args, types, src):
    '''a callback to let the user know the program doesn't understand the messeage it received   '''
    print("got unknown message '%s' from '%s'" % (path, src.url))
    for a, t in zip(args, types):
        print("argument of type '%s': %s" % (t, a))




#hook all callbacks into the liblo server
st.add_method('/angleYaw', 'ff', angleYaw_cb)
st.add_method('/agnleYaw', 'fi' angleYaw_cb)
st.add_method('/anglePitch', 'ff', anglePitch_cb)
st.add_method('/anglePitch', 'fi', anglePitch_cb)
st.add_method('/setMaxYaw', None, setMaxYaw_cb)
st.add_method('/setMinYaw', None, setMinYaw_cb)
st.add_method('/setMaxPitch', None, setMaxPitch_cb)
st.add_method('/setMinPitch', None, setMinPitch_cb)
st.add_method('/zeroYaw', None, zeroYaw_cb)
st.add_method('/zeroPitch', None, zeroPitch_cb)
st.add_method('/autoreleaseYaw', 'i', releaseYaw_cb)
st.add_method('/autoreleasePitch', 'i', releasePitch_cb) 
st.add_method('/sourceDeltaYaw', 'f', deltaYaw_cb)
st.add_method('/sourceDeltaPitch', 'f', deltaPitch_cb)
st.add_method(None, None, fallback_cb)


#start the liblo server
st.start()



time.sleep(1)
print("fruitStepper Ready")

try:
    #start the stepper motor threads
    _thread.start_new_thread(stepperYaw.run,())
    _thread.start_new_thread(stepperPitch.run, ())
except:
    print("failed starting stepper threads")

while(True):
 

    pass
    time.sleep(0.1)

    
    
