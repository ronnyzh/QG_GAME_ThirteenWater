# -*- coding: utf-8 -*-
"""
分数管理器
"""

from gameobject import GameObject
# from common import consts
# from common.log import log, LOG_LEVEL_RELEASE
# from common_player import CommonPlayer

# from common.protocols.mahjong_consts import *
from common_db_define import *
# from card_define import *

# import mahjong_pb2
# import replay4proto_pb2
# from pb_utils import *
import random
# import time
# from datetime import datetime
# import copy
# import redis_instance
# import re


class ScoreMgr(GameObject):
    """
    """
    def __init__(self,server):
        """
        self.side2scores = {
            0   :   [0,0,0]
        }
        """
        self.server = server
        self.type2score = self.setBaseActionScore()
        self.type2scoreLen = len(self.type2score)
        self.score = 0
        self.scoreRound = 0
        # 玩家总得分列表[HU(胡),KONG(杠),CANCELKONG(暗杠)]
        self.scoreListTotal = []
        # 玩家单局得分列表[HU(胡),KONG(杠),CANCELKONG(暗杠)]
        self.scoreListRound = [0]*self.type2scoreLen
        
        """
        Action统计
        [HU(胡),KONG(杠),CANCELKONG(暗杠),PONG(碰),CHOW(吃),BEKONG(放杠),BEBOOM(放炮)]
        """

        self.actionCount = [0] * 7
        #每局碰杠次数统计
        self.actionCountRound = [0] * 7

    def resetScoreData(self):
        pass
        
    def setBaseActionScore(self):
        """
        设置配置文件，由上层重写
        """
        return {
            HU             :         2,
            KONG           :         1,
            CANCELKONG     :         2,
        }
        
        
    def onAction(self, action, *args):
        if self.type2score.has_key(action):
            self.scoreListRound[action] += self.type2score[action]
        self.actionCount[action] += 1
        self.actionCountRound[action] += 1
        
    def __setScore(self,score):
        """
        累积改玩家分数
        """
        self.score+=score

    def getTotalScore(self):
        """
        获取最后输赢总分
        """
        return self.score

    def getWinScore(self,*args):
        """
        抽象方法
        """
        return None

    def getLossScore(self,*args):
        """
        抽象方法
        """
        return None

    def setActionCount(self,action):
        """
        统计玩家action次数
        actionCount = {
            'HU'        :   1,//碰1次
            'KONG'      :   1 //杠1次
        }
        """
        self.actionCount[action]+=1
        self.actionCountRound[action]+=1

    def getActionCount(self,action=None):
        """
        返回相应Action次数
        """
        if action:
            return  self.actionCount[action]

        return self.actionCount

    def resetData(self):
        """
        重置数据
        """
        self.actionCountRound = [0] * 7
        self.scoreRound = 0