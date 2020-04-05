#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    发牌管理器
"""
from common.deal_manage import DealMgr
from common.card_define import *
from common.log import log, LOG_LEVEL_RELEASE
from consts import *

import random
import re

GET_WILD_CARDS = 3

class DealMange(DealMgr):
    """
    发牌管理器
    """
    def __init__(self, game):
        """
        """
        self.setCardDefine()
        super(DealMange, self).__init__(game)

    def setCardDefine(self):
        val2card_map[2] = '2'
        card2val_map['2'] = 2

    def getDealSetting(self):
        """
        设置发牌器参数
        """
        super(DealMange, self).getDealSetting()
        self.setting['HAND_CARDS_COUNT'] = 13
        self.setting['COLOR_LIST'] = self.getColorList()
        if not self.game.hasJoker:
            self.setting['JOKER_CARDS'] = []

    def getColorList(self):
        colorList = [SPADE, HEART, CLUB, DIAMOND]
        playerCount = self.game.maxPlayerCount
        curPlayWay = self.game.playWay
        log(u'[getColorList] playerCount[%s] curPlayWay[%s]'%(playerCount, curPlayWay),LOG_LEVEL_RELEASE)
        if playerCount <= 4:
            colorCount = 4 + curPlayWay
        else:
            colorCount = playerCount + curPlayWay
        return self._getListByCount(colorCount)

    def _getListByCount(self, colorCount):
        baseColorList = [SPADE, HEART, CLUB, DIAMOND]
        quotients, remainders = colorCount/4, colorCount%4
        curColorList = baseColorList[:]*quotients
        curColorList.extend(baseColorList[:remainders])
        log(u'[_getListByCount] colorCount[%s] quotients[%s] remainders[%s] curColorList[%s]' \
            %(colorCount, quotients, remainders, curColorList),LOG_LEVEL_RELEASE)
        return curColorList

    def setCtrlTypes(self):
        """
        GM类型到相应记录数据方法的映射
        """
        super(DealMange, self).setCtrlTypes()


