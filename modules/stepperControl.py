''' wrapper class around adafruit motorkit for use with stepper motors 
It allows control of stepper motors using angles.


First implementation by Léon Spek in May 2019
'''


from adafruit_motorkit import MotorKit
from micropython import const
import time
import liblo


class StepperControl:
    
    #stepper 
    
    FORWARD = const(2)
    """Step forward"""
    BACKWARD = const(1)
    """"Step backward"""
    SINGLE = const(1)
    """Step so that each step only activates a single coil"""
    DOUBLE = const(2)
    """Step so that each step only activates two coils to produce more torque."""
    INTERLEAVE = const(3)
    """Step half a step to alternate between single coil and double coil steps."""
    MICROSTEP = const(4)
    """Step a fraction of a step by partially activating two neighboring coils. Step size is determined
       by ``microsteps`` constructor argument."""
       
    angle = 0
    motorPos = 0
    motorMax = 360
    motorMin = -360
    angleError = 0
    stepDir = FORWARD
    stepperAngle = 1.8
    microStepFactor =  1 / 16.0
    gearReduction = 5 
    motorStepping = False
    stepTime = 0.05
    minStepTime = 0.01
    stepMode = SINGLE
    target = liblo.Address("172.16.3.191", 8000)
    autorelease = True
    sourceDelta = 0
    compMode = False
       
       
       
    def __init__(self, stepperObject, stepperIndex=0):
        self.stepper = stepperObject
        self.index = stepperIndex
    
    
    
    def updateAngle(self, newAngle):
        '''update the stepper motor angle to the desired angle'''
        if(newAngle > self.motorMax):
            newAngle = self.motorMax
        elif(newAngle < self.motorMin):
            newAngle = self.motorMin
        
        self.angle = newAngle
            
        '''if(abs(self.angle - self.motorPos) < 10):
            self.minStepTime = 0.05
        else:
            self.minStepTime = 0.02'''
        
    def setStepMode(self, mode):
        '''set the stepping mode, 0 = auto, 1 = single, 4 = microstepping. Auto will pick microstepping for small angles < 10'''
        if(mode == 0):
            if(abs(self.angle - self.motorPos) < 10 ):
                self.stepMode = 4 #microstepping for small angles
            else:
                self.stepMode = 1 #single stepping
        else:
            self.stepMode = mode
        
        
    def setZero(self):
        '''set the current angle as the new zero angle'''
        self.motorPos = 0
        self.angleError = 0
        self.angle = 0
        
    def setMax(self):
        '''set the current angle as the maximum angle, the stepper will not move beyond this angle'''
        self.motorMax = self.motorPos
        
    def setMin(self):
        '''set the current angle as the minimum angle, the stepper will not move beyond this angle'''
        self.motorMin = self.motorPos
        
    def stepperRelease(self):
        '''release power -> power off the stepper. No hold current will be applied'''
        self.stepper.release()
    
    def setAutorelease(self, release):
        '''turn autorelease on (True) or off (False). StepperControl will automatically power off the stepper or not'''
        self.autorelease = release

    def setSourceDelta(self, deltaVal):
        '''set the delta angle of the light source for the mirror to compensate for its movement'''
        self.sourceDelta = deltaVal

    def setSourceCompensation(self, mode):
        self.compMode = mode
        
        
    def run(self):
        '''the StepperControl loop'''
        while(True):
            if(compMode):
                '''compensate for source movement.
                conditions: source is higher than reflection 
                reflections light up shadows from the source
                in the case of the sun: mirror is aimed towards the southern side of the sky able to send sunlight into shadow
                '''
                angleDifference = (self.angle + (0.5 * self.sourceDelta)) - self.motorPos
            else:
                angleDifference = self.angle - self.motorPos

            if(angleDifference > 0.0):
                self.stepDir = self.FORWARD
            else:
                self.stepDir = self.BACKWARD
        
            #calculate the step angle and microstep angle -> this could probably happen in initialisation
            stepAngle = self.stepperAngle / self.gearReduction
            microStepAngle = stepAngle * self.microStepFactor
        
            stepDistance = abs(angleDifference) / stepAngle
        
            #accel true or false decision needs to be made elsewhere... currently always on, not otherwise implemented
            accel = True
            
            #it might me useful to send some position feedback using OSC
            #it is commented out because it interfered with the stepping process
            #it probably needs the somehow be in a seperate thread
            #target = liblo.Address(57120)

            #take a steps based on the difference between stepper position and user supplied angle
            if(abs(angleDifference) > stepAngle and self.stepMode == self.SINGLE ):
                #single (full) size steps
                self.motorStepping = True
                self.stepper.onestep(direction=self.stepDir, style=self.SINGLE)
                #liblo.send(self.target, "/mAngle", self.index, self.motorPos)
                if(self.stepDir == self.FORWARD):
                    self.motorPos += stepAngle
                else:
                    self.motorPos -= stepAngle
            elif(abs(angleDifference) > microStepAngle):
                #once the remaining angle difference is smaller than a full step take microsteps
                self.motorStepping = True
                self.stepper.onestep(direction=self.stepDir, style=self.MICROSTEP)
                if(self.stepDir == self.FORWARD):
                    self.motorPos += microStepAngle
                else:
                    self.motorPos -= microStepAngle
                #liblo.send(self.target, "/mAngle", self.index, self.motorPos)
            elif(abs(angleDifference) < microStepAngle and self.motorStepping == True): 
                #when angleDifference is to small to take another step, stop stepping (if stepper was stepping...)
                #liblo.send(target, "/mAngle", self.motorPos)
                self.motorStepping = False
                if(self.autorelease == True):
                    self.stepper.release()
                #add / substract the resulting angular error to the accumulated angular error
                if(self.stepDir == self.FORWARD):
                    self.angleError += angleDifference
                else:
                    self.angleError -= angleDifference
                    #calculate error
            
            #correct the accumulated error when it's bigger than a microstep
            if(abs(self.angleError) > microStepAngle ):
                
                if(self.angleError > 0):
                    if(self.stepDir == self.FORWARD):
                        self.stepDir == self.BACKWARD
                        self.motorPos += microStepAngle
                        #print("error correction > 0 self.BACKWARD")
                    else:
                        self.stepDir == self.FORWARD
                        self.motorPos -= microStepAngle
                        #print("error correction > 0 self.FORWARD")
                    self.angleError -= microStepAngle
                    self.stepper.onestep(direction=self.stepDir, style=self.MICROSTEP)
                    if(self.autorelease == True):
                        self.stepper.release()
                    #liblo.send(self.target, "/mAngle", self.index, self.motorPos)
                else:
                    self.angleError += microStepAngle
                    self.motorPos += microStepAngle
                    #print("error correction < 0")
                    self.stepper.onestep(direction=self.stepDir, style=self.MICROSTEP)
                    if(self.autorelease == True):
                        self.stepper.release()
                    #liblo.send(target, "/mAngle", self.motorPos)
        


            
            #a simple acceleration scheme -> this needs more work
            if(self.stepTime > self.minStepTime and self.motorStepping == True and stepDistance > 15 and accel == True):
                self.stepTime -= 0.001
            elif(self.stepTime < self.minStepTime and self.motorStepping == True and stepDistance < 16 and accel == True):
                self.stepTime += 0.001

            time.sleep(self.stepTime)
    
