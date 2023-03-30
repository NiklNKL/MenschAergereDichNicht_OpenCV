import cv2
import math
import numpy as np
from models import Boardgame, Field, Figure, Player

class Prepare:
    def __init__(self, capId = None, cap = None, frame = None):
        self.useImg = False
        # Initialize the webcam 
        if not frame is None:
            self.frame = frame
            self.useImg = True
        elif not cap is None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(capId)
    
    def get_angle(self, a, b, c):
        """
        source: https://stackoverflow.com/questions/58579072/calculate-the-angle-between-two-lines-2-options-and-efficiency
        """
        ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
        return ang + 360 if ang < 0 else ang

    def get_playground(self, frame):
        ## preprocessing
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        upper_red = np.array([255, 90, 90])
        lower_red = np.array([70, 0, 0])
        
        mask = cv2.inRange(rgb, lower_red, upper_red)
        img_with_mask = cv2.bitwise_and(frame, frame, mask = mask)
        gray_img = cv2.cvtColor(img_with_mask, cv2.COLOR_BGR2GRAY)

        ## contour detection
        contours, _ = cv2.findContours(gray_img, 1, 2)
        # print("Number of contours detected:", len(contours))

        if not len(contours) > 0:
            raise Exception("Could not find a contour")

        ## get second largest square (largest could be border of whole image)
        index, area = sorted([[index, cv2.contourArea(cnt)] for index, cnt in enumerate(contours)], key=lambda c: c[1], reverse=True)[1]
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
        corners = np.squeeze(cv2.approxPolyDP(cnt,epsilon,True), axis=1)

        if not len(corners) == 4:
            raise Exception("could not find four corners of playground")
        
        ## get center of playground
        x = [p[0] for p in corners]
        y = [p[1] for p in corners]
        center = (sum(x) / len(corners), sum(y) / len(corners))

        print("finished playground detection")

        return (corners, center)

    def get_street(self, frame, corners, center):
            ## blur
            blurred = cv2.medianBlur(frame, 7)

            ## convert to gray scale for HoughCircles
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

            ## detect "street"
            detected_circles = np.array([])
            maxNum = 0
            ## initialize max and min radius with distance relative to the size of the playground
            minR = round(0.044528126006590264 * math.dist(corners[0],center))
            maxR = round(0.05343375120790832 * math.dist(corners[0],center))
            while(minR >= 0):
                print(f"radius: {minR} to {maxR}")
                circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50, param1 = 120, param2 = 45, minRadius = minR, maxRadius = maxR)
                if circles is not None:
                    numCircles = circles.shape[1]
                    print(f"found {numCircles} circles")

                    if numCircles == 40:
                        detected_circles = np.squeeze(circles, axis=0)
                        break
                    elif numCircles > maxNum and numCircles < 40:
                        maxNum = numCircles
                        detected_circles = np.squeeze(circles, axis=0)
                else:
                    print("could not find any circle")

                minR -= 5

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

    def identify_green_startingfield(self, frame, street):
        """
        source: https://stackoverflow.com/questions/61516526/how-to-use-opencv-to-crop-circular-image
        """
        imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred_houses = cv2.medianBlur(imgHSV, 7)
        for index, (_, x, y, r) in enumerate(street):
            mask = np.zeros_like(frame, dtype=np.uint8)
            cv2.circle(mask, (int(x), int(y)), int(r), (255,255,255), -1)
            mask_area = cv2.bitwise_and(blurred_houses, mask)
            
            if self.check_color_in_mask(mask_area, [(40, 100, 100), (70,255,255)]): # defines green in HSV
                """
                ## show circle containing the green startingfield
                # cv2.imwrite("exports/masks/mask_area"+str(index)+".png", mask_area)
                cv2.imshow("mask", cv2.bitwise_and(cv2.circle(mask, (int(street[index][0]), int(street[index][1])), int(street[index][2]), (255,255,255), -1), frame))
                cv2.waitKey(0)
                """
                print("finished starting field detection")
                return index
        ## return -1 if green wasn't detected
        print("could not identify green starting field")
        return -1

    ## calculate middle between two Fields
    def get_middle(self, a:Field, b:Field):
        ## get x value for middle Field
        x = np.average([a.imgPos[0],b.imgPos[0]])

        ## get y value for middle Field
        y = np.average([a.imgPos[1],b.imgPos[1]])
        
        return Field(imgPos=(x,y), hasFigure=False, streetIndex=-1)
    

    def check_color_in_mask(self, mask, color):
        lower_color = np.array(color[0], dtype=np.uint8)
        upper_color = np.array(color[1], dtype=np.uint8)
        color_mask = cv2.inRange(mask, lower_color, upper_color)
        return np.sum(color_mask) > 0
 
    def create_boardgame(self, street, start):
        BoardgameHandler = Boardgame()

        ## create Field objects (streetIndex range [0,39])
        for index, field in enumerate(street[start:] + street[:start]):
            BoardgameHandler.fields.append(Field(imgPos = field[1:3],
                                                 hasFigure = False,
                                                 streetIndex = index))
        
        ## create Player objects
        startField = 0
        for color in ["green", "red", "black", "yellow"]:
            BoardgameHandler.players.append(Player(color = color,
                                                   startField = startField))
            
            ## create Figure objects for each player (item range [1,4])
            for figureNum in range(1,5):
                BoardgameHandler.figures.append(Figure(relPos = None,
                                                       team = color,
                                                       item = figureNum))
            startField += 10

        ## iterate through all players with their respective startfield index
        for player in BoardgameHandler.players:

            ## get index of first field after start field
            index = player.startField + 1

            ## distance to field on the other side of the endfield
            diff = 4

            endfields = []

            for _ in range(4):
                ## get index of field on the other side of the endfield
                _index = (index-diff)%40
                ## get field objects 
                field = BoardgameHandler.fields[index]
                _field = BoardgameHandler.fields[_index]
                ## endfield is in between the to points
                endfields.append(self.get_middle(field, _field))
                ## index increases by 1 for the next endfield and distance between the opposite street fields increases by two
                index += 1
                diff += 2
            player.set_endfields(endfields)


        print("finished boardgame creation")

        return BoardgameHandler

    def run(self):
        # Grab the latest image from the video feed
        if self.useImg:
            frame = self.frame
        else:
            frameAvailable, frame = self.cap.read()
            if not frameAvailable:
                print("no more frames")
        
        ## get playground
        while True:
            try:
                corners, center = self.get_playground(frame)
                break
            except Exception as e:
                print(e)

        ## get street
        while True:
            detectedCircles = self.get_street(frame, corners, center)
            if len(detectedCircles) == 40:
                break
        
        ## get green starting field
        indexOfGreen = -1
        while indexOfGreen == -1:
            indexOfGreen = self.identify_green_startingfield(frame, detectedCircles)

        ## create boardgame 
        BoardgameHandler = self.create_boardgame(detectedCircles, indexOfGreen)

        ## check if everything was created correctly
        for field in BoardgameHandler.fields:
            print({"imgPos": field.imgPos, "figure": field.hasFigure, "streetIndex": field.streetIndex})
        for player in BoardgameHandler.players:
            print({"color": player.color, "startField": player.startField, "finishField": player.finishField})
        for figure in BoardgameHandler.figures:
            print({"relPos": figure.relPos, "team": figure.team, "item": figure.item})

        print("finished preparations")
        return BoardgameHandler