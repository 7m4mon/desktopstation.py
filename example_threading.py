'''
Description: 
desktopstation.py の動作確認用サンプルプログラムです。
Threading を使用して、各列車を独立して制御しています。
ポイントを２つ使用し、行き違いに出来るようになったコースを
1. ポイントを直線側に切り替えて引き込み線の先端に行く。
2. 引き込み線の先端で停車してポイントを曲線側にする
3. 駅まで進んで停車し、対向列車が来るまで待つ。
を繰り返します。
環境は Windows10 64bit, Python 3.8.10
Author: 7M4MON
Date: 2023/12/24 初版
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

tr1 = Train(10, 200, "horn1.mp3")
tr2 = Train(70, 250, "horn2.mp3")

# 終了時に呼ばれてスレッドをすべて終了する
def kill_all_threads():
  for thread in threading.enumerate():
    if thread != threading.main_thread():
      print(f"kill: {thread.name}")
      ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.native_id, ctypes.py_object(SystemExit))


def train_move(train: Train, train_dir, turnout_addr, turnout_dir, s88_tip, s88_station ):
    ds.setLocoFunction(train.addr,0, 1)                 # ライトを点灯
    ds.setTurnout(turnout_addr,turnout_dir)             # ポイントを引き込み線側へ
    ds.setLocoDirection(train.addr, train_dir)          # 進行方向を引き込み線側へ
    ds.setLocoSpeed(train.addr, train.speed)            # 引込線に向かって出発
    ds.waitForS88(1, s88_tip)                           # 引込線に到着待ち
    ds.setLocoSpeed(train.addr, 0)                      # 引込線に停車
    turnout_dir = 1 if turnout_dir == 0 else 0          # 0 ⇔ 1
    ds.setTurnout(turnout_addr,turnout_dir)             # ポイントを駅側へ切り替え
    train_dir = 1 if train_dir == 2 else 2              # 1 ⇔ 2
    ds.setLocoDirection(train.addr, train_dir)          # 列車の方向転換
    playsound.playsound(train.horn_file, False)         # ホーンを鳴らす（PC・非同期）
    time.sleep(0.5)                                     # ちょっと待つ
    ds.setLocoSpeed(train.addr, train.speed)            # 駅に向かって出発
    ds.waitForS88(1, s88_station)                       # 駅に到着待ち
    ds.setLocoSpeed(train.addr, 0)                      # 駅に停車

if ds.open(DS_COMPORT) == False:
    quit()

ds.setPing()
ds.setPower(1)
ds.start_polling_s88()

state = 0   # 初期位置 0 or 1
try :
    while True:
        print("state=" + str(state))
        if state == 0: # tr1 が左、tr2 が右に行く
            thread1 = threading.Thread(target=train_move, args=(tr1,1,1,1,1,3))
            thread2 = threading.Thread(target=train_move, args=(tr2,2,2,1,4,2))
            thread1.start()
            thread2.start()
            while thread1.is_alive() or thread2.is_alive(): # thread1.join() はCtrl-C を受け取らないので。
                time.sleep(0.01)
        if state == 1: # tr1 が右、tr2 が左に行く
            thread1 = threading.Thread(target=train_move, args=(tr2,1,1,1,1,3))
            thread2 = threading.Thread(target=train_move, args=(tr1,2,2,1,4,2))
            thread1.start()
            thread2.start()
            while thread1.is_alive() or thread2.is_alive(): # thread1.join() はCtrl-C を受け取らないので。
                time.sleep(0.01)

        time.sleep(0.5) # 2列車揃ったら駅に停車

        state += 1      # 次のステートへ
        if state == 2:  # 終わっていたら0に戻す
            state = 0

except KeyboardInterrupt:
    pass

except Exception as e:
    print(e)

finally:
    kill_all_threads()
    ds.stop_polling_s88()
    ds.stop()
