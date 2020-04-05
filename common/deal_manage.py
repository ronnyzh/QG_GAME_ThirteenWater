#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    发牌管理器
"""
from gameobject import GameObject
from common.log import log, LOG_LEVEL_RELEASE
from common.card_define import *
import copy
import random
import re

class DealMgr(GameObject):
    """
    发牌管理器
    """
    def __init__(self, game):
        """
        """
        self.game = game
        self.getDealSetting()
        self.origPoolCards = self.createCards()
        self.poolCards = self.origPoolCards[:]
        self.setCtrlTypes()
        # 记录GM命令数据
        self.getCards4GM = {}
        self.perSideCards = {}

    def deal(self):
        """
        打乱牌
        """
        self.shuffleCards(self.poolCards)
        log(u'[deal] poolCards[%s]'%(self.poolCards),LOG_LEVEL_RELEASE)

    def resetCards(self):
        """
        得到一副牌
        """
        self.poolCards = self.origPoolCards[:]
        log(u'[resetCards] poolCards[%s]'%(self.poolCards),LOG_LEVEL_RELEASE)

    def getTotalCards(self):
        """
        返回牌组的总长度
        """
        return len(self.origPoolCards)

    def setCtrlTypes(self):
        """
        GM类型到相应记录数据方法的映射
        """
        self.ctrlTypes = {
            GET_CARDS  :  self.onGetCards4GM,
        }

    def getDealSetting(self):
        """
        设置发牌器参数
        """
        self.setting = {
            #一副牌
            'REPEAT_COUNT'         :    1,
            #手牌张数
            'HAND_CARDS_COUNT'     :    17,
            #大小王
            'JOKER_CARDS'          :    [LITTLE_JOKER,BIG_JOKER],
            #花色列表
            'COLOR_LIST'           :    color_set,
            #牌值字串列表
            'CARD_LIST'            :    card_set,
            #移除的牌列表
            'REMOVE_CARDS'         :    [],
            #增加的牌列表
            'EXTEND_CARDS'         :    [],
        }

    def shuffleCards(self, cards):
        """
        洗牌方法
        """
        random.shuffle(cards)

    def _doDealCards(self, cardNums):
        """
        处理发牌数据
        """
        lenPoolCards = len(self.poolCards)
        if cardNums > lenPoolCards:
            log(u'[_doDealCards] cardNums[%s] > lenPoolCards[%s]'\
                %(cardNums, lenPoolCards),LOG_LEVEL_RELEASE)
            return
        playerCards = self.poolCards[:cardNums]
        self.poolCards = self.poolCards[cardNums:]
        return playerCards

    def _doAddCards(self, cards):
        self.poolCards.extend(cards)
        log(u'[_doAddCards] cards[%s] poolCards[%s]'%(cards, self.poolCards),LOG_LEVEL_RELEASE)

    def _checkCardInList(self, cards, cardList):
        cardInList = []
        cardOutList = []
        for c in cards:
            if c[0] in cardList:
                cardInList.append(c)
            else:
                cardOutList.append(c)
        log(u'[_checkCardInList] cards[%s] cardList[%s] cardInList[%s] cardOutList[%s]' \
            %(cards, cardList, cardInList, cardOutList),LOG_LEVEL_RELEASE)
        return cardInList, cardOutList

    def dealCards(self, side):
        """
        发牌(GM)
        """
        cardNums = self.setting['HAND_CARDS_COUNT']
        log(u'[dealCards0] getCards4GM[%s]'%(self.getCards4GM),LOG_LEVEL_RELEASE)
        if self.getCards4GM.has_key(side):
            handCards = self.getCards4GM[side][:]
            handCardsVal = [c[0] for c in handCards]
            del self.getCards4GM[side]
            setNums = len(handCards)
            needCards = []
            if setNums < cardNums:
                needCounts = cardNums - setNums
                loopCount = 0
                while needCounts:
                    loopCount += 1
                    _curCards = self._doDealCards(needCounts)
                    cardInList, cardOutList = self._checkCardInList(_curCards, handCardsVal)
                    needCounts = len(cardInList)
                    needCards.extend(cardOutList)
                    self._doAddCards(cardInList)
                    log(u'[dealCards] _curCards[%s] needCards[%s] cardInList[%s] cardOutList[%s]' \
                        %(_curCards, needCards, cardInList, cardOutList),LOG_LEVEL_RELEASE)
                    if loopCount > 80:
                        log(u'[dealCards] GM get card fail.',LOG_LEVEL_RELEASE)
                        # self._doAddCards(handCards)
                        _curCards = self._doDealCards(needCounts)
                        needCards.extend(_curCards)
                        break
                        # return self._doDealCards(needCounts)
                print 'dealCards111111',needCards, handCards, self.poolCards
                handCards.extend(needCards)
                print 'dealCards111111', handCards
            return handCards[:cardNums]
        return self._doDealCards(cardNums)

    def dealGMData(self):
        if not self.getCards4GM:
            return
        for side in self.getCards4GM.keys():
            handCards = self.getCards4GM[side]
            canUse = True
            for card in handCards:
                if self.poolCards.count(card) < handCards.count(card):
                    canUse = False
                    del self.getCards4GM[side]
                    break
            if canUse:
                cardNums = self.setting['HAND_CARDS_COUNT']
                if len(handCards) > cardNums:
                    handCards = handCards[:cardNums]
                for card in handCards:
                    self.poolCards.remove(card)

    def getEachHands(self):
        """
        获得所有边玩家的手牌
        """
        playerCount = self.game.maxPlayerCount
        eachCards = ['']*playerCount
        self.dealGMData()
        for side in xrange(playerCount):
            eachCards[side] = self.dealCards(side)
            self.perSideCards[side] = eachCards[side]
        log(u'[getEachHands] eachCards[%s]'%(eachCards),LOG_LEVEL_RELEASE)
        return eachCards

    def createCards(self):
        """
        生成牌列表
        """
        poolCards = []
        for card in self.setting['CARD_LIST']:
            for color in self.setting['COLOR_LIST']:
                poolCards.append(card+color)
        jokerCards = self.setting['JOKER_CARDS']
        if jokerCards:
            poolCards.extend(jokerCards)
        repeatCount = self.setting['REPEAT_COUNT']
        if repeatCount > 1:
            poolCards *= repeatCount

        extendCardList = self.setting['EXTEND_CARDS']
        poolCards.extend(extendCardList)

        remCards = self.setting['REMOVE_CARDS']
        for card in remCards:
            poolCards.remove(card)

        log(u'[createCards] poolCards[%s]'%(poolCards),LOG_LEVEL_RELEASE)
        return poolCards

    def onGetCards4GM(self, side, data):
        data = reCards.findall(data)
        self.getCards4GM[side] = data
        print 'onGetCards4GM', data


if __name__ == "__main__":
    dealMgr = DealMgr()
    dealMgr.deal()
    print dealMgr.cards
    
 





