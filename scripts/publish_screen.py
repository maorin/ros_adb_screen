#!/usr/bin/env python
import subprocess
import numpy as np
import cv2
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError



def screencap():
    #pub = rospy.Publisher('chatter', String, queue_size=10)
    pub = rospy.Publisher('screen/image_raw', Image, queue_size=2)
    rospy.init_node('screen_puber', anonymous=True)
    bridge = CvBridge()
    
    rate = rospy.Rate(5) # 10hz
    while not rospy.is_shutdown():
        """
        hello_str = "hello world %s" % rospy.get_time()
        rospy.loginfo(hello_str)
        pub.publish(hello_str)
        """
        process = subprocess.Popen('adb shell screencap -p', shell=True, stdout=subprocess.PIPE)
        screenshot = process.stdout.read()
        img = cv2.imdecode(np.frombuffer(screenshot, np.uint8), cv2.IMREAD_COLOR)
        msg = bridge.cv2_to_imgmsg(img, encoding="bgr8")

        #cv2.imwrite("aa.png", img)        
        pub.publish(msg)
        rate.sleep()

if __name__ == '__main__':
    try:
        screencap()
    except rospy.ROSInterruptException:
        pass