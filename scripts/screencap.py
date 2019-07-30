#!/usr/bin/env python
import subprocess
import numpy as np
import cv2
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError



import pygame
import cStringIO
import sys
from time import time

from capclient import CapClient
from touchclient import TouchClient
from rotationclient import RotationClient
from adbclient import AdbClient

MENU_TAP = 2
MENU_TIMEOUT = 10
MENU_BORDER = 10
MENU_WIDTH = 15

NAV_WIDTH = 7

DOUBLECLICK_TIME = 0.2
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))



class screencap():
    def __init__(self):
        #assert len(sys.argv) == 4
        argv1 = "780x360"
        argv2 = "1080x2340"
        argv3 = "/data/local/tmp/adbmirror"
        
        self.size = map(int, argv1.split("x"))
        orig = map(int, argv2.split("x"))
        self.orig = orig[1], orig[0]
        self.path = argv3
        
        self.scalel = True
        self.scalep = False
        
        self.cap = CapClient(self)
        self.cap.start()
        
        self.touch = TouchClient(self)
        self.touch.start()
        
        self.rot = RotationClient()
        self.rot.start()
        
        self.adb = AdbClient()
        self.adb.start()
        
        self.mouse_down = False
        self.mouse_time = 0
        self.mouse_inmenu = False
        
        self.show_menu = False
        self.show_menu_time = 0

        self.show_nav = False

        #image scale orig to disp
        self.scale = self.orig[0] / float(self.size[0])
        self.ratio = self.orig[0] / float(self.orig[1])
        #size of raw image in landscape mode
        self.sizel = self.size[0], int(self.orig[1] / self.scale)
        #size of raw image in portrait mode
        self.sizep = int(self.orig[1] / self.scale), self.size[0]

        self.rotation = 0

        self.calc_scale()

        pygame.init()
        pygame.font.init()
        
        
        """
        self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE | pygame.HWSURFACE)
        pygame.display.set_caption("cj")
        """
        print "---------"
        print(BASE_DIR)
        
        self.color = (200, 200, 200)
        font = pygame.font.Font(BASE_DIR + "/res/fontawesome.ttf", 70)
        self.img_close = font.render(u'\uf00d', True, self.color)
        self.img_portrait = font.render(u'\uf10b', True, self.color)
        self.img_landscape = pygame.transform.rotate(self.img_portrait, 90)
        self.img_bars = font.render(u'\uf0c9', True, self.color)
        
        font = pygame.font.Font(BASE_DIR + "/res/fontawesome.ttf", 30)
        img_back = font.render(u'\uf053', True, self.color)
        img_home = font.render(u'\uf015', True, self.color)
        img_box = font.render(u'\uf009', True, self.color)
        
        self.menu_w = int(self.size[0] * MENU_WIDTH / 100.0)
        self.menu_h = int(self.size[1] / 3)
        self.update_menu()
        
        self.nav_w = int(self.size[0] * NAV_WIDTH / 100.0)
        
        self.img_nav = pygame.Surface((self.nav_w, self.size[1]))
        self.blit_center(self.img_nav, img_box, (0, 0, self.nav_w, self.menu_h))
        self.blit_center(self.img_nav, img_home, (0, self.menu_h, self.nav_w, self.menu_h))
        self.blit_center(self.img_nav, img_back, (0, self.menu_h * 2, self.nav_w, self.menu_h))
        
        #pub = rospy.Publisher('chatter', String, queue_size=10)
        self.pub = rospy.Publisher('usb_cam/image_raw', Image, queue_size=50)
        self.bridge = CvBridge()
       
        self.rate = rospy.Rate(1) # 10hz

    def update_menu(self):
        self.img_menu = pygame.Surface((self.menu_w, self.size[1]))
        
        self.blit_center(self.img_menu, self.img_close, (0, 0, self.menu_w, self.menu_h))
        if self.landscape:
            self.blit_center(self.img_menu, self.img_portrait, (0, self.menu_h, self.menu_w, self.menu_h))
        else:
            self.blit_center(self.img_menu, self.img_landscape, (0, self.menu_h, self.menu_w, self.menu_h))
        self.blit_center(self.img_menu, self.img_bars, (0, self.menu_h * 2, self.menu_w, self.menu_h))


    def calc_scale(self):
        self.landscape = self.rotation in [90, 270]
        
        if self.show_nav:
            max_w = self.size[0] - self.nav_w      
        else:            
            max_w = self.size[0]
 
        if self.landscape:
            x = 0
            w = max_w 
            if self.scalel:
                h = self.size[1]
                y = 0
            else:
                h = w / self.ratio
                y = (self.size[1] - h) / 2
        else:
            y = 0
            h = self.size[1]
            if self.scalep:
                x = 0
                w = max_w
            else:
                w = h / self.ratio
                x = (self.size[0] - w) / 2
        
        print x,y,w,h
        self.proj = map(int, [x, y, w, h]) 
        self.frame_update = True
        
    def blit_center(self, dst, src, rect):
        x = rect[0] - int((src.get_width() / 2) - (rect[2] / 2))
        y = rect[1] - int((src.get_height() / 2) - (rect[3] / 2))
        dst.blit(src, (x, y)) 
        
    def exit(self):
        self.running = False
        
        self.cap.write(["end"])
        self.touch.write(["end"])
        self.rot.write(["end"])
        self.adb.write(["end"])        
        
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exit()
               
            if hasattr(event, "pos"):
                ix, iy = event.pos
                self.mouse_inmenu = ix <= self.size[1] * MENU_BORDER / 100.0
                
                fx = min(max(0, (ix - self.proj[0]) / float(self.proj[2])), 1)
                fy = min(max(0, (iy - self.proj[1]) / float(self.proj[3])), 1)

                if self.rotation == 0:
                    x = fx
                    y = fy

                if self.rotation == 90:
                    x = 1.0 - fy
                    y = fx
                    
                if self.rotation == 180:
                    x = 1.0 - fx
                    y = 1.0 - fy   
                
                if self.rotation == 270:
                    x = fy
                    y = 1.0 - fx                                 
            
            if hasattr(event, "button"):
                if event.button is not 1:
                    continue
                  
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if ix < self.menu_w and self.show_menu:
                        self.menu_action(iy / (self.size[1] / 3))
                    elif ix > self.size[0] - self.nav_w and self.show_nav:
                        self.nav_action(iy / (self.size[1] / 3))
                    else:
                        self.touch.write(["down", x, y])
                        self.mouse_down = True
                        self.mouse_time = time()
                
                if event.type == pygame.MOUSEBUTTONUP:
                    self.touch.write(["up"])
                    self.mouse_down = False
   
            if event.type == pygame.MOUSEMOTION:
                if self.mouse_down:
                    self.touch.write(["move", x, y])
                    

    def nav_action(self, but):
        if but == 0:
            self.adb.write(["apps"])
        if but == 1:
            self.adb.write(["home"])
        if but == 2:
            self.adb.write(["back"])


    def menu_action(self, but):
        if but == 0:
            self.exit()
        if but == 1:
            if self.landscape:
                self.adb.write(["portrait"])
            else:
                self.adb.write(["landscape"])
        if but == 2:
            self.show_nav = not self.show_nav
            self.calc_scale()

        self.show_menu = False
          
    def menu_loop(self):
        if self.mouse_down and time() - self.mouse_time > MENU_TAP and self.mouse_inmenu:
            self.show_menu = True
            self.screen_update = True
            self.show_menu_time = time()

        if self.show_menu and time() - self.show_menu_time > MENU_TIMEOUT:
            self.show_menu = False
            self.screen_update = True
    
    def run(self):
        self.running = True
        self.adb.write(["portrait"])

        self.screen_update = True
        self.frame_update = True
        print "---------%s" % self.size 
        frame_cache = pygame.Surface(self.size)
        last_frame = None
        
        while not rospy.is_shutdown():
            self.events()
 
            for msg in self.rot.read():
                cmd = msg[0]
                if cmd == "rot":
                    self.rotation = msg[1]
                    self.calc_scale()
                    self.update_menu()

            #we will process only one frame at the time
            msgs = self.cap.read()
            msgl = len(msgs)
            if msgl:
                msg = msgs[msgl - 1]
                cmd = msg[0]

                if cmd == "data":
                    img = cv2.imdecode(np.frombuffer(msg[1], np.uint8), cv2.IMREAD_COLOR)
                    last_frame = self.bridge.cv2_to_imgmsg(img, encoding="bgr8")
                    self.frame_update = True


            if self.frame_update:
                self.frame_update = False
                if last_frame is not None:
                    try:
                        self.pub.publish(last_frame)
                    except CvBridgeError as e:
                        e
                    
                    self.rate.sleep()               
            
                    

            for msg in self.adb.read():
                cmd = msg[0]
                if cmd == "end":
                    self.exit()
            

if __name__ == '__main__':
    try:
        rospy.init_node('screencap', anonymous=True)
        cap = screencap()
        cap.run()
    except rospy.ROSInterruptException:
        pass
