'''
Description: 
desktopstation.py の動作確認用サンプルプログラムです。
2つの駅が1本のエンドレス線路に設置されたコースを2本の列車が同時に走ります。
駅に入線時に減速し、到着したときは、もう片方の駅に列車が到着するまで待ちます。
TNOS の 8 エンドレス の動作となります。
環境は Windows10 64bit, Python 3.12.1、playsound は 1.2.2 を使用
Author: 7M4MON
Date: 2024/6/8 初版
'''


import time, threading, ctypes, playsound     # playsound==1.2.2
import desktopstation

ds = desktopstation.DesktopStation()

DS_COMPORT = 'COM3'
DEPARTURE_BELL = 'stationbell1.mp3'

class Train:    # 各列車のパラメータを定義するクラス
    def __init__(self, addr, hi_speed, low_speed, horn_file):
        self.addr = addr
        self.hi_speed = hi_speed
        self.low_speed = low_speed
        self.horn_file = horn_file

tr2 = Train(10, 800, 300, "horn1.mp3")
tr1 = Train(33, 400, 200, "horn2.mp3")

# S88 装置の各センサの位置を定義するクラス
class S88:
    t0_slow = 1         # 駅0側 減速
    t0_stop = 2         # 駅0側 停止
    t1_slow = 3         # 駅1側 減速
    t1_stop = 4         # 駅1側 停止
    t0_thuru = 6        # tr2 が 6 に入る前に tr1 が 1 を抜けていて、かつ
    t1_thuru = 5        # tr2 が 1 に入る前に tr1 が 2 を抜けている条件

# 終了時に呼ばれてスレッドをすべて終了する
def kill_all_threads():
  for thread in threading.enumerate():
    if thread != threading.main_thread():
      print(f"kill: {thread.name}")
      ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.native_id, ctypes.py_object(SystemExit))

def train_init(train: Train, dir):
    ds.setLocoSpeed(train.addr, 0)                      # 念のため
    ds.setLocoFunction(train.addr,0, 1)                 # ライトを点灯
    ds.setLocoDirection(train.addr, dir)                # 進行方向を前へ

def train_move(train: Train, s88_thuru_point, s88_slow_point, s88_stop_point ):
    ds.setLocoSpeed(train.addr, train.hi_speed)         # 出発
    ds.waitForS88(1, s88_thuru_point)
    ds.waitForS88(1, s88_slow_point)                    # 減速位置に到達するのを待つ
    ds.setLocoSpeed(train.addr, train.low_speed)        # 減速
    playsound.playsound(train.horn_file, False)         # ホーンを鳴らす（PC・非同期）
    ds.waitForS88(1, s88_stop_point)                    # 減速位置に到達するのを待つ
    ds.setLocoSpeed(train.addr, 0)                      # 停車


if ds.open(DS_COMPORT) == False:
    quit()

ds.setPing()
ds.setPower(1)
ds.start_polling_s88()

train_init(tr1, 1)
train_init(tr2, 1)

state = 0       # 0 = tr1が駅0, tr2が駅1

try :
    while True:
        if state == 0:
            thread1 = threading.Thread(target=train_move, args=(tr1, S88.t1_thuru, S88.t1_slow, S88.t1_stop))
            thread2 = threading.Thread(target=train_move, args=(tr2, S88.t0_thuru, S88.t0_slow, S88.t0_stop))
        if state == 1:
            thread1 = threading.Thread(target=train_move, args=(tr2, S88.t1_thuru, S88.t1_slow, S88.t1_stop))
            thread2 = threading.Thread(target=train_move, args=(tr1, S88.t0_thuru, S88.t0_slow, S88.t0_stop))
        thread1.start()
        thread2.start()
        while thread1.is_alive() or thread2.is_alive():     # thread1.join() はCtrl-C を受け取らないので。
            time.sleep(0.01)

        # ここで2つの列車が揃っている。
        time.sleep(0.5)
        playsound.playsound(DEPARTURE_BELL, True)          # 発車ベルを鳴らす。鳴り終わるまで待つ。
        state += 1
        if state == 2:
            state = 0


except KeyboardInterrupt:
    pass

except Exception as e:
    print(e)

finally:
    kill_all_threads()
    ds.stop_polling_s88()
    ds.close()
