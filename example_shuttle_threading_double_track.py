'''
Description: 
desktopstation.py の動作確認用サンプルプログラムです。
2つの列車がそれぞれ独立した線路を、S88の1と3の間、S88の4と6の間を往復します。
1,4 に到着したときは、もう片方の列車が到着するまで待ちます。
TNOS における該当例はありません。
環境は Windows10 64bit, Python 3.8.10、playsound は 1.2.2 を使用
Author: 7M4MON
Date: 2023/12/28 初版
'''


import time, threading, ctypes, playsound     # playsound==1.2.2
import desktopstation

ds = desktopstation.DesktopStation()

DS_COMPORT = 'COM3'

class Train:    # 各列車のパラメータを定義するクラス
    def __init__(self, addr, speed, horn_file):
        self.addr = addr
        self.speed = speed
        self.horn_file = horn_file

tr1 = Train(10, 250, "horn1.mp3")
tr2 = Train(70, 300, "horn2.mp3")

# 終了時に呼ばれてスレッドをすべて終了する
def kill_all_threads():
  for thread in threading.enumerate():
    if thread != threading.main_thread():
      print(f"kill: {thread.name}")
      ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.native_id, ctypes.py_object(SystemExit))

def train_move(train: Train, s88_dist, s88_station ):
    ds.setLocoFunction(train.addr,0, 1)                 # ライトを点灯
    ds.setLocoDirection(train.addr, 2)                  # 進行方向を前へ
    ds.setLocoSpeed(train.addr, train.speed)            # 前方に向かって出発
    ds.waitForS88(1, s88_dist)                          # 前方指定位置に到着待ち
    ds.setLocoSpeed(train.addr, 0)                      # 前方指定位置に停車
    ds.setLocoDirection(train.addr, 1)                  # 列車の方向転換
    playsound.playsound(train.horn_file, False)         # ホーンを鳴らす（PC・非同期）
    time.sleep(0.5)                                     # ちょっと待つ
    ds.setLocoSpeed(train.addr, train.speed)            # 出発位置に向かって後進開始
    ds.waitForS88(1, s88_station)                       # 出発位置に到着待ち
    ds.setLocoSpeed(train.addr, 0)                      # 出発位置に停車
    time.sleep(0.5)                                     # ちょっと待つ


if ds.open(DS_COMPORT) == False:
    quit()

ds.setPing()
ds.setPower(1)
ds.start_polling_s88()

try :
    while True:
            thread1 = threading.Thread(target=train_move, args=(tr1, 3, 1))
            thread2 = threading.Thread(target=train_move, args=(tr2, 6, 4))
            thread1.start()
            thread2.start()
            while thread1.is_alive() or thread2.is_alive(): # thread1.join() はCtrl-C を受け取らないので。
                time.sleep(0.01)
            # ここで2つの列車が揃っている。

except KeyboardInterrupt:
    pass

except Exception as e:
    print(e)

finally:
    kill_all_threads()
    ds.stop_polling_s88()
    ds.close()
