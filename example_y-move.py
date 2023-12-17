'''
Description: 
desktopstation.py の動作確認用サンプルプログラムです。
ポイントを一つ使用し、Y字のコースを、
0. ポイントを 0番側に切り替えて、根元からスタート、0番側に移動して停車
1. 根元に戻ってきて停車
2. ポイントを 1番側に切り替え、1番側に移動して停車
3. 根元に戻ってきて停車
を繰り返します。
環境は Windows10 64bit, Python 3.8.10、playsound は 1.2.2 を使用
Author: 7M4MON
Date: 2024/1/1
'''


import time, playsound      # playsound==1.2.2
import desktopstation

ds = desktopstation.DesktopStation()

DS_COMPORT = 'COM3'
LOCO_ADDR = 10
LOCO_SPEED = 400
LOCO_STOP_SEC = 0.3

def train_move(dir, turnout_dir, s88_num):
    ds.setTurnout(1, turnout_dir)
    ds.setLocoDirection(LOCO_ADDR, dir)
    playsound.playsound("de10_whistle.mp3")
    time.sleep(LOCO_STOP_SEC)
    ds.setLocoSpeed(LOCO_ADDR, LOCO_SPEED)
    ds.waitForS88(1,s88_num)
    ds.setLocoSpeed(LOCO_ADDR, 0)


if ds.open(DS_COMPORT) == False:
    quit()

ds.setPing()
ds.setPower(1)
ds.setLocoFunction(LOCO_ADDR, 0, 1) # ライト点灯

state = 0
try :
    while True:
        if state == 0 :
            train_move(2,0,4)
        if state == 1 :
            train_move(1,0,1)
        if state == 2:
            train_move(2,1,3)
        if state == 3:
            train_move(1,1,1)
        state += 1
        if state == 4:
            state = 0

except KeyboardInterrupt:
    pass

except Exception as e:
    print(e)

finally:
    ds.stop()
