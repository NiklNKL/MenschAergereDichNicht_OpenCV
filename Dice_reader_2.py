import cv2
import numpy as np
from sklearn import cluster
import mediapipe as mp

params = cv2.SimpleBlobDetector_Params()

params.filterByInertia
params.minInertiaRatio = 0.6

detector = cv2.SimpleBlobDetector_create(params)

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

def get_blobs(frame):
    frame_blurred = cv2.medianBlur(frame, 7)
    frame_rgb = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2RGB)  # Change color space to RGB
    blobs = detector.detect(frame_rgb)

    return blobs


def get_dice_from_blobs(blobs):
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


def overlay_info(frame, dice, blobs, hand_closed):
    # Overlay blobs
    for b in blobs:
        pos = b.pt
        r = b.size / 2

        if hand_closed:
            cv2.circle(frame, (int(pos[0]), int(pos[1])),
                   int(r), (0, 0, 0), 2)
        else:
            cv2.circle(frame, (int(pos[0]), int(pos[1])),
                   int(r), (255, 0, 0), 2)
        

    # Overlay dice number
    for d in dice:
        # Get textsize for text centering
        textsize = cv2.getTextSize(
            str(d[0]), cv2.FONT_HERSHEY_PLAIN, 3, 2)[0]
        
        # Set color of text based on hand state
        if hand_closed:
            color = (255, 255, 0)  # yellow
        else:
            color = (0, 255, 0)  # green

        cv2.putText(frame, str(d[0]),
                    (int(d[1] - textsize[0] / 2),
                     int(d[2] + textsize[1] / 2)),
                    cv2.FONT_HERSHEY_PLAIN, 3, color, 2)
    return frame


# Initialize a video feed
cap = cv2.VideoCapture(0)

hand_closed = False

while(True):
    # Grab the latest image from the video feed
    ret, frame = cap.read()

    # We'll define these later
    blobs = get_blobs(frame)
    dice = get_dice_from_blobs(blobs)
    out_frame = overlay_info(frame, dice, blobs, hand_closed)

    res = cv2.waitKey(1)

    # Stop if the user presses "q"
    if res & 0xFF == ord('q'):
        break

    result = hands.process(frame)

    if result.multi_hand_landmarks:
        for handLandmarks in result.multi_hand_landmarks:
            mpDraw.draw_landmarks(frame, handLandmarks, mpHands.HAND_CONNECTIONS)

            # Get the position of the tip of the index finger and the palm
            index_tip = handLandmarks.landmark[8]
            palm = handLandmarks.landmark[0]

            # Calculate the distance between the tip of the index finger and the palm
            dist = ((index_tip.x - palm.x)**2 + (index_tip.y - palm.y)**2)**0.5

        for lmId, lm in enumerate(handLandmarks.landmark):
                if lmId == 4:
                    h, w, _ = frame.shape
                    if lm.y < handLandmarks.landmark[2].y:  # check if fist is closed
                        hand_closed = True
                    else:
                        hand_closed = False
    
    cv2.imshow("frame", out_frame)

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()
