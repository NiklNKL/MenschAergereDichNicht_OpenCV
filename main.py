from handler import Handler
from mensch_aergere_dich_nicht import game_logic
import cv2

if __name__ == "__main__":
    ## choose frame to use instead of VideoCapture 
    # frame = cv2.imread('brett.png', cv2.IMREAD_COLOR)
    # frame = cv2.imread('data/empty.JPG', cv2.IMREAD_COLOR)
    frame = cv2.imread('data/wRedAndGreen.JPG', cv2.IMREAD_COLOR)
    # frame = cv2.imread('data/wHand.JPG', cv2.IMREAD_COLOR) # <- case that should not work
    # frame = cv2.imread('data/w2fieldsCovered.jpg', cv2.IMREAD_COLOR) # <- case that should not work

    LogicHandler = Handler(diceId = 0, gestureId = 0, boardId = 0, boardFrame=frame)
    UIHandler = LogicHandler.UIHandler

    while True:
        # status = LogicHandler.current_gesture()
        status = game_logic.play_whole_turn(LogicHandler)

        if cv2.waitKey(1) == ord('q') or status == 1:
            break

    # release the webcam and destroy all active windows
    cv2.VideoCapture(0).release()
    cv2.VideoCapture(0).release()
    cv2.VideoCapture(0).release()
    cv2.destroyAllWindows()