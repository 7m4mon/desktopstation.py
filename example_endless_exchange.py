'''
Description: 
desktopstation.py の動作確認用サンプルプログラムです。
本線側の列車が出発し、その後、退避側の列車が出発。
先発列車を待避側に入れて停車、後続列車を本線側に入れて停車します。
TNOS の 1-3 エンドレス 入れ替え の動作となります。
環境は Windows10 64bit, Python 3.12.1、playsound は 1.2.2 を使用
Author: 7M4MON
Date: 2024/1/2 初版
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

tr1 = Train(33, 550, 200, "horn2.mp3")
tr2 = Train(70, 450, 200, "horn1.mp3")

# S88 装置の各センサの位置を定義するクラス
class S88:
    t0_slow = 1         # ポイント0側 減速
    t0_stop = 2         # ポイント0側 停止
    t1_slow = 3         # ポイント1側 減速
    t1_stop = 4         # ポイント1側 停止
    round_list = [5,6,7,8,9,10]
    turnout_change_index = 5
    late_train_start_index = 3

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

# 減速して駅に停車（passage = True で通過）
def train_stop_station(train: Train, s88_slow, s88_stop, passage = False):
    ds.waitForS88(1, s88_slow)                          # 減速位置に到達
    if not passage:
        ds.setLocoSpeed(train.addr, train.low_speed)    # 減速
    ds.waitForS88(1, s88_stop)                          # 停車位置に到達するのを待つ
    if not passage:
        ds.setLocoSpeed(train.addr, 0)                  # 停車

# 駅入場側ポイントを切り替えつつ、一周回ってくる
def train_go_around(train:Train, turnout_addr, turnout_dir):
    ds.setLocoSpeed(train.addr, train.hi_speed)         # 出発
    for i in range(len(S88.round_list)):
        ds.waitForS88(1, S88.round_list[i])
        print("TRAIN " + str(train.addr) + " ENTER AT " + str(i))
        if  i == S88.turnout_change_index:
            ds.setTurnout(turnout_addr,turnout_dir)     # 入場ポイントを変更
    print("GO_AROUND_DONE : " + str(train.addr))


def train_primary_move(train: Train):
    ds.setTurnout(1,0)                                  # 出発ポイントを本線側へ
    playsound.playsound(train.horn_file, False)
    train_go_around(train, 2, 1)
    train_stop_station(train, S88.t1_slow, S88.t1_stop)

def train_secondery_move(train: Train):
    ds.waitForS88(1, S88.round_list[S88.late_train_start_index])                 # 先行列車が入場検出位置に到達
    ds.setTurnout(1,1)                                  # 出発ポイントを退避側へ
    playsound.playsound(train.horn_file, False)
    train_go_around(train, 2, 0)
    train_stop_station(train, S88.t0_slow, S88.t0_stop) # 直線側に停車


if ds.open(DS_COMPORT) == False:
    quit()

ds.setPing()
ds.setPower(1)
ds.start_polling_s88()

train_init(tr1, 2)
train_init(tr2, 2)
state = 0
try :
    while True:
        if state == 0 :
            thread1 = threading.Thread(target=train_primary_move, args=(tr1,))
            thread2 = threading.Thread(target=train_secondery_move, args=(tr2,))
        if state == 1 :
            thread1 = threading.Thread(target=train_primary_move, args=(tr2,))
            thread2 = threading.Thread(target=train_secondery_move, args=(tr1,))
        thread1.start()
        thread2.start()
        while thread1.is_alive() or thread2.is_alive():     # thread1.join() はCtrl-C を受け取らないので。
            time.sleep(0.01)
        # ここで2つの列車が揃っている。
        time.sleep(2)
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
