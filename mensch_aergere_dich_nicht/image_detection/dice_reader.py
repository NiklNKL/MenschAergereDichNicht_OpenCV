# Quentin Golsteyn Dice Detection
# https://golsteyn.com/writing/dice

import cv2
import numpy as np
from sklearn import cluster

class DiceReader:
    def __init__(self, capId, cap = None):
        # Initialize the webcam 
        if not cap == None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(capId)

        _, self.frame = self.cap.read()

        self.detector = cv2.SimpleBlobDetector_create(self._get_blob_detector_params())
    
    def _get_blob_detector_params(self):

        params = cv2.SimpleBlobDetector_Params()

        params.filterByInertia
        params.minInertiaRatio = 0.6
        return(params)

    def get_blobs(self, frame):
        frame_blurred = cv2.medianBlur(frame, 7)
        frame_gray = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2GRAY)
        blobs = self.detector.detect(frame_gray)

        return blobs


    def get_dice_from_blobs(self, blobs):
        # Get centroids of all blobs
        X = []
        for b in blobs:
            pos = b.pt

            if pos != None:
                X.append(pos)

        X = np.asarray(X)

        if len(X) > 0:
            # Important to set min_sample to 0, as a dice may only have one dot
            clustering = cluster.DBSCAN(eps=40, min_samples=1).fit(X)

            # Find the largest label assigned + 1, that's the number of dice found
            num_dice = max(clustering.labels_) + 1

            dice = []

            # Calculate centroid of each dice, the average between all a dice's dots
            for i in range(num_dice):
                X_dice = X[clustering.labels_ == i]

                centroid_dice = np.mean(X_dice, axis=0)

                dice.append([len(X_dice), *centroid_dice])

            return dice

        else:
            return []


    def overlay_info(self, frame, dice, blobs):
        # Overlay blobs
        for b in blobs:
            pos = b.pt
            r = b.size / 2

            cv2.circle(frame, (int(pos[0]), int(pos[1])),
                    int(r), (255, 0, 0), 2)

        # Overlay dice number
        for d in dice:
            # Get textsize for text centering
            textsize = cv2.getTextSize(
                str(d[0]), cv2.FONT_HERSHEY_PLAIN, 3, 2)[0]

            cv2.putText(frame, str(d[0]),
                        (int(d[1] - textsize[0] / 2),
                        int(d[2] + textsize[1] / 2)),
                        cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2)
        return frame

    def run(self, UiHandler):
        # Grab the latest image from the video feed
        _, self.frame = self.cap.read()

        blobs = self.get_blobs(self.frame)
        dice = self.get_dice_from_blobs(blobs)
        out_frame = self.overlay_info(self.frame, dice, blobs) 
        UiHandler.update(diceFrame = out_frame)
        # cv2.imshow("frame", out_frame)

        if len(dice) > 0:
            # print(dice[0][0])
            return 6
            return dice[0][0]
        else:
            return 0