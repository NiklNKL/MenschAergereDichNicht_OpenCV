from game import Game
from image_detection import HandReader, DiceReader, BoardReader
import cv2
from ui import Ui
from time import time

def main():

    diceCameraId = 1
    handCameraId = 1
    boardCameraId = 1

    # Nur wichtig, wenn wir alles über eine Kamera laufen lassen
    cap = cv2.VideoCapture(diceCameraId)

    DiceThread = DiceReader(capId=diceCameraId, cap=cap)
    HandThread = HandReader(capId=handCameraId, timeThreshold = 2, cap=cap)
    BoardThread = BoardReader(cap=cap, useImg=True)
    GameThread = Game(DiceThread, HandThread, BoardThread)
    UiThread = Ui(GameThread, DiceThread, HandThread, BoardThread)
    print("Starting threads...")
    DiceThread.start()
    HandThread.start()
    BoardThread.start()
    while not (DiceThread.initialized and HandThread.initialized and BoardThread.initialized):
        pass
    print("Initialisation part 1: Success")

    GameThread.start()
    
    while not GameThread.initialized:
        pass

    print("Initialisation part 2: Success")

    UiThread.start()

    print("Initialisation part 3: Success")

    while True:
        # status = LogicHandler.current_gesture()
        status = GameThread.status
        if cv2.waitKey(1) == ord('q') or status == -1:

            UiThread.stop()
            GameThread.stop()
            DiceThread.stop()
            HandThread.stop()
            BoardThread.stop()
            break

    # release the webcam and destroy all active windows
    cv2.VideoCapture(diceCameraId).release()
    cv2.VideoCapture(handCameraId).release()
    cv2.VideoCapture(boardCameraId).release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()