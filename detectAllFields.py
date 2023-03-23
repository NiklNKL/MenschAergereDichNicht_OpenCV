import cv2
import numpy as np

# Read image.
img = cv2.imread('/Users/jan/Library/CloudStorage/OneDrive-bib&FHDW/Wissenschaftliche Arbeit/2.4 CS/brett.png', cv2.IMREAD_COLOR)


# get current positions of all trackbars
hMin = cv2.getTrackbarPos('HMin','image')
sMin = cv2.getTrackbarPos('SMin','image')
vMin = cv2.getTrackbarPos('VMin','image')

hMax = cv2.getTrackbarPos('HMax','image')
sMax = cv2.getTrackbarPos('SMax','image')
vMax = cv2.getTrackbarPos('VMax','image')

# Set minimum and max HSV values to display
lower = np.array([hMin, sMin, vMin])
upper = np.array([hMax, sMax, vMax])

# invert
inverted = cv2.bitwise_not(img)
# blur
blurred = cv2.medianBlur(inverted, 7)
# convert to gray scale for HoughCircles
gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

# Apply Hough transform on the blurred image.
## detect all circles
# detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50, param1 = 50, param2 = 45, minRadius = 10, maxRadius = 120)

## detect "street"
# detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50, param1 = 50, param2 = 45, minRadius = 50, maxRadius = 120)

## detect "house" for beginning (rectangle) and end (line)
# convert to HSV
imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blurred_houses = cv2.medianBlur(imgHSV, 7)
# ### for red:
# mask = cv2.inRange(blurred_houses, np.array([0, 100, 100]), np.array([10, 255, 255]) )

### for green:
mask = cv2.inRange(blurred_houses, np.array([40, 100, 100]), np.array([70, 255, 255]) )

### for yellow: (not working)
# mask = cv2.inRange(blurred_houses, )

### for black: (not working)
# blurredHouse = cv2.medianBlur(img, 7)
# # grayHouse = cv2.cvtColor(blurredHouse, cv2.COLOR_BGR2GRAY)
# gray = cv2.cvtColor(blurredHouse, cv2.COLOR_BGR2GRAY)
# mask = cv2.inRange(gray, 0, 40)



# # mask = cv2.inRange(blurred_houses, np.array([0, 100, 100]), np.array([10, 255, 255]) )
gray =cv2.bitwise_and(img, img, mask = mask)
# cv2.imshow("Detected Circle", gray)
# # cv2.waitKey(0)

# detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 40, param1 = 100, param2 = 20, minRadius = 30, maxRadius = 40)
detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 40, param1 = 100, param2 = 10, minRadius = 30, maxRadius = 40)
""""""
# Draw circles that are detected.
# if detected_circles is not None:

# Convert the circle parameters a, b and r to integers.
detected_circles = np.uint16(np.around(detected_circles))

for pt in detected_circles[0, :]:
	a, b, r = pt[0], pt[1], pt[2]

	# Draw the circumference of the circle.
	cv2.circle(img, (a, b), r, (0, 255, 0), 2)

	# Draw a small circle (of radius 1) to show the center.
	cv2.circle(img, (a, b), 1, (0, 0, 255), 3)
cv2.imshow("Detected Circle", img)
cv2.waitKey(0)

