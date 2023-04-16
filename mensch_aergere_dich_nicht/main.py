from game import Game
from image_detection import HandReader, DiceReader, BoardReader
import cv2
from ui import Ui
from utilities import VideoStream
from utilities import GameStatus
import time

def main():

    dice_camera_id = 1
    hand_camera_id = 1
    board_camera_id = 1

    print("\nStarting threads...")

    start_time = time.time()

    # Nur wichtig, wenn wir alles über eine Kamera laufen lassen
    if dice_camera_id == hand_camera_id == board_camera_id:
        cap = VideoStream(dice_camera_id)
        cap.name = "VideoStreamThread"
        cap.start()
        dice_cap = cap
        hand_cap = cap
        board_cap = cap
    else:
        dice_cap = VideoStream(dice_camera_id)
        dice_cap.name = "DiceCamThread"
        hand_cap = VideoStream(hand_camera_id)
        hand_cap.name = "HandCamThread"
        board_cap = VideoStream(board_camera_id)
        board_cap.name = "BoardCamThread"

        dice_cap.start()
        hand_cap.start()
        board_cap.start()

    if dice_camera_id == hand_camera_id == board_camera_id:
        while not cap.initialized:
            pass
    else:
        while not (dice_cap.initialized and hand_cap.initialized and board_cap.initialized):
            pass

    print("\nWe got all the frames! It took: " + str(time.time()-start_time)+" seconds.\n")

    dice_thread = DiceReader(cap=dice_cap)
    dice_thread.name = "DiceReaderThread"
    hand_thread = HandReader(timeThreshold = 2, cap=hand_cap)
    hand_thread.name = "HandReaderThread"
    board_thread = BoardReader(cap=board_cap, useImg=True)
    board_thread.name = "BoardReaderThread"

    game_thread = Game(dice_thread, hand_thread, board_thread)
    game_thread.name = "GameThread"

    ui_thread = Ui(hand_thread = hand_thread, 
                   dice_thread = dice_thread, 
                   board_thread = board_thread, 
                   game_thread = game_thread,
                   dice_cap = dice_cap,
                   hand_cap = hand_cap,
                   board_cap = board_cap,
                   useImg = True)
    ui_thread.name = "UiThread"

    
    dice_thread.start()
    hand_thread.start()
    board_thread.start()
    while not (dice_thread.initialized and hand_thread.initialized and board_thread.initialized):
        pass
    print("\nAll cam_threads initialized! It took: " + str(time.time()-start_time) + " seconds.\n")

    game_thread.start()
    
    while not game_thread.initialized:
        pass

    print("game_thread initialized! It took: " + str(time.time()-start_time) + " seconds.\n")

    ui_thread.start()

    while True:
        # status = LogicHandler.current_gesture()
        time.sleep(5)
        status = game_thread.game_status
        if status == GameStatus.QUIT or ui_thread.exit:
            end_time = ui_thread.end_time
            ui_thread.stop()
            game_thread.stop()
            dice_thread.stop()
            hand_thread.stop()
            board_thread.stop()
            if dice_camera_id == hand_camera_id == board_camera_id:
                cap.stop()
            else:
                dice_cap.stop()
                hand_cap.stop()
                board_cap.stop()
            print("\nProcess quit!\n")
            print("Process ran for: " + str((time.time()-start_time)/60) + " minutes!\n")
            break

    print("Shutdown took: " + str(time.time()-end_time) + " seconds.\n")
if __name__ == "__main__":
    main()