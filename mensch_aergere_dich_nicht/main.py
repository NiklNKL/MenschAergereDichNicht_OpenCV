from preperation import Preperation
from game import Game
import cv2

diceCameraId = 1
handCameraId = 1
boardCameraId = 1

def main():
    GameHandler = Game()
    LogicHandler = Preperation(diceId = diceCameraId, handId = handCameraId, boardId = boardCameraId, game=GameHandler)

    while True:
        # status = LogicHandler.current_gesture()
        status = GameHandler.play_whole_turn(LogicHandler)

        if cv2.waitKey(1) == ord('q') or status == 1:
            break

    # release the webcam and destroy all active windows
    cv2.VideoCapture(diceCameraId).release()
    cv2.VideoCapture(handCameraId).release()
    cv2.VideoCapture(boardCameraId).release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()