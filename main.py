from handler import Handler
from mensch_aergere_dich_nicht import Game
import cv2

if __name__ == "__main__":
    GameHandler = Game()
    LogicHandler = Handler(diceId = 0, gestureId = 0, boardId = 0, game=GameHandler)

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