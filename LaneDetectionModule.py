import cv2
import numpy as np
import utlis
import RPi.GPIO as GPIO
from gpiozero import AngularServo
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

motorA1, motorA2 = 2,3

GPIO.setup(motorA1, GPIO.OUT)
GPIO.setup(motorA2, GPIO.OUT)
pwmA1 = GPIO.PWM(motorA1, 50)
pwmA2 = GPIO.PWM(motorA2, 50)
pwmA1.start(0)
pwmA2.start(0)

servo = AngularServo(18, min_pulse_width=0.0006, max_pulse_width=0.0023)
curveList = []
avgVal = 10

def getLaneCurve(img, display=2):
    imgCopy = img.copy()
    imgResult = img.copy()
    imgThres = utlis.thresholding(img)

    hT, wT, c = img.shape
    points = utlis.valTrackbars()
    imgWarp = utlis.warpImg(imgThres, points, wT, hT)
    imgWarpPoints = utlis.drawPoints(imgCopy, points)

    middlePoint, imgHist = utlis.getHistogram(imgWarp, display=True, minPer=0.5, region=4)
    curveAveragePoint, imgHist = utlis.getHistogram(imgWarp, display=True, minPer=0.9)
    curveRaw = curveAveragePoint - middlePoint

    curveList.append(curveRaw)
    if len(curveList) > avgVal:
        curveList.pop(0)
    curve = int(sum(curveList) / len(curveList))

    if display != 0:
        imgInvWarp = utlis.warpImg(imgWarp, points, wT, hT, inv=True)
        imgInvWarp = cv2.cvtColor(imgInvWarp, cv2.COLOR_GRAY2BGR)
        imgInvWarp[0:hT // 3, 0:wT] = 0, 0, 0
        imgLaneColor = np.zeros_like(img)
        imgLaneColor[:] = 0, 255, 0
        imgLaneColor = cv2.bitwise_and(imgInvWarp, imgLaneColor)
        imgResult = cv2.addWeighted(imgResult, 1, imgLaneColor, 1, 0)
        midY = 450
        cv2.putText(imgResult, str(curve), (wT // 2 - 80, 85), cv2.FONT_HERSHEY_COMPLEX, 2, (255, 0, 255), 3)
        cv2.line(imgResult, (wT // 2, midY), (wT // 2 + (curve * 3), midY), (255, 0, 255), 5)
        cv2.line(imgResult, ((wT // 2 + (curve * 3)), midY - 25), (wT // 2 + (curve * 3), midY + 25), (0, 255, 0), 5)
        for x in range(-30, 30):
            w = wT // 20
            cv2.line(imgResult, (w * x + int(curve // 50), midY - 10),
                     (w * x + int(curve // 50), midY + 10), (0, 0, 255), 2)
        ##fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);
        ##cv2.putText(imgResult, 'FPS ' + str(int(fps)), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (230, 50, 50), 3);
    if display == 2:
        imgStacked = utlis.stackImages(0.7, ([img, imgWarpPoints, imgWarp],
                                             [imgHist, imgLaneColor, imgResult]))
        cv2.imshow('ImageStack', imgStacked)
    elif display == 1:
        cv2.imshow('Resutlt', imgResult)

    return curve


if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    intialTrackBarVals = [102, 80, 20, 214]
    utlis.initializeTrackbars(intialTrackBarVals)
    frameCounter = 0

    while True:
        frameCounter += 1
        if cap.get(cv2.CAP_PROP_FRAME_COUNT) == frameCounter:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frameCounter = 0

        success, img = cap.read()
        img = cv2.resize(img, (480, 240))
        curve = getLaneCurve(img, display=1)

        if curve > 20:
            curveD = 20
        elif 20 > curve >= 0:
            curveD = curve
        elif curve < -20:
            curveD = -20
        elif -20 < curve <= 0:
            curveD = curve

        print(curveD)
        servo.angle = curveD

        cv2.imshow('Vid', img)
        cv2.waitKey(1)