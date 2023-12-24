'''
desktopstation.py
Description: DesktopStation という、DCCコントローラーの Python Wrapper です。
DS Air Rev. R2n5 で検証しています。
Author: 7M4MON
Date: 2023/12/24 初版
'''
# コマンドは以下のURLで公開されています。
# https://desktopstation.net/wiki/doku.php/desktop_station_s_serial_communication_specification

import time, serial, threading

class DesktopStation:
    # s88_count は接続している S88 装置の数。1つで 8 または 16 port。
    def __init__(self, s88_count = 1):
        self.ser = serial.Serial()
        self.comm_ok = False         
        self.lock = False
        self.polling_s88_en = False
        self.s88b = [0] * s88_count   # S88を読んだときに保存するためのバッファを用意する。
    
    def open(self,port):
        self.ser.port = port
        self.ser.baudrate = 115200
        self.ser.timeout = 1
        try:
            self.ser.open()      # これでリセットがかかる
        except:                  # 開けないときの処理
            print("DS COMPORT_NG")
            return False
        print('Waitihg for DS ...')
        i = 0.0
        while self.ser.in_waiting == 0 and i < 3.0:  #最初のデータが来るのを待つ
            time.sleep(0.1)
            i += 0.1
        time.sleep(1)                               # 残りのデータが来るのを待つ
        rcv = self.ser.read_all().decode()          # 残りのデータを読む
        print(rcv)

        if '100 Ready' in rcv:
            print("DS COMM_OK")
            self.comm_ok = True
        else :
            print("DS NO_RESPONSE")
            self.comm_ok = False
        
        return self.comm_ok
    
    def stop(self):
        print("DS STOP")
        self.lock = False       # 強制的にロックを解除
        if self.ser.is_open :
            self.send_command("setPower(0)")
            self.ser.close()
    
    # 非同期でコマンドを送る場合にbusyだったら空くまで待つ
    def unlock_check(self,timeout = 1.0):
        i = 0.0
        unlock = True
        while self.lock and i < timeout:
            time.sleep(0.01)
            i += 0.01
        if i >= timeout :
            unlock = False
            print("DS SEND_LOCKED")
        return unlock

    def send_command(self,command_str, lock_time = 0.1):
        if not self.comm_ok :
            print("DS NOT_OPEN")
            return
        
        command_str += '\r\n'
        rcv = ''
        if self.unlock_check():
            self.lock = True
            self.ser.write(command_str.encode())
            print(command_str)
            rcv = self.ser.readline().decode()
            time.sleep(0.01)           # 応答が複数の場合の間隔は 6msくらい。
            rcv += self.ser.read_all().decode()
            print(rcv)
            if '200 Ok' in rcv:
                time.sleep(lock_time)   # 200 Okの応答からウェイトを最低100ms以上置いてください。
            else:
                print("DS REPLY_ERROR")
            self.lock = False
        return rcv

    def setPing(self):
        self.send_command("setPing()")

    def setPower(self, on):
        self.send_command("setPower(" + str(on) + ")")

    def setLocoSpeed(self, addr, speed, speed_step = 0):
        self.send_command("setLocoSpeed(" + str(0xC000 + addr) + "," + str(speed) + "," + str(speed_step) + ")")

    def setLocoDirection(self, addr, dir):  # dir = 1 or 2
        self.send_command("setLocoDirection(" + str(0xC000 + addr) + "," + str(dir) + ")",)

    def setLocoFunction(self, addr, num, on):
        self.send_command("setLocoFunction(" + str(0xC000 + addr) + "," + str(num) + "," + str(on) + ")")

    def setLocoConfig(self, addr, value):
        self.send_command("setLocoConfig(" + str(0xC000 + addr) + "," + str(value) + ")")

    def getLocoConfig(self, addr, num):
        rcv = self.send_command("getLocoConfig(" + str(0xC000 + addr) + "," + str(num) + ")")
        return rcv      # 例 : @CV,49162,8,129,\r\n 

    def setTurnout(self, addr, dir):        # dir: even = 0, odd = 1
        self.send_command("setTurnout(" + str(0x3800 + addr - 1) + "," + str(dir) + ")", 0.1)    # これも1始まり。切り替わり時間を待つ(実験したところ、0.1で良かった。)
    
    def getS88(self, count):
        rcv = self.send_command("getS88(" + str(count) + ")", 0.01)    # 3msくらいで応答するみたい。
        retval = -1
        if '@S88,' in rcv:
            s = rcv.split(',')
            retval = int(s[count], 16)
        return retval

    # S88 のバッファ s88b を更新する。
    def updateS88b(self):
        for i in range(len(self.s88b)):                        # 複数の S88装置は未検証（持ってないので。）
            self.s88b[i] = self.getS88(i + 1)                  # 1から始まるので。配列は0から。
            print("S88-" + str(i + 1) + ":" + format(self.s88b[i],'#018b'))
        return True

    # count 個目の s88b のバッファから該当(num)の位置のビットを読む。
    def readS88b(self, count, num):
        a = self.s88b[count - 1]     # 1から始まるらしい。
        a >>= (num - 1)              # 1から始まるらしい。
        arrived = bool(a & 1)
        return arrived

    # count 個目の S88 装置の num番目のビットがHになるのを待つ。
    def waitForS88(self, count, num, timeout = 60):
        i = 0
        arrived = False
        while arrived == False and i < timeout:
            if not self.polling_s88_en:
                self.updateS88b()
            arrived = self.readS88b(count, num)
            if not arrived:
                time.sleep(0.1)
                i += 0.1
        if i >= timeout :
            print("DS NOT_ARRIVED")
        return arrived
    
    def polling_s88(self):
        self.updateS88b()
        if self.polling_s88_en :
            self.tm = threading.Timer( self.polling_interval , self.polling_s88 )   # 自動で再起動しないので毎回自分をセットする。
            self.tm.start()
    
    def start_polling_s88(self, interval = 0.1):
        print("S88 POLLING_START")
        self.polling_interval = interval
        self.polling_s88_en = True
        self.polling_s88()
    
    def stop_polling_s88(self):
        self.polling_s88_en = False
        self.tm.cancel()
        print("S88 POLLING_STOP")
