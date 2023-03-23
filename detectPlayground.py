import cv2
import numpy as np
"""
Detect Playground
"""
## preprocessing
img = cv2.imread('data/empty.JPG')
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
upper_red = np.array([255, 70, 70])
lower_red = np.array([100, 0, 0])

mask = cv2.inRange(rgb, lower_red, upper_red)
img_with_mask = cv2.bitwise_and(img, img, mask = mask)
gray_img = cv2.cvtColor(img_with_mask, cv2.COLOR_BGR2GRAY)

## contour detection
contours, hierarchy = cv2.findContours(gray_img, 1, 2)
print("Number of contours detected:", len(contours))

## get second largest square (largest is border of image)
index, area = sorted([[index, cv2.contourArea(cnt)] for index, cnt in enumerate(contours)], reverse=True)[1]
cnt = contours[index]

## define playground borders
perimeter = cv2.arcLength(cnt,True)
epsilon = 0.01*cv2.arcLength(cnt,True)
approx = cv2.approxPolyDP(cnt,epsilon,True)

## get center of playground
x = [p[0][0] for p in approx]
y = [p[0][1] for p in approx]
center = (sum(x) / len(approx), sum(y) / len(approx))
