from adafruit_servokit import ServoKit
import time

def calibration(kit):

    # Initialize the servokit with 16 channels
    #kit = ServoKit(channels=16)

    # Servo channel assignments
    L_EYE_BALL = 0
    L_EYE_LID = 1
    R_EYE_BALL = 2
    R_EYE_LID = 3

    JAW = 4

    X_AXIS = 5
    Y_AXIS_RIGHT = 6
    Y_AXIS_LEFT = 7

    # Eyes
    kit.servo[L_EYE_BALL].angle = 90
    kit.servo[R_EYE_BALL].angle = 90
    kit.servo[L_EYE_LID].angle = 90
    kit.servo[R_EYE_LID].angle = 105

    # Jaw
    kit.servo[JAW].angle = 108
    time.sleep(1)

    # Neck
    kit.servo[X_AXIS].angle = 90
    time.sleep(2)
    kit.servo[Y_AXIS_RIGHT].angle = 90
    kit.servo[Y_AXIS_LEFT].angle = 90
