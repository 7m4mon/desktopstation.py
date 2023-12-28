'''
Description: 
desktopstation.py の動作確認用サンプルプログラムです。
S88の1と3の間を往復します。
環境は Windows10 64bit, Python 3.8.10、playsound は 1.2.2 を使用
Author: 7M4MON
Date: 2023/12/28 初版
'''


import time, playsound      # playsound==1.2.2
import desktopstation

ds = desktopstation.DesktopStation()

DS_COMPORT = 'COM3'

class Train:    # 各列車のパラメータを定義するクラス
    def __init__(self, addr, speed, horn_file):
        self.addr = addr
        self.speed = speed
        self.horn_file = horn_file

tr1 = Train(10, 250, "de10_whistle.mp3")

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

try :
    while True:
        train_move(tr1, 3, 1)

except KeyboardInterrupt:
    pass

except Exception as e:
    print(e)

finally:
    ds.close()
