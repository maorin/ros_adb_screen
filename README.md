# ros_adb_screen

将手机屏幕发布到ROS topic中

## mincap投屏方式
https://github.com/maorin/minicap

## 启动mincap
adb devices
adb forward tcp:1313 localabstract:minicap
adb shell LD_LIBRARY_PATH=/data/local/tmp/adbmirror /data/local/tmp/adbmirror/minicap -P 2340x2340@780x780/0 -S -Q 80

['adb', 'shell', 'LD_LIBRARY_PATH=/data/local/tmp/adbmirror /data/local/tmp/adbmirror/minicap -P 2340x2340@780x780/0 -S -Q 80']


## 接收屏幕
python gui.py 780x360 1080x2340 /data/local/tmp/adbmirror



# 启动
roslaunch usb_cam-test.launch



