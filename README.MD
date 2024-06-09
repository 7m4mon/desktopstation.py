# desktopstation.py

* DesktopStation という、DCCコントローラーの Python Wrapper です。
* Threading による複数列車同時独立制御をするために作成しました。

---
### 使い方
1. `import desktopstation` でファイルをインポートします。
1. `ds = desktopstation.DesktopStation()` でインスタンスを作成します。S88装置が複数ある場合は引数に個数を指定します。
1. `ds.open('COMx')` で DesktopStation を開きます。
1. `ds.setPing()` , `ds.setPower(1)` で DesktopStation から線路に電気を供給して、S88装置から在線情報を読みつつ列車やポイントを制御します。
1. `ds.close()` で 電源供給を停止、COMポートを閉じて、DesktopStation との接続を解除します。

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

`example_shuttle_threading_double_track.py` が参考になるかと思います。

[![](https://img.youtube.com/vi/2GzQ8uJ73sc/0.jpg)](https://www.youtube.com/watch?v=2GzQ8uJ73sc)

---
### サンプルプログラムについて

TOMIXの[TNOS](https://www.tomytec.co.jp/tomix/necst/5701tnos/)という、自動運転プログラムとの対応表です。

|ファイル名|説明|TNOSの番号|動画|
|---|---|---|---|
|example_endless_alternate.py|交互発着|1-1 エンドレス 交互運転|https://youtu.be/VE1PpkzEKR0|
|example_endless_overtake.py|退避＆追い越し|1-2 エンドレス 追い越し|https://youtu.be/EOrtSsXwhb0|
|example_endless_exchange.py|入れ替え|1-3 エンドレス 入れ替え|https://youtu.be/pulbfx1baHg|
|example_single_track_interchange.py|単線行き違い|5 コンパクト(単線)|https://youtu.be/KzaExJKuuNs|
|example_y-move.py|Y字ポイント往復|該当なし|https://youtube.com/shorts/YktbvJ0o_b4|
|example_shuttle.py|単線往復運転|該当なし|-|
|example_shuttle_threading_double_track.py|複線独立往復運転|該当なし|https://youtu.be/2GzQ8uJ73sc|
|example_endless_chase.py|エンドレス|8|https://youtu.be/mfUUky65Z3k|

TNOS と比較 
- メリット
  * Pythonのスキルがあれば、レイアウトに合わせて自由自在に好みの運転プログラムを作ることが出来る。
  * DCCコントローラーや在線検出器などは同人ハードウェアで提供されているので安価に構築可能。オープンハードウェアなので電子工作のスキルがあれば自作すら可能。
  * Python の多様なライブラリと組み合わせて音を鳴らしたり色々遊べる。
  * VS CodeなどのPC上のエディタでパラメータを設定するので直感的に作業しやすい。
- デメリット
  * 車両のDCC化が必要
  * Pythonの実行環境が必要
  * 動作に関するサポートがない
- 感想
  * KATO には TNOS に相当するソリューションはないので、STEAM教育と絡めてキット化したら面白いのでは。
  * お座敷レイアウトを組み上げて配線するのは一苦労。机上で出来るように、チビ電ないし路面電車のDCCユニットが欲しい。

---
### その他
* 開発環境は、Windows 10 Pro 64bit, Python 3.8.10 / 3.12.1 です。
* DS Air Rev. R2n5 で検証しています。
* horn1.mp3, horn2.mp3 は DesktopStation 様の提供です。
