# # Quentin Golsteyn Dice Detection
# # https://golsteyn.com/writing/dice

# import cv2
# import numpy as np
# from sklearn import cluster

# class DiceDetector:
#     def __init__(self, capId, cap = None):
#         # Initialize the webcam 
#         if not cap == None:
#             self.cap = cap
#         else:
#             self.cap = cv2.VideoCapture(capId)
#         self.detector = cv2.SimpleBlobDetector_create(self._get_blob_detector_params())
    
#     def _get_blob_detector_params(self):

#         params = cv2.SimpleBlobDetector_Params()

#         params.filterByInertia
#         params.minInertiaRatio = 0.6
#         return(params)

#     def get_blobs(self, frame):
#         frame_blurred = cv2.medianBlur(frame, 7)
#         frame_gray = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2GRAY)
#         blobs = self.detector.detect(frame_gray)

#         return blobs


#     def get_dice_from_blobs(self, blobs):
#         # Get centroids of all blobs
#         X = []
#         for b in blobs:
#             pos = b.pt

#             if pos != None:
#                 X.append(pos)

#         X = np.asarray(X)

#         if len(X) > 0:
#             # Important to set min_sample to 0, as a dice may only have one dot
#             clustering = cluster.DBSCAN(eps=40, min_samples=1).fit(X)

#             # Find the largest label assigned + 1, that's the number of dice found
#             num_dice = max(clustering.labels_) + 1

#             dice = []

#             # Calculate centroid of each dice, the average between all a dice's dots
#             for i in range(num_dice):
#                 X_dice = X[clustering.labels_ == i]

#                 centroid_dice = np.mean(X_dice, axis=0)

#                 dice.append([len(X_dice), *centroid_dice])

#             return dice

#         else:
#             return []


#     def overlay_info(self, frame, dice, blobs):
#         # Overlay blobs
#         for b in blobs:
#             pos = b.pt
#             r = b.size / 2

#             cv2.circle(frame, (int(pos[0]), int(pos[1])),
#                     int(r), (255, 0, 0), 2)

#         # Overlay dice number
#         for d in dice:
#             # Get textsize for text centering
#             textsize = cv2.getTextSize(
#                 str(d[0]), cv2.FONT_HERSHEY_PLAIN, 3, 2)[0]

#             cv2.putText(frame, str(d[0]),
#                         (int(d[1] - textsize[0] / 2),
#                         int(d[2] + textsize[1] / 2)),
#                         cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2)
#         return frame

#     def run(self, UiHandler):
#         # Grab the latest image from the video feed
#         ret, frame = self.cap.read()

#         blobs = self.get_blobs(frame)
#         dice = self.get_dice_from_blobs(blobs)
#         out_frame = self.overlay_info(frame, dice, blobs) 
#         UiHandler.update(diceFrame = out_frame)
#         # cv2.imshow("frame", out_frame)

#         if len(dice) > 0:
#             # print(dice[0][0])
#             return 6
#             return dice[0][0]
#         else:
#             return 0



import cv2

class DiceDetector:
    def __init__(self, capId, cap = None):
        # Initialize the webcam 
        if not cap == None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(capId)
        self.detector = cv2.SimpleBlobDetector_create(self._get_blob_detector_params())
    
    def _get_blob_detector_params(self):

        params = cv2.SimpleBlobDetector_Params()

        params.filterByArea = True
        params.filterByCircularity = True
        params.filterByInertia = True
        params.minThreshold = 10
        params.maxThreshold = 200
        params.minArea = 100
        params.minCircularity = 0.3
        params.minInertiaRatio = 0.5
        return(params)


    def get_dice(self, img):
        edges = cv2.Canny(img,100,500)
    
        die_contours,_ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_number_dots = 0
        for die_roi in die_contours:
            (die_x,die_y,die_w, die_h) = cv2.boundingRect(die_roi)
            if die_w > 100 and die_h > 100:
                die_img = img[die_y:die_y+die_h,die_x:die_x+die_w]
                
                dots = self.detector.detect(die_img)

                number_dots = 0
                if dots is not None:
                    # loop through all dot regions of interest found
                    for dot_roi in dots:
                        number_dots += 1
                        # sind noch nich an der richtigen position
                        # img = cv2.drawKeypoints(img, dots, np.array([]), (0, 0, 255),cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
                    total_number_dots += number_dots

                    if number_dots != 0:
                        cv2.drawContours(img, [die_roi], 0, (0,255,0), 3)
                        bbox = cv2.boundingRect(die_roi)
                        img = cv2.putText(img,str(number_dots),
                                        (bbox[0]+bbox[2]+5,bbox[1]+bbox[3]//2),
                                        cv2.FONT_HERSHEY_SIMPLEX,1.5,(0,0,255),3)
        return img


    def run(self, UiHandler):
        # Grab the latest image from the video feed
        ret, frame = self.cap.read()

       
        out_frame = self.get_dice(frame)
        
        UiHandler.update(diceFrame = out_frame)
        # cv2.imshow("frame", out_frame)

        # if len(dice) > 0:
        #     # print(dice[0][0])
        #     return 6
        #     return dice[0][0]
        # else:
        return 0