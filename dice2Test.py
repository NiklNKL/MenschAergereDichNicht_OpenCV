# https://github.com/jimthompson5802/dice_counting/blob/master/dice_dot_counting.ipynb
# https://github.com/BenyaminZojaji/Dice-Recognition/blob/main/dice_recognition.ipynb

import cv2
import numpy as np
from collections import deque
 
 
min_threshold = 10                      # these values are used to filter our detector.
max_threshold = 200                     # they can be tweaked depending on the camera distance, camera angle, ...
min_area = 100                          # ... focus, brightness, etc.
min_circularity = 0.3
min_inertia_ratio = 0.5
 
cap = cv2.VideoCapture(2)               # '0' is the webcam's ID. usually it's 0/1/2/3/etc. 'cap' is the video object.
cap.set(15, -4)                         # '15' references video's exposure. '-4' sets it.
 
counter = 0                             # script will use a counter to handle FPS.
readings = deque([0, 0], maxlen=10)     # lists are used to track the number of pips.
display = deque([0, 0], maxlen=10)
dice = []
oldDice = [0] 
while True:
    ret, img = cap.read()                                    # 'im' will be a frame from the video.
 
    params = cv2.SimpleBlobDetector_Params()                # declare filter parameters.
    params.filterByArea = True
    params.filterByCircularity = True
    params.filterByInertia = True
    params.minThreshold = min_threshold
    params.maxThreshold = max_threshold
    params.minArea = min_area
    params.minCircularity = min_circularity
    params.minInertiaRatio = min_inertia_ratio

    edges = cv2.Canny(img,100,500)
    
    die_contours,_ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total_number_dots = 0
    
    for die_roi in die_contours:
        (die_x,die_y,die_w, die_h) = cv2.boundingRect(die_roi)
        if die_w > 100 and die_h > 100:
            die_img = img[die_y:die_y+die_h,die_x:die_x+die_w]

            detector = cv2.SimpleBlobDetector_create(params)
            dots = detector.detect(die_img)

            number_dots = 0
            if dots is not None:
                # loop through all dot regions of interest found
                for dot_roi in dots:
                    number_dots += 1
                    img = cv2.drawKeypoints(img, dots, np.array([]), (0, 0, 255),cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
                total_number_dots += number_dots

                if number_dots != 0 and number_dots < 7:
                    cv2.drawContours(img, [die_roi], 0, (0,255,0), 3)
                    bbox = cv2.boundingRect(die_roi)
                    img = cv2.putText(img,str(number_dots),
                                    (bbox[0]+bbox[2]+5,bbox[1]+bbox[3]//2),
                                    cv2.FONT_HERSHEY_SIMPLEX,1.5,(0,0,255),3)
                    dice.append(number_dots)
 
    cv2.imshow("Dice Reader", img)
    if dice != oldDice:
        print(dice)
        oldDice = dice
 
    if cv2.waitKey(1) & 0xff == 27:                          # press [Esc] to exit.
        break
 
cv2.destroyAllWindows()