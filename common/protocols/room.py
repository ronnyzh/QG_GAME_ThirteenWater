# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: Room Info
"""
from common.gameobject import GameObject

class RoomInfo(GameObject):
    def __init__(self, room_type, room_sub_type, rate, min_coin, max_coin, max_player_count, gunLevels):
        self.type = room_type
        self.subType = room_sub_type
        self.rate = rate
        self.playerCount = 0
        self.coinMin = min_coin
        self.coinMax = max_coin
        self.maxPlayerCount = max_player_count
        self.gunLevels = gunLevels

    def getGunInfo(self, level):
        _len = len(self.gunLevels)
        assert level >=0 and level < _len, "gunLevels[%d] not in range(0,%d)"%(level, 0, _len)
        return self.gunLevels[level]

    def upGunLevelNCoin(self, level, coin):
        """
        升级处理
        """
        _len = len(self.gunLevels)
        assert level >= 0 and level < _len, "gunLevels[%d] not in range(0,%d)"%(level, 0, _len)
        gunInfo = self.gunLevels[level]
        assert coin >= gunInfo.coinRange[0] and coin <= gunInfo.coinRange[1]
        #金币超出上限升级，否则只是加金币
        if coin + gunInfo.stepCoin > gunInfo.coinRange[1]:
            #最大等级循环回去
            if level >= _len - 1:
                level = 0
            else:
                level += 1
            coin = self.gunLevels[level].coinRange[0]
            return level, coin
        else:
            coin += gunInfo.stepCoin
            return level, coin

    def deGunLevelNCoin(self, level, coin):
        """
        降级处理
        """
        _len = len(self.gunLevels)
        assert level >= 0 and level < _len, "gunLevel[%d] not in range(0,%d)"%(level, 0, _len)
        gunInfo = self.gunLevels[level]
        assert coin >= gunInfo.coinRange[0] and coin <= gunInfo.coinRange[1]
        #金币超出下限降级，否则只是减金币
        if coin - gunInfo.stepCoin < gunInfo.coinRange[0]:
            #最小等级循环回去
            if level <= 0:
                level = _len - 1
            else:
                level -= 1
            coin = self.gunLevels[level].coinRange[1]
            return level, coin
        else:
            coin -= gunInfo.stepCoin
            return level, coin