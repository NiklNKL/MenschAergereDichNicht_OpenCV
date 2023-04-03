import cv2
import math
import numpy as np
from mensch_aergere_dich_nicht import game_logic, Field, Figure, Player

class Prepare:
    def __init__(self, capId = None, cap = None, frame = None):
        self.useImg = False

        ## for testing purposes a single frame can be used
        if not frame is None:
            self.frame = frame
            self.useImg = True
        
        ## a VideCapture object could also be used (if multiple instances use the same cap)
        elif cap is not None:
            self.cap = cap

        ## otherwise use the device id to create a VideoCapture
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

    def detect_circles(self, img, corners, center, minR_factor, maxR_factor, fields):
        ## detect "street"
        detected_circles = np.array([])
        maxNum = 0
        ## initialize max and min radius with distance relative to the size of the playground
        minR = round(minR_factor * math.dist(corners[0],center))
        maxR = round(maxR_factor * math.dist(corners[0],center))
        while(minR >= 0):
            print(f"radius: {minR} to {maxR}")
            circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 50, param1 = 120, param2 = 45, minRadius = minR, maxRadius = maxR)
            if circles is not None:
                numCircles = circles.shape[1]
                print(f"found {numCircles} circles")

                if numCircles == fields:
                    detected_circles = np.squeeze(circles, axis=0)
                    break
                elif numCircles > maxNum and numCircles < fields:
                    maxNum = numCircles
                    detected_circles = np.squeeze(circles, axis=0)
            else:
                print("could not find any circle")

            minR -= 5
        return detected_circles

    def get_street(self, frame, corners, center):
            ## blur
            blurred = cv2.medianBlur(frame, 7)

            ## convert to gray scale for HoughCircles
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

            ## detect "street"
            detected_circles = self.detect_circles(gray, corners, center, minR_factor=0.044528126006590264, maxR_factor=0.05343375120790832, fields=40)

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

    def get_home_and_end(self, frame, corners, center, street, indexOfGreen):
        ## blur
        blurred = cv2.medianBlur(frame, 7)

        ## convert to gray scale for HoughCircles
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

        ## detect "street"
        detected_circles = self.detect_circles(gray, corners, center, minR_factor=0.0333960945049427, maxR_factor=0.03784890710560172, fields=32)

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
            endfield = sorted(endfield, key=lambda c: math.dist(center, (c[1],c[2])), reverse=True)

            homefield = sortedStreet[i+4:i+8]
            ## top left field is first value and bottom right field is last value
            homefield = np.array(sorted(homefield, key= lambda c: c[1]+c[2]))
            ## set top right field to index 1 if not already, bottom left to index 2 
            if homefield[1][2]>homefield[2][2]:
                homefield[[1,2]]=homefield[[2,1]]

            homefields.append(homefield)
            endfields.append(endfield)


        # endfields = np.uint16(np.around(endfields))
        # homefields = np.uint16(np.around(homefields))

        # for index, color in enumerate(["G","R","B","Y"]):
        #     homefield = homefields[index]
        #     endfield = endfields[index]
        #     for idx, (_, a, b, r) in enumerate(homefield):
        #     # a, b, r = pt[1], pt[2], pt[3]
        #     # Draw the circumference of the circle.
        #         cv2.circle(frame, (a, b), r, (0, 255, 0), 20)
        #         # Draw a small circle (of radius 1) to show the center.
        #         cv2.putText(frame, f"H_{color}_{idx}", (a, b), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 5)
        #     for idx, (_, a, b, r) in enumerate(endfield):
        #     # a, b, r = pt[1], pt[2], pt[3]
        #     # Draw the circumference of the circle.
        #         cv2.circle(frame, (a, b), r, (0, 255, 0), 20)
        #         # Draw a small circle (of radius 1) to show the center.
        #         cv2.putText(frame, f"E_{color}_{idx}", (a, b), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 5)

        # cv2.imshow("frame", frame)
        # cv2.waitKey(0)

        print(f"finished non_street detection with {len(sortedStreet)} fields")
        return homefields, endfields
    
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
    
    def check_color_in_mask(self, mask, color):
        lower_color = np.array(color[0], dtype=np.uint8)
        upper_color = np.array(color[1], dtype=np.uint8)
        color_mask = cv2.inRange(mask, lower_color, upper_color)
        return np.sum(color_mask) > 0
 
    def create_boardgame(self, street, start, homefields, endfields):
        ## create Field objects (streetIndex range [0,39])
        for index, field in enumerate(street[start:] + street[:start]):
            game_logic.fields.append(Field(imgPos = field[1:3],
                                           figure = None,
                                           streetIndex = index))
        
        ## create Player objects
        startField = 0
        for index, color in enumerate(["green", "red", "black", "yellow"]):
            game_logic.players.append(Player(color = color,
                                             id = index,
                                             startField = startField))
            
            ## create Figure objects for each player (id range [1,4])
            for figureNum in range(1,5):
                figure = Figure(relPos = None,
                                player = game_logic.players[-1],
                                id = figureNum)
                game_logic.figures.append(figure)
                game_logic.players[-1].figures.append(figure)
            startField += 10
        
        ## move yellow's figure 1 to absPos 6 to test kick logic
        game_logic.players[-1].figures[0].set_position(16)
        game_logic.fields[6].figure = game_logic.players[-1].figures[0]

        ## iterate through all players with their respective startfield index
        for index, player in enumerate(game_logic.players):
            homefield = homefields[index]
            endfield = endfields[index]

            player.set_homefield(homefield)
            player.set_endfield(endfield)


        print("finished boardgame creation")

        # return game_logic

    def run(self):
        # Grab the latest image from the video feed or frame that has been handed over
        if not self.useImg:
            frameAvailable, self.frame = self.cap.read()
            if not frameAvailable:
                print("no more frames")
        
        ## get playground
        while True:
            try:
                corners, center = self.get_playground(self.frame)
                break
            except Exception as e:
                print(e)

        ## get street
        while True:
            street = self.get_street(self.frame, corners, center)
            if len(street) == 40:
                break
        
        ## get green starting field
        indexOfGreen = -1
        while indexOfGreen == -1:
            indexOfGreen = self.identify_green_startingfield(self.frame, street)

        ## get homefields and endfields
        while True:
            homefields, endfields = self.get_home_and_end(self.frame, corners, center, street, indexOfGreen)
            if len(homefields) == 4:
                break
        ## create boardgame 
        self.create_boardgame(street, indexOfGreen, homefields, endfields)

        ## check if everything was created correctly
        for field in game_logic.fields:
            print({"imgPos": field.imgPos, "figure": field.figure, "streetIndex": field.streetIndex})
        for player in game_logic.players:
            print({"color": player.color, "startField": player.startField, "finishField": player.finishField})
        for figure in game_logic.figures:
            print({"relPos": figure.relPos, "team": figure.player, "item": figure.id})
        print("finished preparations")
    
### testing main
    
# if __name__ == "__main__":

#      useImg = False

#      if useImg:
#          # frame = cv2.imread('brett.png', cv2.IMREAD_COLOR)
#          # frame = cv2.imread('data/empty.JPG', cv2.IMREAD_COLOR)
#          frame = cv2.imread('data/wRedAndGreen.JPG', cv2.IMREAD_COLOR)
#          # frame = cv2.imread('data/wHand.JPG', cv2.IMREAD_COLOR) # <- case that should not work
#          # frame = cv2.imread('data/w2fieldsCovered.jpg', cv2.IMREAD_COLOR) # <- case that should not work
#          PrepareHandler = Prepare(frame = frame)
#      else:
#          capId = 0
#          cap = cv2.VideoCapture(capId)
#          # PrepareHandler = Prepare(capId = capId)
#          PrepareHandler = Prepare(cap = cap)

#      game_logic = PrepareHandler.run()

#      # release the webcam and destroy all active windows
#      if not useImg:
#          cv2.VideoCapture(capId).release()