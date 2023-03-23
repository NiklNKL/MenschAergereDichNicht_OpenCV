import cv2
import math
import numpy as np
from detectPlayground import get_playground

MINR_AREA_RATIO = 8.670466504392528e-06

def get_angle(a, b, c):
    ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
    return ang + 360 if ang < 0 else ang

def get_street(img, area):
	# blur
	blurred = cv2.medianBlur(img, 7)

	# convert to gray scale for HoughCircles
	gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)


	## detect "street"
	detected_circles = None
	minR = round(MINR_AREA_RATIO * area + 5)
	while(detected_circles is None):
		print(f"radius: {minR}")
		circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50, param1 = 120, param2 = 45, minRadius = minR, maxRadius = 200)
		if circles is not None:
			print(circles.shape)
			if circles.shape[1] == 40:
				detected_circles = circles
				break
		minR -=5
	return np.squeeze(detected_circles, axis=0)

def get_start_fields(corners, center, street):
	
	distances = []
	for index, field in enumerate(street):
		val = math.dist(field[:2],center)
		distances.append([index,val])
	distances = sorted(distances,key=lambda c: c[1])

	corner = corners[0]
	angles = []
	for index, field in distances:
		angle = get_angle(corner, center, field)
		print(angle)
		angles.append([index, angle])
	angles = sorted(angles,key=lambda c: c[1])
	

	
	return distances[-8:]
	


if __name__ == "__main__":
	# Read image.
	img = cv2.imread('data/empty.JPG', cv2.IMREAD_COLOR)

	corners, center, area = get_playground(img)

	street = get_street(img, area)

	fields = get_start_fields(corners, center, street)

	print(len(fields))


	# detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50, param1 = 120, param2 = 45, minRadius = 115, maxRadius = 200)


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
	# detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 40, param1 = 100, param2 = 10, minRadius = 30, maxRadius = 40)
	""""""
	# Draw circles that are detected.
	# if detected_circles is not None:

	# Convert the circle parameters a, b and r to integers.
	street = np.uint16(np.around(street))

	for pt in street[0, :]:
		a, b, r = pt[0], pt[1], pt[2]

		# Draw the circumference of the circle.
		cv2.circle(img, (a, b), r, (0, 255, 0), 20)

		# Draw a small circle (of radius 1) to show the center.
		cv2.circle(img, (a, b), 1, (0, 0, 255), 3)
	cv2.imshow("Detected Circle", img)
	cv2.waitKey(0)
