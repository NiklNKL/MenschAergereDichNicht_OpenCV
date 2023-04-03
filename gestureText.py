import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model

# initialize mediapipe
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7)
fingers = mpHands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

# Load the gesture recognizer model
model = load_model('image_detection\handGestureDetect\mp_hand_gesture')

# Load class names
f = open('image_detection\handGestureDetect\gesture.names', 'r')
classNames = f.read().split('\n')
f.close()
print(classNames)

def countFingers(results):
  
    # Initialize a dictionary to store the count of fingers of both hands.
    count = {'RIGHT': 0, 'LEFT': 0}
    
    # Store the indexes of the tips landmarks of each finger of a hand in a list.
    fingers_tips_ids = [mpHands.HandLandmark.INDEX_FINGER_TIP, mpHands.HandLandmark.MIDDLE_FINGER_TIP,
                        mpHands.HandLandmark.RING_FINGER_TIP, mpHands.HandLandmark.PINKY_TIP]
    
    # Initialize a dictionary to store the status (i.e., True for open and False for close) of each finger of both hands.
    fingers_statuses = {'RIGHT_THUMB': False, 'RIGHT_INDEX': False, 'RIGHT_MIDDLE': False, 'RIGHT_RING': False,
                        'RIGHT_PINKY': False, 'LEFT_THUMB': False, 'LEFT_INDEX': False, 'LEFT_MIDDLE': False,
                        'LEFT_RING': False, 'LEFT_PINKY': False}
    
    # Iterate over the found hands in the image.
    for hand_index, hand_info in enumerate(results.multi_handedness):
        
        # Retrieve the label of the found hand.
        hand_label = hand_info.classification[0].label
        
        # Retrieve the landmarks of the found hand.
        hand_landmarks =  results.multi_hand_landmarks[hand_index]
        
        # Iterate over the indexes of the tips landmarks of each finger of the hand.
        for tip_index in fingers_tips_ids:
            
            # Retrieve the label (i.e., index, middle, etc.) of the finger on which we are iterating upon.
            finger_name = tip_index.name.split("_")[0]
            
            # Check if the finger is up by comparing the y-coordinates of the tip and pip landmarks.
            if (hand_landmarks.landmark[tip_index].y < hand_landmarks.landmark[tip_index - 2].y):
                
                # Update the status of the finger in the dictionary to true.
                fingers_statuses[hand_label.upper()+"_"+finger_name] = True
                
                # Increment the count of the fingers up of the hand by 1.
                count[hand_label.upper()] += 1
        
        # Retrieve the y-coordinates of the tip and mcp landmarks of the thumb of the hand.
        thumb_tip_x = hand_landmarks.landmark[mpHands.HandLandmark.THUMB_TIP].x
        thumb_mcp_x = hand_landmarks.landmark[mpHands.HandLandmark.THUMB_TIP - 2].x
        
        # Check if the thumb is up by comparing the hand label and the x-coordinates of the retrieved landmarks.
        if (hand_label=='Right' and (thumb_tip_x < thumb_mcp_x)) or (hand_label=='Left' and (thumb_tip_x > thumb_mcp_x)):
            
            # Update the status of the thumb in the dictionary to true.
            fingers_statuses[hand_label.upper()+"_THUMB"] = True
            
            # Increment the count of the fingers up of the hand by 1.
            count[hand_label.upper()] += 1
    
    # Return the output image, the status of each finger and the count of the fingers up of both hands.
    return count
    


# Initialize the webcam for Hand Gesture Recognition Python project
cap = cv2.VideoCapture(0)

while True:
  # Read each frame from the webcam
    _, frame = cap.read()
    x , y, c = frame.shape

    # Flip the frame vertically
    frame = cv2.flip(frame, 1)

    framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Get hand landmark prediction
    result = hands.process(framergb)
    fingerResult = fingers.process(framergb)

    className = ''

    # post process the result
    if result.multi_hand_landmarks:
        landmarks = []
        for handslms in result.multi_hand_landmarks:
            for lm in handslms.landmark:
                # print(id, lm)
                lmx = int(lm.x * x)
                lmy = int(lm.y * y)

                landmarks.append([lmx, lmy])

            # Drawing landmarks on frames
            mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)
        # Predict gesture in Hand Gesture Recognition project
        prediction = model([landmarks])
        print(prediction)
        classID = np.argmax(prediction)
        className = classNames[classID]

        count = countFingers(fingerResult)

        # show the prediction on the frame
        cv2.putText(frame, className, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2, cv2.LINE_AA)
        
        cv2.putText(frame, "Count: " + str(sum(count.values())), (10, 150), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2, cv2.LINE_AA)

    


    # Show the final output
    cv2.imshow("Output", frame)
    if cv2.waitKey(1) == ord('q'):
                break

# release the webcam and destroy all active windows
cap.release()
cv2.destroyAllWindows()