import cv2
from picamera2 import Picamera2
from adafruit_servokit import ServoKit
import random
import time
import logging
import traceback

# --------------------
# Logging setup
# --------------------
logging.basicConfig(
    filename="/home/x/logs/animatronic.log",
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# --------------------
# Servo channels
# --------------------
L_EYE_BALL = 0
L_EYE_LID = 1
R_EYE_BALL = 2
R_EYE_LID = 3
JAW = 4
NECK_X = 5
NECK_Y_RIGHT = 6
NECK_Y_LEFT = 7

def main():
    # --------------------
    # Camera X range
    # --------------------
    IN_X_MIN = 0.0
    IN_X_MAX = 160.0

    # --------------------
    # Neck PAN (X axis)
    # --------------------
    X_LEFT = 160.0
    X_CENTER = 90.0
    X_RIGHT = 30.0

    pan_angle = X_CENTER
    pan_angle_ave = X_CENTER
    pan_alpha = 0.15

    # --------------------
    # Neck TILT (Y axis)
    # --------------------
    Y_UP = 40
    Y_CENTER = 90
    Y_DOWN = 140

    tilt_angle = Y_CENTER
    tilt_angle_ave = Y_CENTER
    tilt_alpha = 0.10

    last_tilt_time = time.time()
    tilt_hold_start = None
    TILT_INTERVAL = 15.0    # how often nods may occur
    TILT_HOLD_TIME = 3.0    # how long to hold up/down

    # --------------------
    # Eyes
    # --------------------
    EYE_LEFT = 113.0
    EYE_CENTER = 90.0
    EYE_RIGHT = 66.0

    eyes_angle = EYE_CENTER
    eyes_angle_ave = EYE_CENTER
    eyes_alpha = 0.30

    # --------------------
    # Eyelids & jaw
    # --------------------
    L_EYE_LID_ave = 90
    R_EYE_LID_ave = 105
    JAW_ave = 108

    lid_alpha = 0.2
    jaw_alpha = 0.2

    L_target = L_EYE_LID_ave
    R_target = R_EYE_LID_ave
    JAW_target = JAW_ave

    last_eyelid_time = time.time()
    last_jaw_time = time.time()

    # --------------------
    # Turn-taking logic
    # --------------------
    last_turn_time = time.time()
    TURN_DURATION = 4.0
    EYES_BIAS = 0.75
    active_controller = "eyes"

    kit = ServoKit(channels=16)

    # --------------------
    # Camera setup
    # --------------------
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(
            main={"size": (160, 120), "format": "RGB888"}
        )
    )
    picam2.start()

    object_detector = cv2.createBackgroundSubtractorMOG2(
        history=50,
        varThreshold=16
    )

    # Comment out if planning to run in crontab
    cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera", 640, 480)
    cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Mask", 640, 480)

    try:
        while True:
            frame = picam2.capture_array()
            mask = object_detector.apply(frame)

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            biggest_box = None
            biggest_area = 0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 400:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w * h > biggest_area:
                        biggest_area = w * h
                        biggest_box = (x, y, w, h)

            if biggest_box:
                x, y, w, h = biggest_box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                eyes_angle = remap(x + w / 2, IN_X_MIN, IN_X_MAX, EYE_LEFT, EYE_RIGHT)
                pan_angle = remap(x + w / 2, IN_X_MIN, IN_X_MAX, X_LEFT, X_RIGHT)

            current_time = time.time()

            # --------------------
            # Turn taking
            # --------------------
            if current_time - last_turn_time > TURN_DURATION:
                active_controller = random.choices(
                    ["eyes", "neck"],
                    weights=[EYES_BIAS, 1 - EYES_BIAS]
                )[0]
                last_turn_time = current_time

            if active_controller == "eyes":
                eyes_angle_ave = eyes_angle * eyes_alpha + eyes_angle_ave * (1 - eyes_alpha)
                pan_angle_ave = X_CENTER * pan_alpha + pan_angle_ave * (1 - pan_alpha)
            else:
                pan_angle_ave = pan_angle * pan_alpha + pan_angle_ave * (1 - pan_alpha)
                eyes_angle_ave = EYE_CENTER * eyes_alpha + eyes_angle_ave * (1 - eyes_alpha)

            # --------------------
            # TILT (nod logic)
            # --------------------
            if tilt_hold_start is None:
                if current_time - last_tilt_time > TILT_INTERVAL:
                    tilt_angle = random.choice([Y_UP, Y_DOWN])
                    tilt_hold_start = current_time
            else:
                if current_time - tilt_hold_start > TILT_HOLD_TIME:
                    tilt_angle = Y_CENTER
                    tilt_hold_start = None
                    last_tilt_time = current_time

            tilt_angle_ave = tilt_angle * tilt_alpha + tilt_angle_ave * (1 - tilt_alpha)

            # --------------------
            # Drive servos
            # --------------------
            kit.servo[L_EYE_BALL].angle = int(eyes_angle_ave)
            kit.servo[R_EYE_BALL].angle = int(eyes_angle_ave)
            kit.servo[NECK_X].angle = int(pan_angle_ave)

            kit.servo[NECK_Y_RIGHT].angle = int(tilt_angle_ave)
            kit.servo[NECK_Y_LEFT].angle = int(180 - tilt_angle_ave)

            # --------------------
            # Eyelids
            # --------------------
            if current_time - last_eyelid_time > 3.0:
                L_target, R_target = random.choice([(120, 70), (50, 140), (90, 105)])
                last_eyelid_time = current_time

            L_EYE_LID_ave = L_target * lid_alpha + L_EYE_LID_ave * (1 - lid_alpha)
            R_EYE_LID_ave = R_target * lid_alpha + R_EYE_LID_ave * (1 - lid_alpha)

            kit.servo[L_EYE_LID].angle = int(L_EYE_LID_ave)
            kit.servo[R_EYE_LID].angle = int(R_EYE_LID_ave)

            # --------------------
            # Jaw
            # --------------------
            if current_time - last_jaw_time > 5.0:
                JAW_target = random.choice([68, 88, 108])
                last_jaw_time = current_time

            JAW_ave = JAW_target * jaw_alpha + JAW_ave * (1 - jaw_alpha)
            kit.servo[JAW].angle = int(JAW_ave)

            # Comment out if planning to run in crontab
            cv2.imshow("Camera", frame)
            cv2.imshow("Mask", mask)

            # Comment out if planning to run in crontab
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except Exception as e:
        logger.error("Unhandled exception occurred!")
        logger.error(traceback.format_exc())
    finally:
        logger.info("Shutting down safely")

        picam2.stop()
        cv2.destroyAllWindows()

def remap(x, in_min, in_max, out_min, out_max):
    x = max(in_min, min(x, in_max))
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

if __name__ == "__main__":
    main()
