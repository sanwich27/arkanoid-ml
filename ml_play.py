"""
The template of the main script of the machine learning process
"""
import pickle
from os import path

import games.arkanoid.communication as comm
from games.arkanoid.communication import ( \
    SceneInfo, GameStatus, PlatformAction
)

def ml_loop():
    """
    The main loop of the machine learning process

    This loop is run in a separate process, and communicates with the game process.

    Note that the game process won't wait for the ml process to generate the
    GameInstruction. It is possible that the frame of the GameInstruction
    is behind of the current frame in the game process. Try to decrease the fps
    to avoid this situation.
    """

    # === Here is the execution order of the loop === #
    # 1. Put the initialization code here.
    ball_served = False
    filename = 'your_file_name.pickle'
    filename = path.join(path.dirname(__file__), filename)
    log = pickle.load(open(filename, 'rb'))
    ball_pos=[0,0]
    line_x=0 #球的落點
    line_y=0
    left=0
    slope=0
    # 2. Inform the game process that ml process is ready before start the loop.
    comm.ml_ready()

    # 3. Start an endless loop.
    while True:
        # 3.1. Receive the scene information sent from the game process.
        scene_info = comm.get_scene_info()

        # 3.2. If the game is over or passed, the game process will reset
        #      the scene and wait for ml process doing resetting job.
        if scene_info.status == GameStatus.GAME_OVER or \
            scene_info.status == GameStatus.GAME_PASS:
            # Do some stuff if needed
            ball_served = False

            # 3.2.1. Inform the game process that ml process is ready
            comm.ml_ready()
            continue

        # 3.3. Put the code here to handle the scene information
        line_x=scene_info.ball[0]
        line_y=scene_info.ball[1]
        if scene_info.frame==1:
            ball_pos[0]=scene_info.ball[0]
            ball_pos[1]=scene_info.ball[1]
            line_x=95
            line_y=395
        else:
            if scene_info.ball[1]-ball_pos[1]<0 or scene_info.ball[1]<250:  #moving up
                line_x=95 #移到中間 
                line_y=395
            else: #moving down
                slope=abs(scene_info.ball[0]-ball_pos[0])
                if scene_info.ball[0]-ball_pos[0]>0:#moving right
                    left=0
                else:#moving left
                    left=1
                while line_y<395:
                    if left==0: #還沒撞到右邊
                        if line_x<195:
                            line_x+=slope
                            line_y+=7
                        if line_x>=195:
                            left=1
                            line_x=195 #向左彈回去
                    elif left==1:
                        if line_x>0:
                            line_x-=slope
                            line_y+=7
                        if line_x<=0:
                            left=0
                            line_x=0 #向右彈
                    
            ball_pos[0]=scene_info.ball[0]
            ball_pos[1]=scene_info.ball[1]
        # 3.4. Send the instruction for this frame to the game process
        if not ball_served:
            comm.send_instruction(scene_info.frame, PlatformAction.SERVE_TO_RIGHT)
            ball_served = True
        else:
            if abs(scene_info.platform[0]+20-line_x)<10: #差不多就不要動了
                comm.send_instruction(scene_info.frame, PlatformAction.NONE)
            elif scene_info.platform[0]+20<line_x:
                comm.send_instruction(scene_info.frame, PlatformAction.MOVE_RIGHT)
            elif scene_info.platform[0]+20>line_x:
                comm.send_instruction(scene_info.frame, PlatformAction.MOVE_LEFT)
            history_log = log[scene_info.frame]
            action = history_log.command
            comm.send_instruction(scene_info.frame, action)
