# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    游戏内信息，用于玩家加入后同步桌内所有玩家及鱼数据
{
    "roomId"        :   0,                      房间ID
    "rommName"      :   "",                     房间名字
    "timestamp"     :   0,                      以毫秒为单位的整型数字时间戳
    "bgIdx"         :   0,                      背景索引号，范围1-3
    "playerList"    :   [{"side", "nickname", "vipLevel", "coin", "level", "gunType", "gunLevel", "gunCoin", "gunDirX", "gunDirY"}, ...]         已在房间的玩家数据列表
    "bufferList"    :   [],                     游戏buffer列表，暂不用
    "fishList"      :   [{"id", "level", "route"}, ...],                                                已存在的鱼数据列表
}
"""

from common.gameobject import GameObject

class GameInfo(GameObject):
    def __init__(self):
        #房间Id，暂时无用
        self.roomId = 0
        #房间名称，暂时无用
        self.roomName = ""
        self.timestamp = 0
        self.playerList = []
        self.bufferList = []
        self.fishList = []

    def addFishData(self, id, level, timestamp, initRot, initX, initY, route):
        """
        "id"        :   0,                          鱼id
        "level"     :   0,                          鱼等级（或者称鱼类型）
        "timestamp" :   0,                          鱼出生的时间戳
        "rot"       :   0,                          起始的朝向角度(0-359)
        "x"         :   0,                          鱼的起始坐标点
        "y"         :   0,                          
        "route" :   [                           鱼路径状态列表
            {
                "rotSpeed"      :   0,          旋转角速度，单位角度/秒，0表示不会转
                "speed"         :   0,          移动速度，单位pixel/s，客户端需要做与设计场景比例的速度缩放
                "duration"      :   0,          移动间隔时间，单位秒
            }
        ]
        """
        self.fishList.append(
            {
                "id"            :   id,
                "level"         :   level,
                "timestamp"     :   timestamp,
                "rot"           :   initRot,
                "x"             :   initX,
                "y"             :   initY,
                "route"         :   route,
            }
        )

    def addPlayerData(self, side, nickname, vipLevel, coin, level, gunType, gunLevel, gunCoin, gunDirX, gunDirY):
        self.playerList.append(
            {
                "side"          :   side,
                "nickname"      :   nickname,
                "vipLevel"      :   vipLevel,
                "coin"          :   coin,
                "level"         :   level,
                "gunType"       :   gunType,
                "gunLevel"      :   gunLevel,
                "gunCoin"       :   gunCoin,
                "gunDirX" :   gunDirX,
                "gunDirY" :   gunDirY,
            }
        )
