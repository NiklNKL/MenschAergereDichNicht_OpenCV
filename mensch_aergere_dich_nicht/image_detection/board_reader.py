import cv2
import numpy as np
import math
import threading
import time

class BoardReader(threading.Thread):
    def __init__(self, cap, use_img=False) -> None:
        """
        Initialises a BoardReader object
        
        Args:
        cap: cv2.VideoCapture object or any other object with a frame attribute
        use_img: bool, whether to use an image instead of capturing video input
        """
        threading.Thread.__init__(self)
        # Initialising of the videocapture
        
        self.cap = cap
        
        self.frame = self.cap.frame

        ## for testing purposes a single frame can be used
        self.use_img = use_img
        if self.use_img:
            self.frame = cv2.imread('mensch_aergere_dich_nicht/resources/images/test/reallife_frame.jpg', cv2.IMREAD_COLOR)
        
        self.street = None
        self.index_of_green =  None
        self.home_fields = None
        self.end_fields = None
        self.corners = None

        self.initialized = False

        self._stop_event = threading.Event()

    def get_angle(self, a, b, c):
        """
        Calculates the angle between two lines (a,b) and (b,c).
        
        Args:
        a: tuple, (x,y) coordinates of point a
        b: tuple, (x,y) coordinates of point b
        c: tuple, (x,y) coordinates of point c
        
        Returns:
        ang: float, the angle between the two lines in degrees
        """
        ## calculate angle between three points a, b and c
        ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
        return ang + 360 if ang < 0 else ang

    def get_playground(self):
        """
        Detects the playground borders from the frame.
        
        Returns:
        tuple:
            corners: np.array, an array of 4 tuples of (x,y) coordinates of the corners of the playground
            center: tuple, (x,y) coordinates of the center of the playground
        """
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

        ## top left field is first value and bottom right field is last value
        corners = np.array(sorted(corners, key= lambda c: c[0]+c[1]))
        ## set top right field to index 1 if not already, bottom left to index 2 
        if corners[1][1]>corners[2][1]:
            corners[[1,2]]=corners[[2,1]]
        print(f"setting corners. No. of corners: {len(corners)}")
        self.corners = corners

        if not len(corners) == 4:
            raise Exception("Could not find four corners of playground")
        
        ## get center of playground
        x = [p[0] for p in corners]
        y = [p[1] for p in corners]
        center = (sum(x) / len(corners), sum(y) / len(corners))

        print("Finished playground detection")

        return (corners, center)

    def detect_circles(self, img, corners, center, minR_factor, maxR_factor, fields):
        """
        Detects circles in an image.

        Args:
        img: The input image.
        corners: The four corners of the board.
        center: The center of the board.
        minR_factor: The minimum radius of the circles relative to the distance between the first corner and the center of the board.
        maxR_factor: The maximum radius of the circles relative to the distance between the first corner and the center of the board.
        fields: The number of circles to be detected.

        Returns:
        An array of circles, where each circle is represented by its center coordinates and its radius.
        """
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
        """
        Detects the playing field in the input image.

        Args:
        corners: The four corners of the board.
        center: The center of the board.

        Returns:
        A sorted list of circles, where each circle is represented by its angle, its center coordinates and its radius.
        """
        
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
        
        print(f"Finished street detection with {len(sortedStreet)}")

        return sortedStreet

    def get_home_and_end(self, corners, center, street, index_of_green):
        """
        Detects and returns the home and end fields for each player using HoughCircles and image processing techniques.

        Args:
        corners: list of corner coordinates (x, y) in the board image
        center: tuple representing the center point of the board image
        street: list of fields on the board (x, y, radius) sorted by angle with vector (center->green start)
        index_of_green: the index of the field that contains the green starting piece

        Returns:
        home_fields: a list of four lists, each containing 4 tuples representing the fields on each player's home
        end_fields: a list of four lists, each containing 4 tuples representing the fields on each player's end
        """
        ## blur
        blurred = cv2.medianBlur(self.frame, 7)

        ## convert to gray scale for HoughCircles
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

        ## detect "street"
        detected_circles = self.detect_circles(gray, corners, center, 
                                                minR_factor=0.0333960945049427, 
                                                maxR_factor=0.04, 
                                                fields=32)
        
        ## order by angle with vector (center->green start)
        green = street[index_of_green][1:]
        angles = []
        for x, y, r in detected_circles:
            angle = self.get_angle(green, center, (x,y))
            angles.append([angle, x, y, r])
        sortedStreet = sorted(angles,key=lambda c: c[0])

        ## shift index
        sortedStreet = np.roll(sortedStreet, (4,4,4,4))

        ## get end_fields and home_fields
        home_fields, end_fields  = [], []
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

            home_fields.append(homefield)
            end_fields.append(endfield)

        
        # end_fields = np.uint16(np.around(end_fields))
        # home_fields = np.uint16(np.around(home_fields))
        # for index, color in enumerate(["G","R","B","Y"]):
        #     homefield = home_fields[index]
        #     endfield = end_fields[index]
        #     for idx, (_, a, b, r) in enumerate(homefield):
        #     # a, b, r = pt[1], pt[2], pt[3]
        #     # Draw the circumference of the circle.
        #         cv2.circle(self.frame, (a, b), r, (0, 255, 0), 20)
        #         # Draw a small circle (of radius 1) to show the center.
        #         cv2.putText(self.frame, f"H_{color}_{idx}", (a, b),
        #             cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 5)
        #     for idx, (_, a, b, r) in enumerate(endfield):
        #     # a, b, r = pt[1], pt[2], pt[3]
        #     # Draw the circumference of the circle.
        #         cv2.circle(self.frame, (a, b), r, (0, 255, 0), 20)
        #         # Draw a small circle (of radius 1) to show the center.
        #         cv2.putText(self.frame, f"E_{color}_{idx}", (a, b),
        #             cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 5)
        
        # cv2.waitKey(0)
        

        print(f"Finished non_street detection with {len(sortedStreet)} fields")
        return home_fields, end_fields

    def identify_green_startingfield(self, street):
        """
        Identifies the starting field for the green player on the board by applying image processing techniques.

        Args:
        street: list of fields on the board (x, y, radius) sorted by angle with vector (center->green start)

        Returns:
        tuple representing the starting field for the green player (x, y, radius)
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
            if self.check_color_in_mask(mask_area, [(35, 40, 40), (120,255,255)]):
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

    def stop(self):
        """
        Sets the event to stop the thread.
        """
        self._stop_event.set()

    def stopped(self):
        """
        Returns a boolean indicating whether the thread has stopped.
        """
        return self._stop_event.is_set()


    def run(self):
        """
        Starts the thread and runs the methods to detect the board and fields.
        """
        self.temp_frame = self.cap.frame
        ## get playground
        print("\nStarting playground detection...")
        while True and not self.initialized:
            try:
                corners, center = self.get_playground()
                break
            except Exception as e:
                print(e)

        ## get street
        print("\nStarting street detection...")
        while True and not self.initialized:   
            self.street = self.get_street(corners, center)
            if len(self.street) == 40:
                break
        
        ## get green starting field
        print("\nStarting non-street detection...")
        self.index_of_green = -1
        while self.index_of_green == -1:
            self.index_of_green = self.identify_green_startingfield(self.street)

        ## get home_fields and end_fields
        while True and not self.initialized:
            self.home_fields, self.end_fields = self.get_home_and_end(corners, center, self.street, self.index_of_green)
            if len(self.home_fields) == 4:
                break
        self.initialized = True
        while True:
            pass
            if self.stopped():
                break

