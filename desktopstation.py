'''
desktopstation.py
Description: DesktopStation という、DCCコントローラーの Python Wrapper です。
Author: 7M4MON
Date: 2024/1/1
'''

#https://desktopstation.net/wiki/doku.php/desktop_station_s_serial_communication_specification

import time, serial

class DesktopStation:

    def __init__(self):
        self.ser = serial.Serial()
        self.comm_ok = False         
        self.lock = False
    
    def open(self,port):
        self.ser.port = port
        self.ser.baudrate = 115200
        self.ser.timeout = 3
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
        time.sleep(1)   # 残りのデータが来るまで待つ。
        rcv = self.ser.read_all().decode()
        print(rcv)

        if '100 Ready' in rcv:
            print("DS COMM_OK")
            self.comm_ok = True
        else :
            print("DS NO_RESPONSE")
            self.comm_ok = False
        
        return self.comm_ok
    
    def close(self):
        if self.ser.is_open :
            self.ser.close()
    
    def stop(self):
        print("DS STOP")
        self.lock = False       # 強制的にロックを解除
        if self.ser.is_open :
            self.send_command("setPower(0)")
            self.ser.close()
    
    def unlock_check(self,timeout = 3.0):
        i = 0.0
        unlock = True
        while self.lock and i < timeout:
            time.sleep = 0.01
            i += 0.01
        if i >= timeout :
            unlock = False
            print("DS SEND_LOCKED")
        return unlock

    def send_command(self,command_str, lock_time = 0.1):
        if not self.comm_ok :
            print("DS NOT_OPEN")
            return
        self.ser.reset_input_buffer()
        command_str += '\r\n'
        rcv = ''
        if self.unlock_check():
            self.lock = True
            self.ser.write(command_str.encode())
            print(command_str)
            rcv = self.ser.readline().decode()
            time.sleep(0.01)            # 応答が複数の場合の間隔は 6msくらい。
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

    def setLocoDirection(self, addr, dir):
        self.send_command("setLocoDirection(" + str(0xC000 + addr) + "," + str(dir) + ")")

    def setLocoFunction(self, addr, num, on):
        self.send_command("setLocoFunction(" + str(0xC000 + addr) + "," + str(num) + "," + str(on) + ")")

    def setTurnout(self, addr, dir):
        self.send_command("setTurnout(" + str(0x3800 + addr - 1) + "," + str(dir) + ")")    #これも1始まり。
    
    def getS88(self, count):
        rcv = self.send_command("getS88(" + str(count) + ")", 0.005)    # 3msくらいで応答するみたい。
        retval = -1
        if '@S88,' in rcv:
            s = rcv.split(',')
            retval = int(s[count], 16)
        return retval

    def waitForS88(self, count, num, timeout = 60):
        i = 0
        arrived = False
        while arrived == False and i < timeout:
            a = self.getS88(count)
            a >>= (num - 1)     # 1から始まるらしい。
            arrived = bool(a & 1)
            time.sleep(0.1)
            i += 0.1
        if i >= timeout :
            print("DS NOT_ARRIVED")
        
        return not arrived
    
    def setLocoConfig(self, addr, value):
        self.send_command("setLocoConfig(" + str(0xC000 + addr) + "," + str(value) + ")")

    def getLocoConfig(self, addr, num):
        rcv = self.send_command("getLocoConfig(" + str(0xC000 + addr) + "," + str(num) + ")")
        return rcv      # 例 : @CV,49162,8,129,\r\n 
