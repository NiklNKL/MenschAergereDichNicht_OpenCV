import cv2
import numpy as np

#Detect Playground
img = cv2.imread('data/empty.JPG')
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
upper_red = np.array([255, 70, 70])
lower_red = np.array([100, 0, 0])

mask = cv2.inRange(rgb, lower_red, upper_red)
img_with_mask = cv2.bitwise_and(img, img, mask = mask)
cv2.imshow("IMG",img_with_mask)
cv2.waitKey(0)

gray_img = cv2.cvtColor(img_with_mask, cv2.COLOR_BGR2GRAY)

contours, hierarchy = cv2.findContours(gray_img, 1, 2)
print("Number of contours detected:", len(contours))

index, area = sorted([[index, cv2.contourArea(cnt)] for index, cnt in enumerate(contours)], reverse=True)[1]

# Get Center
cnt = contours[index]

# define main island contour approx. and hull
perimeter = cv2.arcLength(cnt,True)
epsilon = 0.01*cv2.arcLength(cnt,True)
approx = cv2.approxPolyDP(cnt,epsilon,True)

cv2.drawContours(img, [approx], -1, (0, 0, 255), 6)

cv2.imshow("Contour", img)
cv2.waitKey(0)
