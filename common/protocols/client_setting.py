#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    客户端设置
"""

from common.gameobject import GameObject

class ClientSetting(GameObject):
    def __init__(self):
        self.musicVolume = 0.0
        self.soundVolume = 0.0
        self.coinTransferPerTime = 0
