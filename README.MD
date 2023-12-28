# desktopstation.py

* DesktopStation という、DCCコントローラーの Python Wrapper です。
* Threading による複数列車同時独立制御をするために作成しました。

---
### 使い方
1. `import desktopstation` でファイルをインポートします。
1. `ds = desktopstation.DesktopStation()` でインスタンスを作成します。S88装置が複数ある場合は引数に個数を指定します。
1. `ds.open('COMx')` で DesktopStation を開きます。
1. `ds.setPing()` , `ds.setPower(1)` で DesktopStation から線路に電気を供給して、S88装置から在線情報を読みつつ列車やポイントを制御します。
1. `ds.stop()` で 電源供給を停止、COMポートを閉じて、DesktopStation との接続を解除します。

---
### よく使う関数 
* `ds.setLocoDirection(train_addr, train_dir)`   
列車の進行方向を決定します。
* `ds.setLocoSpeed(train_addr, train_speed)`  
列車の速度を決定します。
* `ds.setTurnout(turnout_addr, turnout_dir)`  
ポイントの開通方向を決定します。
* `ds.waitForS88(s88_count, s88_num)`    
S88 装置の指定のポートが アクティブになるのを待ちます。 

[Serial Communication Specification](https://desktopstation.net/wiki/doku.php/desktop_station_s_serial_communication_specification) に記載されているコマンドはすべて実装済です。  

使い方は、example_y-move.py が参考になるかと思います。

---
### Threading による非同期アクセスについて
* `threading` を使用して、複数の列車を非同期でコントロールすることが可能です。  
その場合、`updateS88b` を各スレッドがアクセスすると、読み取るセンサの数に比例したシリアルポートの読み取り時間が発生します。  
これを防ぐには、`start_polling_s88(interval = 0.1)` で S88 装置のポーリングをしておくと、`waitForS88` は共有メモリ(s88b)から S88 装置の状態を読むようになります。

`example_threading.py` や `example_shuttle_threading_double_track.py` が参考になるかと思います。

[![](https://img.youtube.com/vi/KzaExJKuuNs/0.jpg)](https://www.youtube.com/watch?v=KzaExJKuuNs)
[![](https://img.youtube.com/vi/2GzQ8uJ73sc/0.jpg)](https://www.youtube.com/watch?v=2GzQ8uJ73sc)

---
### その他
* 開発環境は、Windows 10 Pro 64bit, Python 3.8.10 です。
* DS Air Rev. R2n5 で検証しています。
* horn1.mp3, horn2.mp3 は DesktopStation 様の提供です。
