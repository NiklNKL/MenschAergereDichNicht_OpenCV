import cv2
import numpy as np
import math
from ui import Ui


class BoardReader():
    def __init__(self, capId=None, cap = None, useImg=False) -> None:
        ## for testing purposes a single frame can be used
        self.useImg = useImg
        self.frame = None

        ## a VideCapture object could also be used (if multiple instances use the same cap)
        if cap is not None:
            self.cap = cap

        ## otherwise use the device id to create a VideoCapture
        else:
            self.cap = cv2.VideoCapture(capId)
        
        self.get_frame()

    def get_angle(self, a, b, c):
        """
        source: https://stackoverflow.com/questions/58579072/calculate-the-angle-between-two-lines-2-options-and-efficiency
        """
        ## calculate angle between three points a, b and c
        ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
        return ang + 360 if ang < 0 else ang

    def get_playground(self):
        ## preprocessing
        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        upper_red = np.array([255, 90, 90])
        lower_red = np.array([70, 0, 0])
        
        mask = cv2.inRange(rgb, lower_red, upper_red)
        img_with_mask = cv2.bitwise_and(self.frame, self.frame, mask = mask)
        gray_img = cv2.cvtColor(img_with_mask, cv2.COLOR_BGR2GRAY)

        ## contour detection
        contours, _ = cv2.findContours(gray_img, 1, 2)
        # print("Number of contours detected:", len(contours))

        if not len(contours) > 0:
            raise Exception("Could not find a contour")

        ## get second largest square (largest could be border of whole image)
        index, _ = sorted([[index, cv2.contourArea(cnt)] for index, cnt in enumerate(contours)], 
                            key=lambda c: c[1], reverse=True)[1]
        cnt = contours[index]

        """
        ## show all contours
        frame = cv2.drawContours(frame, [contours[index]], -1, (0,255,255), 10)
        cv2.imshow("Shapes", frame)
        cv2.waitKey(0)
        ## show selected contour
        frame = cv2.drawContours(frame, [cnt], -1, (0,255,255), 10)
        cv2.imshow("Shapes", frame)
        cv2.waitKey(0)
        """

        ## define playground borders
        epsilon = 0.01*cv2.arcLength(cnt,True)
        corners = np.squeeze(cv2.approxPolyDP(cnt, epsilon, True), axis=1)

        if not len(corners) == 4:
            raise Exception("could not find four corners of playground")
        
        ## get center of playground
        x = [p[0] for p in corners]
        y = [p[1] for p in corners]
        center = (sum(x) / len(corners), sum(y) / len(corners))

        print("finished playground detection")

        return (corners, center)

    def detect_circles(self, img, corners, center, minR_factor, maxR_factor, fields):
        detected_circles, maxNum = np.array([]), 0

        ## initialize min and max radius with distance relative to the size of the playground
        minR = round(minR_factor * math.dist(corners[0],center))
        maxR = round(maxR_factor * math.dist(corners[0],center))
        ## loop till the minimum radius equals 0 or the required amount of circles is found
        while(minR >= 0):
            print(f"radius: {minR} to {maxR}")
            circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 50,
                                    param1 = 120, param2 = 45,
                                    minRadius = minR, maxRadius = maxR)
            if circles is not None:
                numCircles = circles.shape[1]
                print(f"found {numCircles} circles")

                ## if the required amount of circles is found, return them
                if numCircles == fields:
                    detected_circles = np.squeeze(circles, axis=0)
                    break
                ## else store as many circle as possible for later evaluation
                elif numCircles > maxNum and numCircles < fields:
                    maxNum = numCircles
                    detected_circles = np.squeeze(circles, axis=0)
            else:
                print("could not find any circle")

            ## if not all required circles were found, decrease the minimum radius
            minR -= 5
        return detected_circles

    def get_street(self, corners, center):
        ## preprocessing --> convert to gray for HoughCircles
        blurred = cv2.medianBlur(self.frame, 7)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

        ## find circles in image 
        ## minR_ and maxR_factor are used to define the radius of the searched circles
        ## to calculate the factors =>
        ## radius +- 5 / distance between corner[0] and center of the playing field
        detected_circles = self.detect_circles(gray, corners, center, 
                                                minR_factor=0.044528126006590264, 
                                                maxR_factor=0.05343375120790832, 
                                                fields=40)

        """
        ## show detected fields
        fields = np.uint16(np.around(detected_circles))
        for pt in fields:
            a, b, r = pt[0], pt[1], pt[2]
            # Draw the circumference of the circle.
            cv2.circle(frame, (a, b), r, (0, 255, 0), 20)
            # Draw a small circle (of radius 1) to show the center.
            cv2.circle(frame, (a, b), 10, (0, 0, 255), 3)
        cv2.imshow("frame", frame)
        cv2.waitKey(0)
        """

        ## order by angle
        corner = corners[0]
        angles = []
        for x, y, r in detected_circles:
            angle = self.get_angle(corner, center, (x,y))
            angles.append([angle, x, y, r])
        sortedStreet = sorted(angles,key=lambda c: c[0])
        
        print(f"finished street detection with {len(sortedStreet)}")

        return sortedStreet

    def get_home_and_end(self, corners, center, street, indexOfGreen):
        ## blur
        blurred = cv2.medianBlur(self.frame, 7)

        ## convert to gray scale for HoughCircles
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

        ## detect "street"
        detected_circles = self.detect_circles(gray, corners, center, 
                                                minR_factor=0.0333960945049427, 
                                                maxR_factor=0.03784890710560172, 
                                                fields=32)

        ## order by angle with vector (center->green start)
        green = street[indexOfGreen][1:]
        angles = []
        for x, y, r in detected_circles:
            angle = self.get_angle(green, center, (x,y))
            angles.append([angle, x, y, r])
        sortedStreet = sorted(angles,key=lambda c: c[0])

        ## shift index
        sortedStreet = np.roll(sortedStreet, (4,4,4,4))

        ## get endfields and homefields
        homefields, endfields  = [], []
        for i in range(0,32,8):
            homefield, endfield = [], []

            endfield = sortedStreet[i:i+4]
            ## sort by distance to center
            endfield = sorted(endfield,
                                key=lambda c: math.dist(center, (c[1],c[2])),
                                reverse=True)

            homefield = sortedStreet[i+4:i+8]
            ## top left field is first value and bottom right field is last value
            homefield = np.array(sorted(homefield, key= lambda c: c[1]+c[2]))
            ## set top right field to index 1 if not already, bottom left to index 2 
            if homefield[1][2]>homefield[2][2]:
                homefield[[1,2]]=homefield[[2,1]]

            homefields.append(homefield)
            endfields.append(endfield)

        """
        endfields = np.uint16(np.around(endfields))
        homefields = np.uint16(np.around(homefields))
        for index, color in enumerate(["G","R","B","Y"]):
            homefield = homefields[index]
            endfield = endfields[index]
            for idx, (_, a, b, r) in enumerate(homefield):
            # a, b, r = pt[1], pt[2], pt[3]
            # Draw the circumference of the circle.
                cv2.circle(frame, (a, b), r, (0, 255, 0), 20)
                # Draw a small circle (of radius 1) to show the center.
                cv2.putText(frame, f"H_{color}_{idx}", (a, b),
                    cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 5)
            for idx, (_, a, b, r) in enumerate(endfield):
            # a, b, r = pt[1], pt[2], pt[3]
            # Draw the circumference of the circle.
                cv2.circle(frame, (a, b), r, (0, 255, 0), 20)
                # Draw a small circle (of radius 1) to show the center.
                cv2.putText(frame, f"E_{color}_{idx}", (a, b),
                    cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 5)
        cv2.imshow("frame", frame)
        cv2.waitKey(0)
        """

        print(f"finished non_street detection with {len(sortedStreet)} fields")
        return homefields, endfields

    def identify_green_startingfield(self, street):
        """
        source: https://stackoverflow.com/questions/61516526/how-to-use-opencv-to-crop-circular-image
        """
        ## preprocessing
        imgHSV = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        blurred_houses = cv2.medianBlur(imgHSV, 7)

        ## loop over circles in street list
        for index, (_, x, y, r) in enumerate(street):
            ## create empty mask
            mask = np.zeros_like(self.frame, dtype=np.uint8)
            ## draw circle for current field on mask 
            cv2.circle(mask, (int(x), int(y)), int(r), (255,255,255), -1)
            ## bitwise_and to leave only pixels inside drawn circle
            mask_area = cv2.bitwise_and(blurred_houses, mask)
            
            ## check if pixels in the HSV color range 40-70 (green) are found in masked area
            if self.check_color_in_mask(mask_area, [(40, 100, 100), (70,255,255)]):
                """
                ## show circle containing the green startingfield
                # cv2.imwrite("exports/masks/mask_area"+str(index)+".png", mask_area)
                cv2.imshow("mask", cv2.bitwise_and(cv2.circle(mask,
                    (int(street[index][0]),int(street[index][1])),
                    int(street[index][2]), (255,255,255), -1), frame))
                cv2.waitKey(0)
                """
                print("finished starting field detection")
                return index

        ## return -1 if green wasn't detected
        print("could not identify green starting field")
        return -1

    def check_color_in_mask(self, mask, color):
        ## search for color with inRange
        lower_color = np.array(color[0], dtype=np.uint8)
        upper_color = np.array(color[1], dtype=np.uint8)
        color_mask = cv2.inRange(mask, lower_color, upper_color)
        ## check if any pixels in specified range were found
        return np.sum(color_mask) > 0

    # def highlight_moves(UiHandler, BoardgameHandler, avail_moves):
    #     from mensch_aergere_dich_nicht import Game 
    #     for figure, field in avail_moves:
    #         # _, board = cap.read()
    #         board = UiHandler.boardFrame
    #         normPos = game_logic.normalize_position(figure.player, figure.relPos)

    #         normCord = BoardgameHandler.fields[normPos].imgPos
    #         newCord = BoardgameHandler.fields[field].imgPos
            
    #         board = cv2.arrowedLine(board, normCord, newCord)

    def prepare(self):   
        self.get_frame()

        ## get playground
        while True:
            try:
                corners, center = self.get_playground()
                break
            except Exception as e:
                print(e)

        ## get street
        while True:
            street = self.get_street(corners, center)
            if len(street) == 40:
                break
        
        ## get green starting field
        indexOfGreen = -1
        while indexOfGreen == -1:
            indexOfGreen = self.identify_green_startingfield(street)

        ## get homefields and endfields
        while True:
            homefields, endfields = self.get_home_and_end(corners, center, street, indexOfGreen)
            if len(homefields) == 4:
                break

        return street, indexOfGreen, homefields, endfields

    def get_frame(self):
        # Grab the latest image from the video feed or frame that has been handed over
        if self.useImg == False:
            if self.cap is None:
                self.cap = cv2.VideoCapture(self.capId)
            _, frame = self.cap.read()
        else:
            ## choose frame to use instead of VideoCapture 
            # frame = cv2.imread('brett.png', cv2.IMREAD_COLOR)
            # frame = cv2.imread('data/empty.JPG', cv2.IMREAD_COLOR)
            frame = cv2.imread('data/wRedAndGreen.JPG', cv2.IMREAD_COLOR)
            # frame = cv2.imread('data/wHand.JPG', cv2.IMREAD_COLOR) # <- case that should not work
            # frame = cv2.imread('data/w2fieldsCovered.jpg', cv2.IMREAD_COLOR) # <- case that should not work
        self.frame = frame

    def run(self, UiHandler: Ui):
        self.get_frame()
        UiHandler.update(boardFrame = self.frame)

