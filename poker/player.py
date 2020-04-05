# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: Player peer
"""

from common.common_player import CommonPlayer
from handle import Handel
from common.card_define import *
from common.log import *
from consts import *

class Player(CommonPlayer):
    def __init__(self):
        super(Player, self).__init__()
        #结算相关数据
        self.resetPerGame()
        self.totalShootCount = 0
        self.totalAllShootCount = 0
        self.totalSpeCount = 0

    def __str__(self):
        return '(account[%s] nickname[%s] side[%s] curScore[%s])' \
            %(self.account, self.nickname, self.chair, self.curGameScore)

    def resetPerGame(self):
        super(Player, self).resetPerGame()
        # 每墩类型[头,中,尾]
        self.perPierType = []
        self.defaultType = []
        self.perCards = []
        self.defaultCards = []
        self.hasHorse = False

        self.multiple = 0
        # 特殊牌型分
        self.specialScore = []
        self.pierTotalScore = {0:[0, 0], 1:[0, 0], 2:[0, 0]}
        self.arranged = False
        self.curScore = 0
        self.basePierTotalScore = 0
        self.shootScore = 0
        self.tmpGameScore = 0
        self.isDealer = False
        self.speScoreStr = ''
        self.isSureCards = False

    def getBalanceDescs(self):
        descs = []

        # 有马
        desc = ('%s'%(self.hasHorse)).decode('utf-8')
        descs.append(desc)

        shootDict = self.game.shootDict
        side = self.chair
        if shootDict.has_key(side):
            beShootSides = shootDict[side]
            shootCount = len(beShootSides)
            # 打枪
            if self.game.isAllShoot(shootCount):
                desc = '全垒打'.decode('utf-8')
                self.totalAllShootCount += 1
            else:
                desc = ('打枪x%s'%(shootCount)).decode('utf-8')
                self.totalShootCount += shootCount
        else:
            desc = ('').decode('utf-8')
        descs.append(desc)

        # 中枪
        beShootCount = 0
        for vals in shootDict.values():
            if side in vals:
                beShootCount += 1
        if beShootCount > 0:
            desc = ('中枪x%s'%(beShootCount)).decode('utf-8')
        else:
            desc = ('').decode('utf-8')
        descs.append(desc)

        # 倍数
        if self.game.hasDoODealer and not self.isDealer:
            desc = ('%s'%(self.multiple)).decode('utf-8')
        else:
            desc = ('').decode('utf-8')
        descs.append(desc)

        return descs

    def updateScore(self, pierNo, deltaScore, speScore=0, baseScore=0):
        # log(u'[updateScore] pierNo[%s] deltaScore[%s] speScore[%s] baseScore[%s].' \
            # %(pierNo, deltaScore, speScore, baseScore), LOG_LEVEL_RELEASE)
        if deltaScore == 0:
            return
        self.curScore += deltaScore
        if pierNo > 2:
            return
        scoreList = self.pierTotalScore[pierNo]
        scoreList[0] += baseScore
        scoreList[1] += speScore

    def checkSpecialType(self):
        return self.handleMgr.checkSpecialType()

    def getSpecialType(self):
        return self.handleMgr.getSpecialType()

    def getPierIns(self):
        return self.handleMgr.perPierIns

    def setSpecialScore(self):
        SIX_PAIRS = 13
        perPierType = self.perPierType
        if perPierType:
            specialScore = [0, 0, 0]
            for pierNo, type in enumerate(perPierType):
                score = self.game.getSpecialScore(type, pierNo)
                if type == SIX_PAIRS:
                    score = self.game.getSixPairsScore(self.perCards[0].split(','))
                specialScore[pierNo] = score
            log(u'[setSpecialScore] specialScore[%s].'%(specialScore), LOG_LEVEL_RELEASE)
            self.specialScore = specialScore

    def getHandleMgr(self): #玩家手牌管理器
        return Handel(self)

    def upTotalUserData(self):
        if self.isUpdated:
            return
        self.isUpdated = True
        self.totalGameScore += self.curGameScore
        if self.curGameScore > 0:
            self.totalWinCount += 1
        if self.getSpecialType() > -1:
            self.totalSpeCount += 1

    def packTotalBalanceDatas(self):
        totalBalanceDatas = []
        data = ('打枪次数:%s'%(self.totalShootCount)).decode('utf-8')
        totalBalanceDatas.append(data)
        data = ('全垒打次数:%s'%(self.totalAllShootCount)).decode('utf-8')
        totalBalanceDatas.append(data)
        data = ('特殊牌次数:%s'%(self.totalSpeCount)).decode('utf-8')
        totalBalanceDatas.append(data)
        data = ('胜利局数:%s'%(self.totalWinCount)).decode('utf-8')
        totalBalanceDatas.append(data)
        return totalBalanceDatas

