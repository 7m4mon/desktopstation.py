'''
Description: 
desktopstation.py の動作確認用サンプルプログラムです。
島式ホームが一つ設置されたコースの待避線側から列車が出発し、続いて本線側から列車が出発。
先行列車が待避線に停車後、本線側を後続列車が通過、その後、退避列車が出発。
通過した列車が本線に停車して、退避列車が待避線に停車します。
TNOS の 1-2 エンドレス 追い越し の動作となります。
環境は Windows10 64bit, Python 3.8.10、playsound は 1.2.2 を使用
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
    ds.setLocoDirection(train.addr, dir)                # 進行方向を決定

# 減速して駅に停車（passage = True で通過）
def train_stop_station(train: Train, s88_slow, s88_stop, passage = False, passage_horn = ""):
    ds.waitForS88(1, s88_slow)                          # 減速位置に到達
    if passage_horn != "":
        playsound.playsound(passage_horn, False)
    if not passage:
        ds.setLocoSpeed(train.addr, train.low_speed)    # 減速
    ds.waitForS88(1, s88_stop)                          # 停車位置に到達するのを待つ
    if not passage:
        ds.setLocoSpeed(train.addr, 0)                  # 停車

# 駅通過
def train_passage_station(train: Train, s88_slow, s88_stop):
    train_stop_station(train, s88_slow, s88_stop, True, train.horn_file)

# 駅入場側ポイントを切り替えつつ、一周回ってくる
def train_go_around(train:Train, turnout_addr, turnout_dir):
    ds.setLocoSpeed(train.addr, train.hi_speed)         # 出発
    for i in range(len(S88.round_list)):
        ds.waitForS88(1, S88.round_list[i])
        print("TRAIN " + str(train.addr) + " ENTER AT " + str(i))
        if  i == S88.turnout_change_index:
            ds.setTurnout(turnout_addr,turnout_dir)     # 入場ポイントを変更
    print("GO_AROUND_DONE : " + str(train.addr))

def train_rapid_move(train: Train, turnout_dir = 0):
    ds.waitForS88(1, S88.round_list[S88.late_train_start_index])                 # 先行列車が入場検出位置に到達
    ds.setTurnout(1,turnout_dir)                        # 出発ポイントを本線側へ
    train_go_around(train, 2, turnout_dir)              # 入場位置まで列車を進める
    ds.setTurnout(1,turnout_dir)                        # 出発ポイントを本線側へ（念のため）
    train_passage_station(train, S88.t0_slow, S88.t0_stop)
    train_go_around(train, 2, turnout_dir)              # 入場位置まで列車を進める
    train_stop_station(train, S88.t0_slow, S88.t0_stop)

def train_local_move(train: Train, turnout_dir = 1):
    ds.setTurnout(1,turnout_dir)                        # 出発ポイントを退避側へ
    train_go_around(train, 2, turnout_dir)              # 入場位置まで列車を進める
    train_stop_station(train, S88.t1_slow, S88.t1_stop)
    # --- 通過待ち --- 
    ds.waitForS88(1, S88.t0_stop)                       # 先行列車がホームに到達
    ds.waitForS88(1, S88.round_list[S88.late_train_start_index])  # 先行列車が出場検出位置に到達
    playsound.playsound(train.horn_file, False)
    # --- 
    ds.setTurnout(1,turnout_dir)                        # 出発ポイントを退避側へ
    train_go_around(train, 2, turnout_dir)              # 入場位置まで列車を進める
    train_stop_station(train, S88.t1_slow, S88.t1_stop)

if ds.open(DS_COMPORT) == False:
    quit()

ds.setPing()
ds.setPower(1)
ds.start_polling_s88()

train_init(tr1, 2)
train_init(tr2, 2)

try :
    while True:
        thread1 = threading.Thread(target=train_rapid_move, args=(tr1,))
        thread2 = threading.Thread(target=train_local_move, args=(tr2,))
        thread1.start()
        thread2.start()
        while thread1.is_alive() or thread2.is_alive():     # thread1.join() はCtrl-C を受け取らないので。
            time.sleep(0.01)
        # ここで2つの列車が揃っている。
        time.sleep(0.1)
        playsound.playsound(DEPARTURE_BELL, True)          # 発車ベルを鳴らす。鳴り終わるまで待つ。


except KeyboardInterrupt:
    pass

except Exception as e:
    print(e)

finally:
    kill_all_threads()
    ds.stop_polling_s88()
    ds.close()
