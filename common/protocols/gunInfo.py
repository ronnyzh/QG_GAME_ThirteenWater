# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
Gun Levels
"""
from common.gameobject import GameObject

class GunInfo(GameObject):
    def __init__(self, level, coinRange, stepCoin):
        self.level = level
        self.coinRange = coinRange
        self.stepCoin = stepCoin
