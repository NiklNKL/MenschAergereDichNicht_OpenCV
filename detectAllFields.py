import cv2
import math
import numpy as np

MINR_AREA_RATIO = 8.670466504392528e-06

def get_angle(a, b, c):
	"""
	source: https://stackoverflow.com/questions/58579072/calculate-the-angle-between-two-lines-2-options-and-efficiency
	"""
	ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
	return ang + 360 if ang < 0 else ang

def get_playground(img):
	## preprocessing
	# img = cv2.imread('data/empty.JPG')
	rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	upper_red = np.array([255, 70, 70])
	lower_red = np.array([100, 0, 0])

	mask = cv2.inRange(rgb, lower_red, upper_red)
	img_with_mask = cv2.bitwise_and(img, img, mask = mask)
	gray_img = cv2.cvtColor(img_with_mask, cv2.COLOR_BGR2GRAY)

	## contour detection
	contours, _ = cv2.findContours(gray_img, 1, 2)
	print("Number of contours detected:", len(contours))

	if len(contours) > 0:
		## get second largest square (largest is border of image)
		index, area = sorted([[index, cv2.contourArea(cnt)] for index, cnt in enumerate(contours)], reverse=True)[1]
		cnt = contours[index]

		## define playground borders
		epsilon = 0.01*cv2.arcLength(cnt,True)
		corners = np.squeeze(cv2.approxPolyDP(cnt,epsilon,True), axis=1)

		## get center of playground
		x = [p[0] for p in corners]
		y = [p[1] for p in corners]
		center = (sum(x) / len(corners), sum(y) / len(corners))

		return (corners, center, area)
	else:
		return ([], (), 0.0)


def get_street(img, area):
	## blur
	blurred = cv2.medianBlur(img, 7)

	## convert to gray scale for HoughCircles
	gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

	## detect "street"
	detected_circles = np.array([])
	minR = 26#round(MINR_AREA_RATIO * area + 5)
	while(detected_circles.size == 0 and minR >= 0):
		print(f"radius: {minR}")
		circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50, param1 = 120, param2 = 45, minRadius = minR, maxRadius = 35)
		if circles is not None:
			print(circles.shape)
			if circles.shape[1] <= 40:
				detected_circles = circles
				break
		minR -=5
	return np.squeeze(detected_circles, axis=0)

def get_start_fields(corners, center, street):
	start_fields = []
	for corner in corners:
		distances = []
		for index, field in enumerate(street):
			val = math.dist(field[:2],corner)
			distances.append([index, val])
		distances = sorted(distances, key=lambda c: c[1])
		start_fields.extend(distances[:2])
			
	print(start_fields)
	corner = corners[0]
	angles = []
	for index, field in start_fields:
		angle = get_angle(corner, center, street[index])
		print(angle)
		angles.append([index, angle])
	angles = sorted(angles,key=lambda c: c[1])

	unwanted = [0,2,4,6]
	for ele in sorted(unwanted, reverse = True): 
		del angles[ele]

	return [street[index] for index, angle in angles]

if __name__ == "__main__":
	# Read image.
	img = cv2.imread('data/empty.JPG', cv2.IMREAD_COLOR)
	cap = cv2.VideoCapture(0)
	while True:
		frameAvailable, frame = cap.read() # ließt das nächste Frame ein
		if not frameAvailable:
			print("no more frames")
			break

		corners, center, area = get_playground(frame)

		if len(corners) > 0 and area > 0.0:
			street = get_street(frame, area)
			if len(street) == 40:
				fields = get_start_fields(corners, center, street)

				print(len(fields))

				# Convert the circle parameters a, b and r to integers.
				fields = np.uint16(np.around(fields))

				for pt in fields:
				# for pt in fields[0, :]:
					a, b, r = pt[0], pt[1], pt[2]

					# Draw the circumference of the circle.
					cv2.circle(frame, (a, b), 20, (0, 255, 0), 20)

					# Draw a small circle (of radius 1) to show the center.
					cv2.circle(frame, (a, b), 1, (0, 0, 255), 3)

		cv2.imshow("frame", frame)

		if cv2.waitKey(1) & 0xFF == ord("q"):
			break

	cap.release()
	cv2.destroyAllWindows()

	# cv2.imshow("Detected Circle", img)
	# cv2.waitKey(0)


"""
Erkenntnisse:
- Playground ausführen nur am Anfang
- street detection auch mit figuren realtiv zuverlässig
- camera feed full-hd deshalb hardcoded bisher 
- robuster programmieren, damit auch wenn nicht die nötigen Sachen gefunden werden das Programm weriterläuft.
- 
"""
