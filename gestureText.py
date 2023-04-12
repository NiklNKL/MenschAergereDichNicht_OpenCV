import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model
from time import time

# initialize mediapipe
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7)
fingers = mpHands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

videoFeed = "gesture"

timeThreshold = 2

currentClass = ''
previousClass = ''
class_time_without_change = 0
class_last_update_time = time()

currentCount = ''
previousCount = ''
count_time_without_change = 0
count_last_update_time = time()

# Load the gesture recognizer model
model = load_model('image_detection\handGestureDetect\mp_hand_gesture')

# Load class names
f = open('image_detection\handGestureDetect\gesture.names', 'r')
classNames = f.read().split('\n')
f.close()

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
    if results.multi_handedness is not None:
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
    return count, fingers_statuses

def annotate(image, results, fingers_statuses, count):
    '''
    This function will draw an appealing visualization of each fingers up of the both hands in the image.
    Args:
        image:            The image of the hands on which the counted fingers are required to be visualized.
        results:          The output of the hands landmarks detection performed on the image of the hands.
        fingers_statuses: A dictionary containing the status (i.e., open or close) of each finger of both hands. 
        count:            A dictionary containing the count of the fingers that are up, of both hands.
        display:          A boolean value that is if set to true the function displays the resultant image and 
                          returns nothing.
    Returns:
        output_image: A copy of the input image with the visualization of counted fingers.
    '''
    
    # Get the height and width of the input image.
    height, width, _ = image.shape
    
    # Create a copy of the input image.
    output_image = image.copy()
    
    # Select the images of the hands prints that are required to be overlayed.
    ########################################################################################################################
    
    # Initialize a dictionaty to store the images paths of the both hands.
    # Initially it contains red hands images paths. The red image represents that the hand is not present in the image. 
    HANDS_IMGS_PATHS = {'LEFT': ["image_detection/fingerMedia/left_hand_not_detected.png"], 'RIGHT': ['image_detection/fingerMedia/right_hand_not_detected.png']}
    
    # Check if there is hand(s) in the image.
    if results.multi_hand_landmarks:
        
        # Iterate over the detected hands in the image.
        for hand_index, hand_info in enumerate(results.multi_handedness):
            
            # Retrieve the label of the hand.
            hand_label = hand_info.classification[0].label
            
            # Update the image path of the hand to a green color hand image.
            # This green image represents that the hand is present in the image. 
            HANDS_IMGS_PATHS[hand_label.upper()] = ['image_detection/fingerMedia/'+hand_label.lower()+'_hand_detected.png']
            
            # Check if all the fingers of the hand are up/open.
            if count[hand_label.upper()] == 5:
                
                # Update the image path of the hand to a hand image with green color palm and orange color fingers image.
                # The orange color of a finger represents that the finger is up.
                HANDS_IMGS_PATHS[hand_label.upper()] = ['image_detection/fingerMedia/'+hand_label.lower()+'_all_fingers.png']
            
            # Otherwise if all the fingers of the hand are not up/open.
            else:
                
                # Iterate over the fingers statuses of the hands.
                for finger, status in fingers_statuses.items():
                    
                    # Check if the finger is up and belongs to the hand that we are iterating upon.
                    if status == True and finger.split("_")[0] == hand_label.upper():
                        
                        # Append another image of the hand in the list inside the dictionary.
                        # This image only contains the finger we are iterating upon of the hand in orange color.
                        # As the orange color represents that the finger is up.
                        HANDS_IMGS_PATHS[hand_label.upper()].append('image_detection/fingerMedia/'+finger.lower()+'.png')
    
    ########################################################################################################################
    
    # Overlay the selected hands prints on the input image.
    ########################################################################################################################
    
    # Iterate over the left and right hand.
    for hand_index, hand_imgs_paths in enumerate(HANDS_IMGS_PATHS.values()):
        
        # Iterate over the images paths of the hand.
        for img_path in hand_imgs_paths:
            
            # Read the image including its alpha channel. The alpha channel (0-255) determine the level of visibility. 
            # In alpha channel, 0 represents the transparent area and 255 represents the visible area.
            hand_imageBGRA = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            hand_imageBGRA = cv2.resize(hand_imageBGRA, (100,100), interpolation=cv2.INTER_LINEAR)
            
            # Retrieve all the alpha channel values of the hand image. 
            alpha_channel = hand_imageBGRA[:,:,-1]
            
            # Retrieve all the blue, green, and red channels values of the hand image.
            # As we also need the three-channel version of the hand image. 
            hand_imageBGR  = hand_imageBGRA[:,:,:-1]
            
            # Retrieve the height and width of the hand image.
            hand_height, hand_width, _ = hand_imageBGR.shape

            # Retrieve the region of interest of the output image where the handprint image will be placed.
            ROI = output_image[30 : 30 + hand_height,
                               (hand_index * width//2) + width//12 : ((hand_index * width//2) + width//12 + hand_width)]
            
            # Overlay the handprint image by updating the pixel values of the ROI of the output image at the 
            # indexes where the alpha channel has the value 255.
            ROI[alpha_channel==255] = hand_imageBGR[alpha_channel==255]

            # Update the ROI of the output image with resultant image pixel values after overlaying the handprint.
            output_image[30 : 30 + hand_height,
                         (hand_index * width//2) + width//12 : ((hand_index * width//2) + width//12 + hand_width)] = ROI
    
    return output_image

def getGesture(result, frame):
    className = ""
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
        classID = np.argmax(prediction)
        className = classNames[classID]
         # show the prediction on the frame
        cv2.putText(frame, "Gesture: " + className, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2, cv2.LINE_AA)
    else:
        cv2.putText(frame, "Waiting for Gesture...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2, cv2.LINE_AA)
    return className, frame
     
def getFingers(result, frame):
    count = 0
    # post process the result
    if result.multi_hand_landmarks:
        for handslms in result.multi_hand_landmarks:
            # Drawing landmarks on frames
            mpDraw.draw_landmarks(frame, handslms,mpHands.HAND_CONNECTIONS,
                                    landmark_drawing_spec=mpDraw.DrawingSpec(color=(255,255,255),
                                                                                   thickness=2, circle_radius=2),
                                    connection_drawing_spec=mpDraw.DrawingSpec(color=(0,255,0),
                                                                                     thickness=2, circle_radius=2))
        count, fingers_statuses = countFingers(result)
        frame = annotate(frame, result,fingers_statuses, count)
        count = sum(count.values())
        # show the prediction on the frame
        cv2.putText(frame, "Count: " + str(count), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2, cv2.LINE_AA)
    else:
        cv2.putText(frame, "Waiting for Fingercount...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2, cv2.LINE_AA)
    return count, frame

def update_class(className):
    # Wenn sich der Klassenname geändert hat, setze die Zeit ohne Änderung auf 0 zurück und aktualisiere previousClass
    if className != previousClass:
        previousClass = className
        time_without_change = 0
        if className == '':
            currentClass = className
    else:
        # Andernfalls erhöhe die Zeit ohne Änderung um die vergangene Zeit seit dem letzten Update
        time_without_change += time() - last_update_time

    last_update_time = time()
    # Wenn die Zeit ohne Änderung größer als timeThreshold Sekunden ist, aktualisiere das Bild
    if time_without_change >= timeThreshold:
        # Hier kann der aktuelle Wert der Variable abgerufen werden
        current_value = className
        # Setze die letzte Aktualisierungszeit auf die aktuelle Zeit
        # self.last_update_time = time.time()
        currentClass = current_value
        
        # Speichere die letzte Aktualisierungszeit
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
    count = 0

    if videoFeed == "gesture":
        className, newFrame = getGesture(result, frame)
    elif videoFeed == "counter":
        count, newFrame = getFingers(fingerResult, frame)

    if cv2.waitKey(1) == ord('w'):
                if videoFeed == "gesture":
                     videoFeed = "counter"
                else:
                     videoFeed = "gesture"

    # Show the final output

    update_class(className)
    # cv2.putText(newFrame, "Detected Gesture: " + currentClass, (10, 80), cv2.FONT_HERSHEY_SIMPLEX,
    #                     1, (0,0,255), 2, cv2.LINE_AA)
    cv2.imshow("Output", newFrame)
    
    if cv2.waitKey(2) == ord('q'):
                break

# release the webcam and destroy all active windows
cap.release()
cv2.destroyAllWindows()