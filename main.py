from handler import Handler
from mensch_aergere_dich_nicht import Game
import cv2

diceCam = 0
gestureCam = 0
boardCam = 0

if __name__ == "__main__":

    GameHandler = Game()
    LogicHandler = Handler(diceId = diceCam, gestureId = gestureCam, boardId = boardCam, game=GameHandler)
    UiHandler = LogicHandler.UiHandler

    while True:
        # status = LogicHandler.current_gesture()
        status = GameHandler.play_whole_turn(LogicHandler)

        if cv2.waitKey(1) == ord('q') or status == 1:
            break

    # release the webcam and destroy all active windows
    cv2.VideoCapture(diceCam).release()
    cv2.VideoCapture(gestureCam).release()
    cv2.VideoCapture(boardCam).release()
    cv2.destroyAllWindows()