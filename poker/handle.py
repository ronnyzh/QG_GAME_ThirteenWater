# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: game logic
"""

#from common.gameobject import GameObject
from common.handle_manger import HandleManger
from common.card_define import *
from common.log import *
# from tw_arith import *
from lj_tw_arith import *
from consts import *

import copy

class Handel(HandleManger):
    def __init__(self, player):
        super(Handel, self).__init__(player)

    def resetDataPerGame(self):
        super(Handel, self).resetDataPerGame()
        self.specialType = None
        # 实例
        self.perPierIns = []

    def setHandCards(self, cards):
        '''
        设置手牌
        '''
        super(Handel, self).setHandCards(cards)
        self.hasHorse()
        self.checkSpecialType()
        self.dealDefaultType()

    # def cardSort(self, cards):
        # if not cards:
            # return cards
        # log(u'[cardSort_S] cards[%s]'%(cards), LOG_LEVEL_RELEASE)
        # cards = sorted(cards, key=lambda x:x[1] , reverse = False)
        # sortedCards = sorted(cards, key=lambda x:card2val_map[x[0]] , reverse = False)
        # log(u'[cardSort_E] sortedCards[%s]'%(sortedCards), LOG_LEVEL_RELEASE)
        # return sortedCards

    def checkSpecialType(self):
        if self.hasJoker() or len(self.cards) != 13:
            return False
        curGame = self.player.game
        curType = getSpecialType(self.cards, not curGame.Fuqing)
        log(u'[checkSpecialType] curType[%s]'%(curType), LOG_LEVEL_RELEASE)
        if curType.get_type() == -1:
            return False
        self.specialType = curType
        log(u'[checkSpecialType] perPierIns[%s] specialType[%s]' \
            %(self.perPierIns, self.specialType), LOG_LEVEL_RELEASE)
        return True

    def checkCardsType(self, cardsList, cardTypes):
        curPlayer = self.player
        if curPlayer.isSureCards:
            log(u'[checkCardsType] curPlayer[%s] isSureCards'%(curPlayer), LOG_LEVEL_RELEASE)
            return False
        newCards = self.checkCards(cardsList)
        if not newCards:
            return False
        curType = self.getSpecialType()
        log(u'[checkCardsType] cardsList[%s] cardTypes[%s] curType[%s]' \
            %(cardsList, cardTypes, curType), LOG_LEVEL_RELEASE)
        curGame = curPlayer.game
        side = curPlayer.chair
        curPlayer.perPierType = cardTypes
        lenType = len(cardTypes)
        isSpecial = (lenType == 1 and cardTypes[0] == curType > INVALID_TYPE)
        log(u'[checkCardsType] isSpecial[%s] lenType[%s]'%(isSpecial, lenType), LOG_LEVEL_RELEASE)
        if isSpecial:
            curGame.speSideNTypes.append((side, self.specialType))
            curPlayer.perCards = [self.specialType.get_cardStr()]
            curPlayer.isSureCards = True
            return True
        if lenType < 3:
            return False
        if curType > INVALID_TYPE:
            self.specialType = None
        if not (cardTypes[0] <= cardTypes[1] <= cardTypes[2]):
            return False
        perPierIns = []
        specialScore = []
        comSideNIns = copy.deepcopy(curGame.comSideNIns)
        for pierNo, cards in enumerate(newCards):
            # cNjStrs = cardsStr.split(';')
            # cards = cNjStrs[0].split(',')
            curTypeIns = CardsModelFactory(cards)
            type = cardTypes[pierNo]
            if type != curTypeIns.get_type():
                return False
            perPierIns.append(curTypeIns)
            comSideNIns[pierNo].append((side, curTypeIns))
            specialScore.append(curGame.getSpecialScore(curTypeIns.get_type(), pierNo))

        curPlayer.perCards = cardsList
        self.perPierIns = perPierIns
        curGame.comSideNIns = comSideNIns
        curComSides = curGame.comSides
        if side not in curComSides:
            curComSides.append(side)
        curPlayer.specialScore = specialScore
        curPlayer.setSpecialScore()
        curPlayer.isSureCards = True
        log(u'[checkCardsType] perPierIns[%s] comSideNIns[%s] comSides[%s] specialScore[%s]' \
            %(perPierIns, comSideNIns, curComSides, specialScore), LOG_LEVEL_RELEASE)
        return True

    def checkCards(self, cardsList):
        # print '44444444', cardsList
        if not cardsList:
            return True
        newCards = []
        allCards = []
        for cardsStr in cardsList:
            cNjStrs = cardsStr.split(';')
            _cards = cNjStrs[0].split(',')
            newCards.append(_cards)
            allCards.extend(_cards)
        # print '5555555', newCards, allCards, self.cards
        for card in set(allCards):
            if allCards.count(card) > self.cards.count(card):
                log(u'[checkCards] error: allCards[%s] cards[%s]'%(allCards, self.cards), LOG_LEVEL_RELEASE)
                return []
        return newCards

    def hasJoker(self):
        return (LITTLE_JOKER in self.cards or BIG_JOKER in self.cards)

    def hasHorse(self):
        curGame = self.player.game
        if not curGame.hasHorse:
            return False
        horseCard = NO2CARD[curGame.horseCard]
        if horseCard in self.cards:
            self.player.hasHorse = True
            print 'hasHorse is True'
            return True
        return False

    def getSpecialType(self):
        if self.specialType is None:
            return -1
        return self.specialType.get_type()

    def dealDefaultType(self):
        """
        处理默认牌型
        """
        curPlayer = self.player
        curType = self.getSpecialType()
        if curType != INVALID_TYPE:
            curTypeIns = self.specialType
            curPlayer.defaultCards = [curTypeIns.get_cardStr()]
            curPlayer.defaultType = [curType]
            return
        perPierIns = getDefaultType(self.cards)
        perPierIns.reverse()
        defaultCards = []
        defaultType = []
        for pierIns in perPierIns:
            defaultCards.append(pierIns.get_cardStr())
            defaultType.append(pierIns.get_type())
        log(u'[dealDefaultType] defaultCards[%s] defaultType[%s]'%(defaultCards, defaultType), LOG_LEVEL_RELEASE)
        curPlayer.defaultCards = defaultCards
        curPlayer.defaultType = defaultType

    def sortedCards(self, cards):
        valStr2Count = {}
        # cards = sorted(cards, key=lambda x:x[1] , reverse = True)
        log(u'[sortedCards] cards[%s]'%(cards), LOG_LEVEL_RELEASE)
        for c in cards:
            valStr = c[0]
            if valStr2Count.has_key(valStr):
                valStr2Count[valStr] += 1
            else:
                valStr2Count[valStr] = 1
        log(u'[sortedCards] valStr2Count[%s]'%(valStr2Count), LOG_LEVEL_RELEASE)
        count2valStr = {1:[], 2:[], 3:[], 4:[]}
        for key, val in valStr2Count.items():
            count2valStr[val].append(key)
        valStrSetList = []
        for i in [4, 3, 2, 1]:
            valStrs = count2valStr[i]
            valStrs = sorted(valStrs, key=lambda x:card2val_map[x] , reverse = True)
            log(u'[sortedCards] i[%s] valStrs[%s]'%(i, valStrs), LOG_LEVEL_RELEASE)
            valStrSetList.extend(valStrs)
        log(u'[sortedCards] valStrSetList[%s]'%(valStrSetList), LOG_LEVEL_RELEASE)
        newCards = []
        for valStr in valStrSetList:
            valStrCards = [card for card in cards if card[0] == valStr]
            newCards.extend(valStrCards)
        log(u'[sortedCards] newCards[%s]'%(newCards), LOG_LEVEL_RELEASE)
        return newCards

if __name__ == '__main__':
    handlMgr = Handel()




