# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: game logic
"""

from gameobject import GameObject
from card_define import *
from log import *
import copy

class HandleManger(GameObject):
    def __init__(self, player):
        self.player = player
        self.resetDataPerGame()
        self.setAllowAction2CallbackDict()
        self.setAction2CallbackDict()


    def resetDataPerGame(self):

        self.cards = [] #手牌列表
        self.myCardsCount = 17

        self.discardCards = [] #已经打出的牌列表

        self.color2cards = {} #牌花色对应的牌列表
        self.card2count = {} #每张牌的数量(不分花色)

        self.action2balanceCards = {DISCARD:[]}

        #万能牌，可变成任意牌的牌
        self.wildCardList = []

    def setWildCard(self, cardList): #设置万能牌
        self.wildCardList = cardList

    def cleanGhostList(self): #清空万能牌列表
        self.wildCardList = []

 #++++++++++++++++++++ action相关 ++++++++++++++++++++


    def setAllowAction2CallbackDict(self):
        '''
        '''
        self.allowAction2Callback = {
            DISCARD: self.getDiscardList,
        }

    def getDiscardList(self):
        pass

    def getAllowActionNCards(self, allowActions = ()):
        '''
        获得允许进行的action
        '''
        actionNcards = {}
        for action in allowActions:
            cards = self.allowAction2Callback[action]()
            if cards:
                actionNcards[action] = cards
        log(u'[getAllowActionNCards] allowActions[%s] actionNcards[%s]'\
            %(allowActions,actionNcards), LOG_LEVEL_RELEASE)
        return actionNcards

    def setAction2CallbackDict(self):
        '''
        '''
        self.doAction2callback = {
            PASS: self.doPass,
            DISCARD: self.doDiscard,
        }

    def doCurAction(self, action, cardList):
        '''
        执行操作
        '''
        log(u'[doCurAction] action[%s] cardList[%s]'%(action,cardList), LOG_LEVEL_RELEASE)
        if action not in self.doAction2callback:
            log(u'[doCurAction] action not in actions', LOG_LEVEL_RELEASE)
            return []
        return self.doAction2callback[action](cardList)

    def doPass(self, cardList):
        '''
        进行过操作
        '''
        self.player.lastDiscard = ['pass']
        log(u'[doPass] cardList[%s]'%(cardList), LOG_LEVEL_RELEASE)
        return []

    def doDiscard(self, cardList):
        '''
        进行出牌操作
        '''
        log(u'[doDiscard] cardList[%s]'%(cardList), LOG_LEVEL_RELEASE)
        if not cardList:
            log(u'[doDiscard][error] no cardList', LOG_LEVEL_RELEASE)
            return []
        _len = len(cardList)
        cards = cardList[0].split(',')
        for card in cards:
            if card not in self.cards:
                log(u'[doDiscard][error] card[%s] not in cards[%s]'%(card,self.cards), LOG_LEVEL_RELEASE)
                return []
        newCards = cards[:]
        useWildCard = []
        if _len == 2:
            substituteCards = cardList[1].split(',')
            wildCard = self.wildCardList[0][0]
            log(u'[doDiscard] substituteCards[%s] wildCard[%s]'%(substituteCards,wildCard), LOG_LEVEL_RELEASE)
            for c in cards:
                if c[0] == wildCard:
                    newCards.remove(c)
                    useWildCard.append(c)
            newCards.extend(substituteCards)
        if self.isValidDiscard(newCards[:], useWildCard):
            self.dealDiscardData(cards)
            self.player.lastDiscard = newCards
            print 'aaaaaa', newCards
            return newCards
        return []

    def isValidDiscard(self, cards, useWildCard = []):
        log(u'[isValidDiscard] cards[%s]'%(cards), LOG_LEVEL_RELEASE)
        return False

    def dealDiscardData(self, cards):
        log(u'[dealDiscardData] cards[%s]'%(cards), LOG_LEVEL_RELEASE)
        self._rmCards(cards)
        self.discardCards.append(cards)

    def getBalanceCards(self):
        # balanceCards = self.cards[:]
        balanceCards = ','.join(self.cards)
        return [balanceCards]

 #++++++++++++++++++++ action相关end ++++++++++++++++++++


 #++++++++++++++++++++ 添加移除牌相关 ++++++++++++++++++++

    def _addCards(self, cards = []):
        '''
        添加一组牌
        '''
        self.cards.extend(cards)
        log(u'[_addCards] cards[%s] self.cards[%s]'%(cards, self.cards), LOG_LEVEL_RELEASE)

    def _rmCards(self, cards = []):
        '''
        移除一组牌
        '''
        for card in cards:
            self.cards.remove(card)
        log(u'[_rmCards] cards[%s] self.cards[%s]'%(cards, self.cards), LOG_LEVEL_RELEASE)

    def setMyCardCount(self):
        '''
        设置手牌数
        '''
        pass

    def setHandCards(self, cards):
        '''
        设置手牌
        '''
        cards = self.cardSort(cards)
        self.cards = cards
        log(u'[setHandCards] cards[%s]'%(cards), LOG_LEVEL_RELEASE)

    def getNeedCardCount(self):
        '''
        获得需要补的牌数
        '''
        pass


 #++++++++++++++++++++ 添加移除牌相关end ++++++++++++++++++++


 #++++++++++++++++++++ 通用工具函数 ++++++++++++++++++++

    def cardSort(self, cards):
        if not cards:
            return cards
        log(u'[cardSort_S] cards[%s]'%(cards), LOG_LEVEL_RELEASE)
        cards = sorted(cards, key=lambda x:x[1] , reverse = True)
        sortedCards = sorted(cards, key=lambda x:card2val_map[x[0]] , reverse = True)
        log(u'[cardSort_E] sortedCards[%s]'%(sortedCards), LOG_LEVEL_RELEASE)
        return sortedCards

    def checkCard(self, card):
        '''
        检测有无此牌
        '''
        if card in self.cards:
            return True
        return False

    def getDiscardCards(self):
        '''
        返回出过的牌列表
        '''
        return self.discardCards

    def getCards(self):
        '''
        返回手牌列表
        '''
        return self.cards

 #++++++++++++++++++++ 通用工具函数end ++++++++++++++++++++

