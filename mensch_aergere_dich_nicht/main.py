from preperation import Preperation
from game import Game
import cv2

def main():
    GameHandler = Game()
    LogicHandler = Preperation(diceId = 0, gestureId = 0, boardId = 0, game=GameHandler)

    while True:
        # status = LogicHandler.current_gesture()
        status = GameHandler.play_whole_turn(LogicHandler)

        if cv2.waitKey(1) == ord('q') or status == 1:
            break

    # release the webcam and destroy all active windows
    cv2.VideoCapture(0).release()
    cv2.VideoCapture(0).release()
    cv2.VideoCapture(0).release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()