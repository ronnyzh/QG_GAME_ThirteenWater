# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
鱼路径节点
"""

from common.gameobject import GameObject

class RouteNode(GameObject):
    def __init__(self, rotSpeed, speed, duration):
        self.rotSpeed = rotSpeed
        self.speed = speed
        self.duration = duration