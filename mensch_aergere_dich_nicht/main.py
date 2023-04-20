import cv2
import time
from ui import Ui
from game import Game
from image_detection import HandReader, DiceReader, BoardReader
from utilities import VideoStream, GameStatus, Fps


def main():
    '''Starts the game.

    This module initializes all threads with the right timing
    checks if everything worked out, prints in terminal
    and quits the game, if the ESC-Key is hit.
    '''

    # Variables needed for performance testing
    fps_tracker = Fps("MainThread")
    start_time = time.time()
    new_time = start_time
    prev_frame_time = 0

    # Camera_ids for all cameras
    dice_camera_id = 4
    hand_camera_id = 4
    board_camera_id = 4

    print("\nStarting threads...")

    # Checks if only 1 VideoStream object / 1 camera is needed
    if dice_camera_id == hand_camera_id == board_camera_id:
        
        cap = VideoStream(dice_camera_id)
        cap.name = "VideoStreamThread"

        # initializes VideoStream
        cap.start()

        # Shares VideoStream with all other threads
        dice_cap = cap
        hand_cap = cap
        board_cap = cap
    
    # Initializes 1 VideoStream for every camera needed
    else:
        dice_cap = VideoStream(dice_camera_id)
        dice_cap.name = "DiceCamThread"
        hand_cap = VideoStream(hand_camera_id)
        hand_cap.name = "HandCamThread"
        board_cap = VideoStream(board_camera_id)
        board_cap.name = "BoardCamThread"

        # initializes VideoStream
        dice_cap.start()
        hand_cap.start()
        board_cap.start()

    # Waits till all cameras have startet and got their first frame
    if dice_camera_id == hand_camera_id == board_camera_id:
        while not cap.initialized:
            pass
    else:
        while not (dice_cap.initialized and hand_cap.initialized and board_cap.initialized):
            pass

    print(f"\nWe got all the frames! It took: {(time.time()-new_time):.3f} seconds.\n")
    new_time = time.time()

    # Image detection objects assigned to variables
    dice_thread = DiceReader(cap=dice_cap, time_threshold = 2)
    dice_thread.name = "DiceReaderThread"
    hand_thread = HandReader(cap=hand_cap, time_threshold = 1)
    hand_thread.name = "HandReaderThread"
    board_thread = BoardReader(cap=board_cap, use_img=True)
    board_thread.name = "BoardReaderThread"

    # Game object assigned to variable
    game_thread = Game(dice_thread, hand_thread, board_thread)
    game_thread.name = "GameThread"

    # Ui object assigned to variable
    ui_thread = Ui(hand_thread = hand_thread, 
                   dice_thread = dice_thread, 
                   board_thread = board_thread, 
                   game_thread = game_thread,
                   dice_cap = dice_cap,
                   hand_cap = hand_cap,
                   board_cap = board_cap,
                   use_img = True)
    ui_thread.name = "UiThread"

    # Initializing all image detection threads
    dice_thread.start()
    hand_thread.start()
    board_thread.start()

    # Waits for image detection threads to have one complete run
    while not (dice_thread.initialized and hand_thread.initialized and board_thread.initialized):
        pass

    print(f"\nAll cam_threads initialized! It took: {(time.time()-new_time):.3f} seconds.\n")
    new_time = time.time()

    # Initializing game thread
    game_thread.start()
    game_thread.corners = board_thread.corners

    # Waits for game_thread to have one complete run
    while not game_thread.initialized:
        pass
    
    print(f"game_thread initialized! It took: {(time.time()-new_time):.3f} seconds.\n")
    new_time = time.time()

    # Stopping board_thread for performance reasons
    board_thread.stop()
    while not board_thread.stopped():
        pass
    
    print(f"board_thread stopped! It took: {(time.time()-new_time):.3f} seconds.\n")
    new_time = time.time()

    # Initializing game thread
    ui_thread.start()

    print(f"ui_thread started! It took: {(time.time()-new_time):.3f} seconds.\n")
    print(f"### Game has started ############################\n")

    # While-loop runs while game is active
    while True:
        
        # Takes the frame from ui and puts it trough fps_tracker
        ui_frame = fps_tracker.counter(ui_thread.frame, prev_frame_time, name="Main", corner=1)
        prev_frame_time = time.time()

        # Saves performance stats
        main_stats = fps_tracker.stats

        # Checks if the game is still running
        status = game_thread.game_status

        # Shows ui_frame in window
        cv2.imshow(ui_thread.window_name, ui_frame)

        # Waits for a key input
        key = cv2.waitKey(20)  

        # Checks if the game should quit or if ESC-Key is pressed        
        if status == GameStatus.QUIT or key == 27:

            # Closes the ui window
            cv2.destroyAllWindows()

            # Saves the stats of different threads
            ui_stats = ui_thread.stats
            dice_stats = dice_thread.stats
            hand_stats = hand_thread.stats

            # Stops all threads
            ui_thread.stop()
            game_thread.stop()
            dice_thread.stop()
            hand_thread.stop()
            board_thread.stop()
            if dice_camera_id == hand_camera_id == board_camera_id:
                cap_stats = cap.stats
                dice_cap_stats = "No DiceCam"
                hand_cap_stats = "No HandCam"
                board_cap_stats = "No BoardCam"
                cap_res = cap.camera_resolution
                cap.stop()
            else:
                cap_stats  = "More than one camera used"
                dice_cap_stats = dice_cap.stats
                hand_cap_stats = hand_cap.stats
                board_cap_stats = board_cap.stats
                cap_res = hand_cap.camera_resolution
                dice_cap.stop()
                hand_cap.stop()
                board_cap.stop()
            print("\n### Process quit!\n\n#################################\n")

            print("Process ran for: " + str(time.strftime("%Hh %Mm %Ss", time.gmtime((time.time()-start_time)))) + "\n")

            break
    
    # Prints all collected statistics
    print(f"###### Statistics ######\n")
    print(f"Camera Resolution: {cap_res}\n\n")
    print(f"{main_stats}\n")
    print(f"{ui_stats}\n")
    print(f"{dice_stats}\n")
    print(f"{hand_stats}\n")
    print(f"{cap_stats}\n")
    print(f"{dice_cap_stats}\n")
    print(f"{hand_cap_stats}\n")
    print(f"{board_cap_stats}\n")
    print(f"#########################\n")

# Runs main method
if __name__ == "__main__":
    main()