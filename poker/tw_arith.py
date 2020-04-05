# -*- coding: utf-8 -*-
# ===================================================== (接口)

import random
import time
import copy
from datetime import datetime

def getTimestamp():
    return int(time.time()*1000)

# ===================================================== 常量
INVALID_TYPE = -1
OOLONG = 0 #乌龙
PAIR = 1 #对子
TWO_PAIRS = 2 #两对
TRIPLET = 3 #三条(冲三)
DOUBLE_GHOST = 4 #双鬼冲头
STRAIGHT = 5 #顺子
FLUSH = 6 #同花
GOURD = 7 #葫芦
IRON_BRANCH = 8 #铁支
STRAIGHT_FLUSH = 9 #同花顺
FIVE_HEADS = 10 #五同

#特殊牌型
THREE_FLUSH = 11 #三同花
THREE_STRAIGHT = 12 #三顺子
SIX_PAIRS = 13 #六对半
FIVE_PAIRS_A_TRIPLET = 14 #五对三条
FOUR_TRIPLET = 15 #四套三条
ONE_COLOR = 16 #凑一色
ALL_SMALL = 17 #全小
ALL_BIG = 18 #全大
SIX_HEADS = 19 #六同
THREE_POINTS = 20#三分天下
THREE_STRAIGHT_FLUSH = 21 #三同花顺
TWELVE_ROYALTY = 22 #十二皇族
SEVEN_HEADS = 23 #七同
DRAGON = 24 #一条龙
SUPREME_QINGLONG = 25 #至尊青龙

FIRST_EQ = (THREE_POINTS, THREE_STRAIGHT_FLUSH, TWELVE_ROYALTY)
SECONED_EQ = (THREE_FLUSH, THREE_STRAIGHT, SIX_PAIRS, FIVE_PAIRS_A_TRIPLET, \
    FOUR_TRIPLET, ONE_COLOR, ALL_SMALL, ALL_BIG)

type2Texts = { \
    INVALID_TYPE           :        "无效牌".decode('utf-8'), \
    OOLONG                 :        "乌龙".decode('utf-8'), \
    PAIR                   :        "对子".decode('utf-8'), \
    TWO_PAIRS              :        "两对".decode('utf-8'), \
    TRIPLET                :        "三条".decode('utf-8'), \
    DOUBLE_GHOST           :        "双鬼冲头".decode('utf-8'), \
    STRAIGHT               :        "顺子".decode('utf-8'), \
    FLUSH                  :        "同花".decode('utf-8'), \
    GOURD                  :        "葫芦".decode('utf-8'), \
    IRON_BRANCH            :        "铁支".decode('utf-8'), \
    STRAIGHT_FLUSH         :        "同花顺".decode('utf-8'), \
    FIVE_HEADS             :        "五同".decode('utf-8'), \
    THREE_FLUSH            :        "三同花".decode('utf-8'), \
    THREE_STRAIGHT         :        "三顺子".decode('utf-8'), \
    SIX_PAIRS              :        "六对半".decode('utf-8'), \
    FIVE_PAIRS_A_TRIPLET   :        "五对三条".decode('utf-8'), \
    FOUR_TRIPLET           :        "四套三条".decode('utf-8'), \
    ONE_COLOR              :        "凑一色".decode('utf-8'), \
    ALL_SMALL              :        "全小".decode('utf-8'), \
    ALL_BIG                :        "全大".decode('utf-8'), \
    SIX_HEADS              :        "六同".decode('utf-8'), \
    THREE_POINTS           :        "三分天下".decode('utf-8'), \
    THREE_STRAIGHT_FLUSH   :        "三同花顺".decode('utf-8'), \
    TWELVE_ROYALTY         :        "十二皇族".decode('utf-8'), \
    SEVEN_HEADS            :        "七同".decode('utf-8'), \
    DRAGON                 :        "一条龙".decode('utf-8'), \
    SUPREME_QINGLONG       :        "至尊青龙".decode('utf-8'), \
}

LITTLE_JOKER = 'Lj'
BIG_JOKER = 'Bj'
DRAGON_VAL_LIST = xrange(2,15)
VAL_A = 14
VAL_K = 13
STRAIGHT_1_5 = [VAL_A,2,3,4,5]
STRAIGHT_1_3 = [VAL_A,2,3]

BLACK_COLOR = ('b', 'd')
RED_COLOR = ('a', 'c')
# ===================================================== 函数

def getVal2Card():
    val2card_map = {}
    for i in xrange(2, 10):
        val2card_map[i] = str(i)
    val2card_map[10] = 'T'
    val2card_map[11] = 'J'
    val2card_map[12] = 'Q'
    val2card_map[13] = 'K'
    val2card_map[14] = 'A'
    val2card_map[16] = 'L'
    val2card_map[17] = 'B'
    return val2card_map

def getCard2Val(val2card_map):
    card2val_map = {}
    for k, v in val2card_map.iteritems():
        card2val_map[v] = k
    return card2val_map

val2card = getVal2Card()
card2val = getCard2Val(val2card)
val2card[1] = 'A'

#-------------------------------------------------------------------

def dealCardDatas(cards):
    """
    处理牌数据
    """
    # print 'dealCardDatas, cards', cards
    # vals, jokers, val2cards, color2vals = dealCardsData(cards)
    vals, jokers = [], []
    val2cards, color2vals = {}, {}
    for card in cards:
        valStr, color = card
        if color == 'j':
            jokers.append(card)
            continue
        val = card2val[valStr]
        vals.append(val)
        if val2cards.has_key(val):
            val2cards[val].append(card)
        else:
            val2cards[val] = [card]
        if color2vals.has_key(color):
            color2vals[color].append(val)
        else:
            color2vals[color] = [val]

    count2vals = getCount2Vals(vals)

    print 'dealCardDatas', vals, jokers, val2cards, color2vals
    return (vals, jokers, val2cards, color2vals)

def getCount2Vals(vals):
    count2vals = {1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[]}
    valSetList = sorted(list(set(vals)), reverse = True)
    for _val in valSetList:
        valCount = vals.count(_val)
        count2vals[valCount].append(_val)
    # print 'getCount2Vals', count2vals
    return count2vals

def __compare(l, r):
    if l[1] > r[1]:
        return 1
    elif l[1] == r[1]:
        return 1 if l[0] > r[0] else -1
    else:
        return -1

def getRankFromSideNcards(sideInsList):
    """
    比对所有牌大小，牌型及牌值相同，后边的为大
    @return: 排序后的结果列表，从小到大排列
    """
    if not sideInsList:
        return [], {}
    sideInsList.sort(cmp = __compare, reverse=False)
    # print 'getRankFromSideNcards', sideInsList
    _len = len(sideInsList)
    firstTup = sideInsList[0]
    side2ltSides = {firstTup[0]:[]}
    curSideList = []

    for i in xrange(_len-1):
        sideInsTup_1 = sideInsList[i]
        sideInsTup_2 = sideInsList[i+1]
        curSideList.append(sideInsTup_1[0])

        if sideInsTup_2[1] > sideInsTup_1[1]:
            side2ltSides[sideInsTup_2[0]] = curSideList[:]
        else:
            side2ltSides[sideInsTup_2[0]] = side2ltSides[sideInsTup_1[0]]
        # if i == _len-2:
            # curSideList.append(sideInsTup_2[0])
    lastTup = sideInsList[-1]
    curSideList.append(lastTup[0])
    print 'getRankFromSideNcards_1', curSideList, side2ltSides
    return curSideList, side2ltSides

def dealStraight(vals, validStraight=[], allList=[]):
    if VAL_A in vals:
        allStraight = [xrange(10,15), STRAIGHT_1_5, xrange(12,15), STRAIGHT_1_3]
    else:
        minVal = min(vals)
        allStraight = [xrange(minVal,minVal+5), xrange(minVal,minVal+3)]
    _dealStraight(vals, allStraight, validStraight, allList)
    return allList

def _dealStraight(vals, allStraight, validStraight, allList):
    for straight in allStraight:
        curList = validStraight[:]
        if set(straight) <= set(vals):
            leftVals = _rmVals(vals, straight)
            curList.append(straight)
            _len = len(leftVals)
            if _len in [3,5,8,10,13]:
                dealStraight(leftVals, curList, allList)
            elif _len == 0:
                allList.append(curList)
            else:
                return

def _rmVals(vals, rmVals):
    curVals = vals[:]
    # print '_rmVals', vals, rmVals
    for val in rmVals:
        curVals.remove(val)
    return curVals

def val_change(vals):
    curVals = vals[:]
    if VAL_A in curVals and VAL_K not in curVals:
        curVals.remove(VAL_A)
        curVals.append(1)
    return curVals

def isJoint(vals):
    print 'isJoint_0 vals', vals
    _len = len(vals)
    if len(set(vals)) != _len:
        return False
    vals = val_change(vals)
    vals.sort()
    if vals[-1] > VAL_A:
        return False
    print 'isJoint vals', vals
    if vals[0]+_len == vals[-1]+1:
        return [vals[0]]
    return False

def getCardData(cards):
    vals, colors = [], []
    jokerCount = 0
    colorCount = 0
    for valStr, color in cards:
        if color == 'j':
            jokerCount += 1
            continue
        vals.append(card2val[valStr])
        if color not in colors:
            colors.append(color)
    colorCount = len(colors)
    print 'getCardData', vals, jokerCount, colorCount, colors
    return vals, jokerCount, colorCount

def getValData(vals):
    valSet = set(vals)
    valSetList = sorted(list(valSet), reverse = True)
    valCounts = []
    count2vals = {1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[]}
    for val in valSetList:
        valCount = vals.count(val)
        valCounts.append(valCount)
        count2vals[valCount].append(val)
    print 'getValData', valSet, valSetList, valCounts, count2vals
    return valSet, valSetList, valCounts, count2vals

#------------------------------------------------------------------

def isThreeStraightFlush(colorCounts, color2vals):
    """
    三同花顺
    [3,5,5],[3,10],[5,8],[13]
    """
    if not isThreeFlush(colorCounts):
        return False
    allList = []
    for color, vals in color2vals.items():
        vals = val_change(vals)
        lenVals = len(vals)
        print 'isThreeStraightFlush, lenVals', lenVals
        if lenVals in [3,5]:
            minValList = isJoint(vals)
            print 'minValList', minValList
            if not minValList:
                return False
            minVal = minValList[0]
            sfTup = (xrange(minVal, minVal+lenVals), color)
            if lenVals == 3:
                allList.insert(0, sfTup)
            else:
                allList.append(sfTup)
        else:
            rslt = dealStraight(vals, [], [])
            print 'rslt', rslt
            if not rslt:
                return False
            allSF = rslt[0]
            for sf in allSF:
                sfTup = (sf, color)
                if len(sf) == 3:
                    allList.insert(0, sfTup)
                else:
                    allList.append(sfTup)
    print 'allList', allList
    return allList

def isThreeStraight(vals):
    """
    三顺子
    """
    rslt = dealStraight(vals, [], [])
    print 'rslt', rslt
    return rslt

def isThreeFlush(colorCounts):
    """
    三同花
    """
    return colorCounts in ([3,5,5],[3,10],[5,8],[13])

def isFlush(vals, jokerCount, colorCount):
    """
    同花
    """
    if colorCount == 1:
        return dealFlushUseJoker(vals, jokerCount)
    return False

def dealFlushUseJoker(vals, jokerCount):
    valsSort = sorted(vals, reverse = True)
    curList = valsSort
    if jokerCount > 0:
        rsltVals = dealFlushVals(valsSort)
        threeLs, pCount, pairLs, oneLs = rsltVals
        if pairLs and jokerCount <= 1:
            jVal = pairLs[0]
            # threeLs.append(jVal)
            # pairLs.remove(jVal)
            # rsltVals[1] = pCount-1
        else:
            jVal = oneLs[0]
            # if jokerCount == 2:
                # threeLs.append(jVal)
                # oneLs.remove(jVal)
            # else:
                # pairLs.append(jVal)
                # oneLs.remove(jVal)
                # rsltVals[1] = pCount+1
        curList = [jVal]*jokerCount + valsSort
        curList = sorted(curList, reverse = True)
    print 'dealFlushUseJoker', curList
    return curList

def isStraight(vals, jokerCount, valSet):
    """
    顺子
    """
    if not(len(vals)+jokerCount == len(valSet)+jokerCount == 5):
        return False

    if jokerCount == 0:
        curList = isJoint(vals)
        if curList:
            return curList
        return False
    if valSet <= set(STRAIGHT_1_5):
        return [1]
    # vals = val_change(vals)
    minVal = min(vals)
    if minVal > 10:
        minVal = 10
    jointList = xrange(minVal, minVal+5)
    if valSet <= set(jointList):
        return [minVal]
    return False

def dealAS(val):
    return 9.5 if val == 1 else val

def dealFlushVals(vals):
    dealedVals = []
    rsltVals = [[], [], []]
    for val in vals:
        if val not in dealedVals:
            dealedVals.append(val)
            vCount = vals.count(val)
            rsltVals[3-vCount].append(val)
    pairCount = len(rsltVals[1])
    rsltVals.insert(1, pairCount)

    # print 'dealFlushVals', rsltVals
    return rsltVals

def __dealSFcards(vals, useJoker, jokers, color, val2cards):
    pierList = []
    joker2Crads = []
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
    for val in vals:
        if val == 1:
            val = VAL_A
        card = val2card[val]+color
        if val2cards.has_key(val) and card in val2cards[val]:
            pierList.append(card)
            val2cards[val].remove(card)
        else:
            joker2Crads.append(card)
    return pierList, joker2Crads

def _getCardData_FH(pierTup, val2cards, jokers):
    # print '_getCardData_FH', val2cards
    type, val, useJoker = pierTup
    pierList = []
    joker2Crads = []
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
        cardStr = val2card[val]+'d'
        joker2Crads = [cardStr]*useJoker
    # if val2cards.has_key(val):
    cards = val2cards[val]
    pierList.extend(cards[:5-useJoker])
    val2cards[val] = cards[5-useJoker:]
    # return pierList, joker2Crads
    return FiveHeads(pierList, FIVE_HEADS, [val], joker2Crads)

def _getCardData_SF(pierTup, val2cards, jokers):
    # print '_getCardData_SF', val2cards
    type, minVal, useJoker, hasVals, color = pierTup
    # vals = xrange(minVal, minVal+5)
    vals = xrange(minVal+4, minVal-1, -1)
    pierList, joker2Crads = __dealSFcards(vals, useJoker, jokers, color, val2cards)
    return StraightFlush(pierList, STRAIGHT_FLUSH, [minVal], joker2Crads)

def _getCardData_IB(pierTup, val2cards, jokers):
    # print '_getCardData_IB', val2cards
    type, vals, useJoker = pierTup
    pierList = []
    joker2Crads = []
    v_0 = vals[0]
    v_1 = vals[1]
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
        cardStr = val2card[v_0]+'d'
        joker2Crads = [cardStr]*useJoker
    # if val2cards.has_key(v_0):
    cards = val2cards[v_0]
    cards_1 = val2cards[v_1]
    pierList.extend(cards[:4-useJoker]+cards_1[:1])
    val2cards[v_0] = cards[4-useJoker:]
    val2cards[v_1] = cards_1[1:]
    # return pierList, joker2Crads
    return IronBranch(pierList, IRON_BRANCH, vals, joker2Crads)

def _getCardData_G(pierTup, val2cards, jokers):
    # print '_getCardData_G', val2cards
    type, vals, useJoker = pierTup
    pierList = []
    joker2Crads = []
    v_0 = vals[0]
    v_1 = vals[1]
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
        cardStr = val2card[v_0]+'d'
        joker2Crads = [cardStr]*useJoker
    # if val2cards.has_key(v_0):
    cards = val2cards[v_0]
    cards_1 = val2cards[v_1]
    pierList.extend(cards[:3-useJoker]+cards_1[:2])
    val2cards[v_0] = cards[3-useJoker:]
    val2cards[v_1] = cards_1[2:]
    # return pierList, joker2Crads
    return Gourd(pierList, GOURD, vals, joker2Crads)

def _getCardData_F(pierTup, val2cards, jokers):
    # print '_getCardData_F', val2cards
    type, vals, useJoker, hasVals, color = pierTup
    pierList, joker2Crads = __dealSFcards(vals, useJoker, jokers, color, val2cards)
    return Flush(pierList, FLUSH, vals, joker2Crads)

def _getCardData_S(pierTup, val2cards, jokers):
    # print '_getCardData_S', val2cards
    type, minVal, useJoker, hasVals, color = pierTup
    vals = xrange(minVal+4, minVal-1, -1)
    pierList = []
    joker2Crads = []
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
    for v in vals:
        if v == 1:
            v = VAL_A
        if val2cards.has_key(v) and v in hasVals:
            cards = val2cards[v]
            pierList.extend(cards[:1])
            val2cards[v] = cards[1:]
        else:
            cardStr = val2card[v]+'d'
            joker2Crads.append(cardStr)
    return Straight(pierList, STRAIGHT, [minVal], joker2Crads)

def _getCardData_DG(pierTup, val2cards, jokers):
    # print '_getCardData_DG', val2cards
    type, vals, useJoker = pierTup
    pierList = []
    joker2Crads = []
    val = vals[0]
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
        cardStr = val2card[val]+'d'
        joker2Crads = [cardStr]*useJoker
    # if val2cards.has_key(val):
    cards = val2cards[val]
    pierList.extend(cards[:1])
    val2cards[val] = cards[1:]
    return DoubleGhost(pierList, DOUBLE_GHOST, vals, joker2Crads)

def _getCardData_T(pierTup, val2cards, jokers):
    # print '_getCardData_T', val2cards, pierTup
    type, vals, useJoker = pierTup
    pierList = []
    joker2Crads = []
    val = vals[0]
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
        cardStr = val2card[val]+'d'
        joker2Crads = [cardStr]*useJoker
    cards = val2cards[val]
    # print '111', cards, useJoker
    pierList.extend(cards[:3-useJoker])
    val2cards[val] = cards[3-useJoker:]
    leftVals = vals[1:]
    # print '111', pierList
    if leftVals:
        for v in leftVals:
            _cards = val2cards[v]
            pierList.extend(_cards[:1])
            val2cards[v] = _cards[1:]
    return Triplet(pierList, TRIPLET, vals, joker2Crads)

def _getCardData_TP(pierTup, val2cards, jokers):
    # print '_getCardData_TP', val2cards
    type, vals, useJoker = pierTup
    pierList = []
    joker2Crads = []
    v_0, v_1, v_2 = vals
    cards_0 = val2cards[v_0]
    cards_1 = val2cards[v_1]
    cards_2 = val2cards[v_2]
    pierList = cards_0[:2]+cards_1[:2]+cards_2[:1]
    val2cards[v_0] = cards_0[2:]
    val2cards[v_1] = cards_1[2:]
    val2cards[v_2] = cards_2[1:]
    return TwoPairs(pierList, TWO_PAIRS, vals, joker2Crads)

def _getCardData_P(pierTup, val2cards, jokers):
    # print '_getCardData_P', val2cards
    type, vals, useJoker = pierTup
    pierList = []
    joker2Crads = []
    val = vals[0]
    if useJoker > 0:
        pierList = jokers[0:useJoker]
        jokers = jokers[useJoker:]
        cardStr = val2card[val]+'d'
        joker2Crads = [cardStr]*useJoker
    cards = val2cards[val]
    pierList.extend(cards[:2-useJoker])
    val2cards[val] = cards[2-useJoker:]
    leftVals = vals[1:]
    for v in leftVals:
        _cards = val2cards[v]
        pierList.extend(_cards[:1])
        val2cards[v] = _cards[1:]
    return Pair(pierList, PAIR, vals, joker2Crads)

def _getCardData_O(pierTup, val2cards, jokers):
    # print '_getCardData_O', val2cards
    type, vals, useJoker = pierTup
    pierList = []
    joker2Crads = []
    for v in vals:
        _cards = val2cards[v]
        pierList.extend(_cards[:1])
        val2cards[v] = _cards[1:]
    return Oolong(pierList, OOLONG, vals, joker2Crads)

type2GetCardsFunc = {
    OOLONG            :        _getCardData_O, \
    PAIR              :        _getCardData_P, \
    TWO_PAIRS         :        _getCardData_TP, \
    TRIPLET           :        _getCardData_T, \
    DOUBLE_GHOST      :        _getCardData_DG, \
    STRAIGHT          :        _getCardData_S, \
    FLUSH             :        _getCardData_F, \
    GOURD             :        _getCardData_G, \
    IRON_BRANCH       :        _getCardData_IB, \
    STRAIGHT_FLUSH    :        _getCardData_SF, \
    FIVE_HEADS        :        _getCardData_FH, \
}

def getL1_7(count2vals):
    return (count2vals[1], count2vals[2], count2vals[3], \
        count2vals[4], count2vals[5], count2vals[6], count2vals[7])

def dealSSort(allThreeS, val2cards):
    cards_3 = []
    cards_5 = []
    allS = allThreeS[0]
    for sVals in allS:
        tmpCards = []
        for val in sVals:
            cards = val2cards[val]
            # print 'cards111', cards
            card = cards[0]
            tmpCards.append(card)
            cards.remove(card)
        if len(sVals) == 3:
            cards_3 = tmpCards
        else:
            cards_5.extend(tmpCards)
    rsltCards = cards_3 + cards_5
    # print 'rsltCards', rsltCards
    return rsltCards

def dealSFSort(allSF):
    headCards = []
    otherCards = []
    for sfVals, color in allSF:
        curCards = []
        for val in sfVals:
            card = val2card[val] + color
            curCards.append(card)
        if len(curCards) == 3:
            headCards.extend(curCards)
        else:
            otherCards.extend(curCards)
    # print 'rsltCards', headCards, otherCards
    return headCards + otherCards

def dealOneSort(cards, oneVal):
    oneCards = []
    otherCards = cards[:]
    oneValStr = val2card[oneVal]
    for card in cards:
        if card[0] == oneValStr:
            oneCards.append(card)
            otherCards.remove(card)
            break
    rsltCards = otherCards + oneCards
    # print 'rsltCards', rsltCards
    return rsltCards

def dealCountSort(cards, mostVal):
    mostCards = []
    otherCards = []
    mostValStr = val2card[mostVal]
    for card in cards:
        if card[0] == mostValStr:
            mostCards.append(card)
        else:
            otherCards.append(card)
    rsltCards = mostCards + otherCards
    # print 'rsltCards', rsltCards
    return rsltCards

def dealColorSort(cards):
    color2cards = {'a':[], 'b':[], 'c':[], 'd':[]}
    for c in cards:
        color = c[1]
        color2cards[color].append(c)
    # print 'color2cards', color2cards
    headCards = []
    otherCards = []
    for color, cards in color2cards.items():
        _len = len(cards)
        if _len % 5 == 3:
            headCards.extend(cards)
        elif _len > 0:
            otherCards.extend(cards)
    return headCards + otherCards

#---------------------------------------------------------------

def getSpecialType(cards, isCommonPlay=True):
    valList, jokers, val2cards, color2vals = dealCardDatas(cards)
    count2vals = getCount2Vals(valList)
    colorCounts = [len(_vals) for _vals in color2vals.values()]
    colorSet = set(color2vals.keys())
    colorCounts.sort()
    # jokerCount = len(jokers)
    colorCount = len(color2vals)
    valCounts = []
    for count, vals in count2vals.items():
        _len = len(vals)
        valCounts.extend([count]*_len)
    # valCounts = [ for count in count2vals.keys() if count2vals[count]]
    print 'deal datas', cards, valList, color2vals, colorCounts, valCounts, colorCount, isCommonPlay

    if set(valList) == set(DRAGON_VAL_LIST):
        #至尊青龙, 一条龙
        if colorCount == 1:
            return SpecialType(cards, SUPREME_QINGLONG)
        return SpecialType(cards, DRAGON)

    if isCommonPlay:
        maxCount = max(valCounts)
        minVal = min(valList)
        maxVal = max(valList)
        # 七同, 十二皇族, 三同花顺, 三分天下, 六同
        if maxCount == 7:
            mostVal = count2vals[maxCount][0]
            cards = dealCountSort(cards, mostVal)
            return SpecialType(cards, SEVEN_HEADS)
        if minVal >= 11:
            return SpecialType(cards, TWELVE_ROYALTY)
        if colorCount <= 3:
            allSF = isThreeStraightFlush(colorCounts, color2vals)
            if allSF:
                cards = dealSFSort(allSF)
                return SpecialType(cards, THREE_STRAIGHT_FLUSH)
        if valCounts.count(4)+valCounts.count(5) == 3:
            oneVal = count2vals[1][0]
            cards = dealOneSort(cards, oneVal)
            return SpecialType(cards, THREE_POINTS)
        if maxCount == 6:
            mostVal = count2vals[maxCount][0]
            cards = dealCountSort(cards, mostVal)
            return SpecialType(cards, SIX_HEADS)
        #全大, 全小, 凑一色, 四套三条, 五对三条
        if minVal >= 8:
            return SpecialType(cards, ALL_BIG)
        if maxVal <= 9:
            return SpecialType(cards, ALL_SMALL)
        if colorSet <= set(BLACK_COLOR) or colorSet <= set(RED_COLOR):
            return SpecialType(cards, ONE_COLOR)
        if valCounts.count(3)+valCounts.count(4) == 4:
            oneVal = count2vals[1][0]
            cards = dealOneSort(cards, oneVal)
            return SpecialType(cards, FOUR_TRIPLET)
        if valCounts.count(2) == valCounts.count(3)+4 == 5:
            mostVal = count2vals[maxCount][0]
            cards = dealCountSort(cards, mostVal)
            return SpecialType(cards, FIVE_PAIRS_A_TRIPLET)
    #六对半, 三顺子, 三同花
    if valCounts.count(2) == 6:
        oneVal = count2vals[1][0]
        cards = dealOneSort(cards, oneVal)
        return SpecialType(cards, SIX_PAIRS)
    allThreeS = isThreeStraight(valList)
    if allThreeS:
        cards = dealSSort(allThreeS, val2cards)
        return SpecialType(cards, THREE_STRAIGHT)
    if isThreeFlush(colorCounts):
        cards = dealColorSort(cards)
        return SpecialType(cards, THREE_FLUSH)
    return CardsInvalid(cards, INVALID_TYPE)

def CardsModelFactory(cards):
    """
    cards:牌列表
    """
    print 'CardsModelFactory_s, cards', cards
    _len = len(cards)
    if _len not in [3,5]:
        return CardsInvalid(cards, INVALID_TYPE)

    vals, jokerCount, colorCount = getCardData(cards)
    valSet, valSetList, valCounts, count2vals = getValData(vals)
    lenValSet = len(valSet)

    if _len == 3:
        if jokerCount == 2:
            return DoubleGhost(cards, DOUBLE_GHOST, valSetList)
        if lenValSet == 1:
            return Triplet(cards, TRIPLET, valSetList)
        if lenValSet == 2:
            valList = valSetList[:]
            if vals.count(valList[-1]) == 2:
                valList.reverse()
            return Pair(cards, PAIR, valList)
        if lenValSet == 3:
            return Oolong(cards, OOLONG, valSetList)
    else:
        #[5]
        if lenValSet == 1:
            return FiveHeads(cards, FIVE_HEADS, valSetList)
        valList = isStraight(vals, jokerCount, valSet)
        if valList:
            if colorCount == 1:
                return StraightFlush(cards, STRAIGHT_FLUSH, valList)
            return Straight(cards, STRAIGHT, valList)

        maxCount = max(valCounts)
        valList = count2vals[maxCount]

        #[(4,1),(3,2)]
        if lenValSet == 2:
            if maxCount + jokerCount == 4:
                valList.extend(count2vals[1])
                return IronBranch(cards, IRON_BRANCH, valList)
            if maxCount + jokerCount == 3:
                if jokerCount == 0:
                    valList.extend(count2vals[2])
                return Gourd(cards, GOURD, valList)
        #同花
        curList = isFlush(vals, jokerCount, colorCount)
        if curList:
            return Flush(cards, FLUSH, curList)
        #[(3,1,1),(2,2,1)]
        if lenValSet == 3:
            if maxCount + jokerCount == 3:
                if jokerCount in [0,1]:
                    valList.extend(count2vals[1])
                return Triplet(cards, TRIPLET, valList)
            if maxCount + jokerCount == 2:
                valList.extend(count2vals[1])
                return TwoPairs(cards, TWO_PAIRS, valList)
        #[(2,1,1,1)]
        if lenValSet == 4:
            if jokerCount == 0:
                valList.extend(count2vals[1])
            return Pair(cards, PAIR, valList)
        return Oolong(cards, OOLONG, valList)


def _getBestChoice(allVals, jokers, color2vals):
    # t1 = getTimestamp()
    # allVals, jokers, val2cards, color2vals = dealCardDatas(cards)
    jokerCount = len(jokers)
    count2vals = getCount2Vals(allVals)
    l1, l2, l3, l4, l5, l6, l7 = getL1_7(count2vals)
    if l6 or l7:
        l5 = l5 + l6 + l7
        l1 = l1 + l6
        l2 = l2 + l7
        l1.sort(reverse=True)
        l2.sort(reverse=True)

    allPierList = []
    allFiveList = getAllFiveHeads(l5, l4, l3, jokerCount)
    allFourList = getAllIronBranch(l5+l4, l3, l2, jokerCount)
    l3_5 = l5+l4+l3
    l25 = l5+l2
    allGourdList = getAllGourd(l3_5, l25, l1, jokerCount)
    allThreeList = getAllTriplet(l3_5, l25, l1, jokerCount)
    l23 = l3+l2
    
    allTwoList_SF = []
    allTwoList_S = []
    allList_SF = []
    allList_S = []
    allList_F = []
    double_SF = []
    double_S = []
    allDict_F = {}
    for color, vals in color2vals.items():
        twoList_SF, list_SF = getTwoJoint(vals, jokerCount, color)
        if twoList_SF:
            allTwoList_SF.extend(twoList_SF)
        elif list_SF:
            allList_SF.extend(list_SF)
            double_SF.append(list_SF)
        rsltLs = hasFlushTup(vals, jokerCount, color)
        if rsltLs:
            allDict_F[color] = rsltLs
            allList_F.append(rsltLs)

    allTwoList_S, allList_S = getTwoJoint(allVals, jokerCount, '')

    # t2 = getTimestamp()
    # print 'time0', t2-t1
    
    maxScore = 0
    # 五同
    if allFiveList:
        tailScore = 9
        isTrue = True
        for v_1, useJoker_1 in allFiveList:
            leftVals_1 = _rmVals(allVals, [v_1]*(5-useJoker_1))
            tailPier = (FIVE_HEADS, v_1, useJoker_1)
            leftJoker_1 = jokerCount-useJoker_1
            paramTup = leftJoker_1, leftVals_1, tailPier, 9, 0

            # 五同
            maxScore, curPierList = dealFiveHeads_m(allFiveList, maxScore, paramTup)
            if curPierList:
                allPierList.extend(curPierList)
            # 同花顺
            if allList_SF:
                maxScore, curPierList = dealSF(allList_SF, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 铁支
            if allFourList:
                maxScore, curPierList = dealIronBranch_m(allFourList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 葫芦
            if allGourdList:
                maxScore, curPierList = dealGourd_m(allGourdList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 同花
            if allList_F:
                maxScore, curPierList = dealFlush(allList_F, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 顺子
            if allList_S:
                maxScore, curPierList = dealStraight_m(allList_S, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 三条
            if allThreeList:
                maxScore, curPierList = dealTriplet_m(allThreeList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)

            if allPierList and isTrue:
                continue
            isTrue = False

            _count2vals = getCount2Vals(leftVals_1)
            l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1 = getL1_7(_count2vals)

            # 两对
            if len(l2_1) >= 2 and leftJoker_1 == 0:
                maxScore, curPierList = dealTwoPairs_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue

            lenL1 = len(l1_1)
            # 对子
            if len(l2_1) == 1 or (lenL1 == 7 and leftJoker_1 == 1):
                maxScore, curPierList = dealPair_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue
            # 乌龙
            if lenL1 == 8:
                maxScore, curPierList = dealOolong_m(l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)

    # t3 = getTimestamp()
    # print 'time1', t3-t2
    if jokerCount < 2 and maxScore >= 16:
        return allPierList

    # 双同花顺
    if allTwoList_SF:
        for tup_SF_1, tup_SF_2 in allTwoList_SF:
            maxScore, curPierList = dealDoubleSF(tup_SF_1, tup_SF_2, allVals, jokerCount, maxScore, STRAIGHT_FLUSH, 4, 9)
            if curPierList:
                allPierList.extend(curPierList)
    if len(double_SF) == 2:
        allTup_SF_1, allTup_SF_2 = double_SF
        for tup_SF_1 in allTup_SF_1:
            for tup_SF_2 in allTup_SF_2:
                maxScore, curPierList = dealDoubleSF(tup_SF_1,tup_SF_2,allVals,jokerCount,maxScore,STRAIGHT_FLUSH,4,9)
                if curPierList:
                    allPierList.extend(curPierList)

    # t4 = getTimestamp()
    # print 'time2', t4-t3
    # 同花顺
    if allList_SF:
        tailScore = 4
        isTrue = True
        for minVal_1, useJoker_1, hasValSet_1, color_1 in allList_SF:
            leftVals_1 = _rmVals(allVals, hasValSet_1)
            tailPier = (STRAIGHT_FLUSH, minVal_1, useJoker_1, hasValSet_1, color_1)
            leftJoker_1 = jokerCount-useJoker_1
            paramTup = leftJoker_1, leftVals_1, tailPier, 4, 0
            # 铁支
            if allFourList:
                maxScore, curPierList = dealIronBranch_m(allFourList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 葫芦
            if allGourdList:
                maxScore, curPierList = dealGourd_m(allGourdList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 同花
            if allList_F:
                tmpDict_F = copy.deepcopy(allDict_F)
                vLs = tmpDict_F[color_1][0]
                # print 'xxxxxx', tmpDict_F, vLs, hasValSet_1
                for v in hasValSet_1:
                    vLs.remove(v)

                tmpList_F = tmpDict_F.values()
                # print 'xxxxxx22', tmpList_F

                maxScore, curPierList = dealFlush(tmpList_F, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 顺子
            if allList_S:
                maxScore, curPierList = dealStraight_m(allList_S, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 三条
            if allThreeList:
                maxScore, curPierList = dealTriplet_m(allThreeList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)

            if allPierList and isTrue:
                continue
            isTrue = False

            _count2vals = getCount2Vals(leftVals_1)
            l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1 = getL1_7(_count2vals)

            # 两对
            if len(l2_1) >= 2 and leftJoker_1 == 0:
                maxScore, curPierList = dealTwoPairs_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue

            lenL1 = len(l1_1)
            # 对子
            if len(l2_1) == 1 or (lenL1 == 7 and leftJoker_1 == 1):
                maxScore, curPierList = dealPair_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue
            # 乌龙
            if lenL1 == 8:
                maxScore, curPierList = dealOolong_m(l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)

    # t5 = getTimestamp()
    # print 'time3', t5-t4
    if jokerCount < 2 and maxScore >= 12:
        return allPierList

    # 铁支
    if allFourList:
        tailScore = 3
        isTrue = True
        for v_1, useJoker_1 in allFourList:
            fourList = [v_1]*(4-useJoker_1)
            leftVals_1 = _rmVals(allVals, fourList)
            tailPier = [IRON_BRANCH, [v_1], useJoker_1]
            leftJoker_1 = jokerCount-useJoker_1
            paramTup = leftJoker_1, leftVals_1, tailPier, 3, 1

            # 铁支
            maxScore, curPierList = dealIronBranch_m(allFourList, maxScore, paramTup)
            if curPierList:
                allPierList.extend(curPierList)
            # 葫芦
            if allGourdList:
                maxScore, curPierList = dealGourd_m(allGourdList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 同花
            if allList_F:
                maxScore, curPierList = dealFlush(allList_F, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 顺子
            if allList_S:
                maxScore, curPierList = dealStraight_m(allList_S, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 三条
            if allThreeList:
                maxScore, curPierList = dealTriplet_m(allThreeList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)

            if allPierList and isTrue:
                continue
            isTrue = False

            leftVal = min(l1)
            leftVals_1.remove(leftVal)
            tailPier[1].append(leftVal)

            _count2vals = getCount2Vals(leftVals_1)
            l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1 = getL1_7(_count2vals)

            # 两对
            if len(l2_1) >= 2 and leftJoker_1 == 0:
                maxScore, curPierList = dealTwoPairs_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue

            lenL1 = len(l1_1)
            # 对子
            if len(l2_1) == 1 or (lenL1 == 7 and leftJoker_1 == 1):
                maxScore, curPierList = dealPair_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue
            # 乌龙
            if lenL1 == 8:
                maxScore, curPierList = dealOolong_m(l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)

    # t6 = getTimestamp()
    # print 'time4', t6-t5
    if jokerCount < 2 and maxScore >= 3:
        return allPierList

    tailScore = 0
    # 葫芦
    if allGourdList:
        isTrue = True
        for v_0, v_1, useJoker_1 in allGourdList:
            gourdList = [v_0]*(3-useJoker_1) + [v_1]*2
            leftVals_1 = _rmVals(allVals, gourdList)
            tailPier = (GOURD, [v_0, v_1], useJoker_1)
            leftJoker_1 = jokerCount-useJoker_1
            paramTup = leftJoker_1, leftVals_1, tailPier, 0, 0

            # 葫芦
            maxScore, curPierList = dealGourd_m(allGourdList, maxScore, paramTup)
            if curPierList:
                allPierList.extend(curPierList)
            
            # 同花
            if allList_F:
                maxScore, curPierList = dealFlush(allList_F, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 顺子
            if allList_S:
                maxScore, curPierList = dealStraight_m(allList_S, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            # 三条
            if allThreeList:
                maxScore, curPierList = dealTriplet_m(allThreeList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)

            if allPierList and isTrue:
                continue
            isTrue = False

            _count2vals = getCount2Vals(leftVals_1)
            l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1 = getL1_7(_count2vals)

            # 两对
            if len(l2_1) >= 2 and leftJoker_1 == 0:
                maxScore, curPierList = dealTwoPairs_m(l2_1,l1_1,leftJoker_1,leftVals_1,tailPier,tailScore,maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue

            lenL1 = len(l1_1)
            # 对子
            if len(l2_1) == 1 or (lenL1 == 7 and leftJoker_1 == 1):
                maxScore, curPierList = dealPair_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue
            # 乌龙
            if lenL1 == 8:
                maxScore, curPierList = dealOolong_m(l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)

    # t7 = getTimestamp()
    # print 'time5', t7-t6
    if jokerCount < 2 and maxScore >= 2:
        return allPierList

    allPairList = getAllPairs(l23, l1, jokerCount)

    # 同花
    if allList_F:
        curPierList = []
        # 双同花
        if allThreeList:
            maxScore, curPierList = _dealDoubleFlushData(allThreeList,3,allList_F,jokerCount,allVals,maxScore)
        if not curPierList and allPairList:
            maxScore, curPierList = _dealDoubleFlushData(allPairList,2,allList_F,jokerCount,allVals,maxScore)
        if not curPierList:
            maxScore, curPierList = _dealDoubleFlushData([(0,0)],0,allList_F,jokerCount,allVals,maxScore)
        if curPierList:
            allPierList.extend(curPierList)
        # 顺子
        if allList_S:
            for minVal_1, useJoker_1, hasValSet_1, _ in allList_S:
                leftJoker_1 = jokerCount-useJoker_1
                leftVals_1 = _rmVals(allVals, hasValSet_1)
                middlePier = (STRAIGHT, minVal_1, useJoker_1, hasValSet_1, '')
                paramTup = leftJoker_1, leftVals_1, middlePier, 0, 0
                maxScore, curPierList = dealFlush(allList_F, maxScore, paramTup, True)
                if curPierList:
                    allPierList.extend(curPierList)
        # 三条
        if allThreeList:
            for v_1, useJoker_1 in allThreeList:
                leftJoker_1 = jokerCount-useJoker_1
                leftVals_1 = _rmVals(allVals, [v_1]*(3-useJoker_1))
                middlePier = [TRIPLET, [v_1], useJoker_1]
                paramTup = leftJoker_1, leftVals_1, middlePier, 0, 2
                maxScore, curPierList = dealFlush(allList_F, maxScore, paramTup, True)
                if curPierList:
                    allPierList.extend(curPierList)

        # if allPierList and isTrue:
                # continue
            # isTrue = False

        # 两对
        if len(allPairList) >= 2:
            for v_0, useJoker_0 in allPairList:
                if useJoker_0 > 0:
                    continue
                tmpPairList = allPairList[:]
                tmpPairList.remove((v_0, useJoker_0))
                for v_1, useJoker_1 in tmpPairList:
                    if v_0 < v_1 or useJoker_1 > 0:
                        continue
                    leftJoker_1 = jokerCount-useJoker_0-useJoker_1
                    leftVals_1 = _rmVals(allVals, [v_0, v_1]*2)
                    middlePier = [TWO_PAIRS, [v_0, v_1], 0]
                    paramTup = leftJoker_1, leftVals_1, middlePier, 0, 1
                    maxScore, curPierList = dealFlush(allList_F, maxScore, paramTup, True)
                    if curPierList:
                        allPierList.extend(curPierList)
        # break
        # 对子
        # print 'allPairList', allPairList
        if allPairList:
            for v_1, useJoker_1 in allPairList:
                # print 'allPairList', v_1, useJoker_1
                leftJoker_1 = jokerCount-useJoker_1
                leftVals_1 = _rmVals(allVals, [v_1]*(2-useJoker_1))
                middlePier = [PAIR, [v_1], useJoker_1]
                paramTup = leftJoker_1, leftVals_1, middlePier, 0, 3
                maxScore, curPierList = dealFlush(allList_F, maxScore, paramTup, True)
                if curPierList:
                    allPierList.extend(curPierList)
        # 乌龙
        if len(l1) >= 8:
            curPierList = []
            flushTup = checkFlush(allVals, allList_F, jokerCount)
            if flushTup:
                tailPier = flushTup
                leftVals_1 = _rmVals(allVals, flushTup[3])
                middlePier = (OOLONG, leftVals_1[:5], 0)
                headPier = (OOLONG, leftVals_1[5:], 0)
                totalScore = 0+0+0
                # paramTup = (totalScore,tailPier,middlePier,headPier,maxScore,curPierList)
                maxScore, curPierList = updatePierList(totalScore,tailPier,middlePier,headPier,maxScore,curPierList)
            if curPierList:
                allPierList.extend(curPierList)

    # t8 = getTimestamp()
    # print 'time6', t8-t7
    if jokerCount < 2 and maxScore >= 2:
        return allPierList

    # 双顺子
    if allTwoList_S:
        for tup_S_1, tup_S_2 in allTwoList_S:
            maxScore, curPierList = dealDoubleSF(tup_S_1, tup_S_2, allVals, jokerCount, maxScore, STRAIGHT, 0, 0)
            if curPierList:
                allPierList.extend(curPierList)

    # 顺子
    if allList_S:
        isTrue = True
        # print '111111111', allList_S
        for minVal_1, useJoker_1, hasValSet_1, _ in allList_S:
            leftJoker_1 = jokerCount-useJoker_1
            leftVals_1 = _rmVals(allVals, hasValSet_1)
            tailPier = [STRAIGHT, minVal_1, useJoker_1, hasValSet_1, '']
            paramTup = leftJoker_1, leftVals_1, tailPier, 0, 0
            # 三条
            if allThreeList:
                maxScore, curPierList = dealTriplet_m(allThreeList, maxScore, paramTup)
                if curPierList:
                    allPierList.extend(curPierList)
            
            if allPierList and isTrue:
                continue
            isTrue = False

            _count2vals = getCount2Vals(leftVals_1)
            l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1 = getL1_7(_count2vals)
            # print '222222222', hasValSet_1, leftJoker_1, l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1

            # 两对
            if len(l2_1) >= 2 and leftJoker_1 == 0:
                maxScore, curPierList = dealTwoPairs_m(l2_1,l1_1,leftJoker_1,leftVals_1,tailPier,tailScore,maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue

            lenL1 = len(l1_1)
            # 对子
            if len(l2_1) == 1 or (lenL1 == 7 and leftJoker_1 == 1):
                maxScore, curPierList = dealPair_m(l2_1, l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)
                continue
            # 乌龙
            if lenL1 == 8:
                maxScore, curPierList = dealOolong_m(l1_1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore)
                if curPierList:
                    allPierList.extend(curPierList)

    # t9 = getTimestamp()
    # print 'time7', t9-t8
    if jokerCount < 2 and maxScore >= 2:
        return allPierList

    # 三条*2 + 双鬼冲头
    curPierList = []
    if len(l3) == 2 and jokerCount == 2 and not l2:
        minVal = l1[-1]
        if minVal <= l3[-1]:
            tailPier, middlePier = __dealTripletData(l3, l1)
            headPier = (DOUBLE_GHOST, [minVal], 2)
            totalScore = 0+0+20
            maxScore, curPierList = updatePierList(totalScore,tailPier,middlePier,headPier,maxScore,curPierList)
    if not curPierList:
        # 三条*2 + 冲三
        if len(l3) == 3 and jokerCount == 0 and not l2:
            tailPier, middlePier = __dealTripletData(l3, l1)
            headPier = (TRIPLET, l3[2:3], 0)
            totalScore = 0+0+2
            maxScore, curPierList = updatePierList(totalScore,tailPier,middlePier,headPier,maxScore,curPierList)
    if not curPierList:
        # 三条 + 乌龙 +乌龙
        if len(l3) == 1 and jokerCount == 0 and not l2:
            tailList = l3[:]
            tailList.extend(l1[-2:])
            tailPier = [TRIPLET, tailList, 0]
            middlePier = (OOLONG, l1[0:5], 0)
            headPier = (OOLONG, l1[5:8], 0)
            maxScore, curPierList = updatePierList(0,tailPier,middlePier,headPier,maxScore,curPierList)
    if curPierList:
        allPierList.extend(curPierList)

    # t10 = getTimestamp()
    # print 'time8', t10-t9
    # 两对
    lenL2 = len(l2)
    if not(l5 or l4 or l3) and lenL2 >= 2 and jokerCount==0:
        curPierList = []
        tailPier = (TWO_PAIRS, l2[0:2]+l1[-1:], 0)
        if lenL2 == 6:
            middlePier = (TWO_PAIRS, l2[2:4]+l2[-1:], 0)
            headPier = (PAIR, l2[4:5]+l2[-1:], 0)
        elif lenL2 == 5:
            # 两对 + 两对 + 对子 = 0
            middlePier = (TWO_PAIRS, l2[2:4]+l1[-2:-1], 0)
            headPier = (PAIR, l2[4:5]+l1[-3:-2], 0)
        elif lenL2 == 4:
            # 两对 + 两对 + 乌龙 = 0
            middlePier = (TWO_PAIRS, l2[2:4]+l1[-2:-1], 0)
            headPier = (OOLONG, l1[0:3], 0)
        elif lenL2 == 3:
            # 两对 + 对子 + 乌龙 = 0
            middlePier = (PAIR, l2[2:3]+l1[-4:-1], 0)
            headPier = (OOLONG, l1[0:3], 0)
        elif lenL2 == 2:
            # 两对 + 乌龙 + 乌龙 = 0
            middlePier = (OOLONG, l1[0:5], 0)
            headPier = (OOLONG, l1[5:8], 0)
        else:
            middlePier = ()
            headPier = ()

        if headPier:
            maxScore, curPierList = updatePierList(0,tailPier,middlePier,headPier,maxScore,curPierList)
        if curPierList:
            allPierList.extend(curPierList)

    return allPierList

def getDefaultType(cards):
    print 'getDefaultType_s', cards
    allVals, jokers, val2cards, color2vals = dealCardDatas(cards)
    allPierList = _getBestChoice(allVals, jokers, color2vals)
    print 'getDefaultType_e', allPierList
    return dealDefaultData(allPierList, val2cards, jokers)

def dealDefaultData(allPierList, val2cards, jokers):
    allPierList = allPierSort(allPierList)
    defaultTup = allPierList[0]
    perPierIns = [None]*3
    colorPier = []
    nomalPier = []
    for i in xrange(1, 4):
        pierTup = defaultTup[i]
        if pierTup[0] in [STRAIGHT_FLUSH, FLUSH]:
            colorPier.append((i-1, pierTup))
        else:
            nomalPier.append((i-1, pierTup))
    for num, pierTup in colorPier+nomalPier:
        pierIns = type2GetCardsFunc[pierTup[0]](pierTup, val2cards, jokers)
        perPierIns[num] = pierIns
    return perPierIns

#----------------------------------------------------------------------------

def __dealTripletData(l3, l1):
    tailList = l3[0:1] + l1[0:2]
    middleList = l3[1:2] + l1[2:4]
    tailPier = (TRIPLET, tailList, 0)
    middlePier = (TRIPLET, middleList, 0)
    return tailPier, middlePier

def _dealDoubleFlushData(allList, vCount, allList_F, jokerCount, allVals, maxScore):
    curPierList = []
    for v_1, useJoker_1 in allList:
        leftJoker_1 = jokerCount-useJoker_1
        headList = [v_1]*(vCount-useJoker_1)
        leftVals_1 = _rmVals(allVals, headList)
        
        flushTups = checkDoubleFlush(leftVals_1, allList_F, leftJoker_1)
        if not flushTups:
            continue
        tailPier = flushTups[0]
        middlePier = flushTups[1]
        if len(headList) < 3:
            rmVals = tailPier[3] + middlePier[3]
            leftVals_2 = _rmVals(leftVals_1, rmVals)
            headList.extend(leftVals_2)
        headPier, headScore = checkHeadPier(headList, useJoker_1)
        totalScore = 0+0+headScore
        maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)
    # print '_dealDoubleFlushData', maxScore, curPierList
    return maxScore, curPierList

def updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList):
    if totalScore >= maxScore and tailPier and middlePier and headPier \
        and tailPier[0] >= middlePier[0] >= headPier[0]:
        curTailPier = copy.deepcopy(tailPier)
        curMiddlePier = copy.deepcopy(middlePier)
        curHeadPier = copy.deepcopy(headPier)
        if totalScore == maxScore:
            curPierList.append((totalScore, curTailPier, curMiddlePier, curHeadPier))
        if totalScore > maxScore:
            maxScore = totalScore
            curPierList = [(totalScore, curTailPier, curMiddlePier, curHeadPier)]
        # print 'updatePierList', maxScore, curPierList
    return maxScore, curPierList

def dealFiveHeads_m(allFiveList, maxScore, paramTup):
    leftJoker_1, leftVals_1, tailPier, tailScore, tailLack = paramTup
    tailType, v_1, useJoker_1 = tailPier
    curPierList = []
    tmpFiveList = allFiveList[:]
    tmpFiveList.remove((v_1, useJoker_1))
    for v_2, useJoker_2 in tmpFiveList:
        if v_2 > v_1:
            continue
        leftJoker_2 = leftJoker_1-useJoker_2
        curVals = [v_2]*(5-useJoker_2)
        if leftJoker_2 >= 0 and checkVals(curVals, leftVals_1):
            leftVals_2 = _rmVals(leftVals_1, curVals)
            middlePier = (FIVE_HEADS, v_2, useJoker_2)
            headPier, headScore = checkHeadPier(leftVals_2, leftJoker_2)
            totalScore = tailScore+19+headScore
            maxScore, curPierList = updatePierList(totalScore,tailPier,middlePier,headPier,maxScore,curPierList)
    # print 'dealFiveHeads_m', maxScore, curPierList
    return maxScore, curPierList

def dealDoubleSF(tup_SF_1, tup_SF_2, allVals, jokerCount, maxScore, type, tailScore, middleScore):
    curPierList = []
    minVal_1, useJoker_1, hasValSet_1, color_1 = tup_SF_1
    minVal_2, useJoker_2, hasValSet_2, color_2 = tup_SF_2
    leftJoker_2 = jokerCount-useJoker_1-useJoker_2
    if leftJoker_2 >= 0:
        rmList = list(hasValSet_1) + list(hasValSet_2)
        leftVals_1 = _rmVals(allVals, rmList)
        tailPier = (type, minVal_1, useJoker_1, hasValSet_1, color_1)
        middlePier = (type, minVal_2, useJoker_2, hasValSet_2, color_2)

        minVal_1 = dealAS(minVal_1)
        minVal_2 = dealAS(minVal_2)

        if minVal_1 < minVal_2:
            tailPier, middlePier = exChange(tailPier, middlePier)
        headPier, headScore = checkHeadPier(leftVals_1, leftJoker_2)
        totalScore = tailScore+middleScore+headScore
        maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)
    # print 'dealDoubleSF', maxScore, curPierList
    return maxScore, curPierList

def dealSF(allList_SF, maxScore, paramTup):
    leftJoker_1, leftVals_1, tailPier, tailScore, tailLack = paramTup
    curPierList = []
    for minVal, useJoker_2, hasValSet, color in allList_SF:
        leftJoker_2 = leftJoker_1-useJoker_2
        if leftJoker_2 >= 0 and checkVals(list(hasValSet), leftVals_1):
            leftVals_2 = _rmVals(leftVals_1, hasValSet)
            middlePier = (STRAIGHT_FLUSH, minVal, useJoker_2, hasValSet, color)
            headPier, headScore = checkHeadPier(leftVals_1, leftJoker_2)
            totalScore = tailScore+9+headScore
            maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)
    # print 'dealSF', maxScore, curPierList
    return maxScore, curPierList

def getIronBranchLeft1Card(leftVals_2):
    count2vals = getCount2Vals(leftVals_2)
    l1_1, l2_1, l3_1, l4_1, _, _, _ = getL1_7(count2vals)
    if l1_1:
        leftVal = min(l1_1)
    elif l2_1:
        leftVal = min(l2_1)
    elif l4_1:
        leftVal = min(l4_1)
    else:
        leftVal = 0
    return leftVal

def dealIronBranch_m(allFourList, maxScore, paramTup):
    leftJoker_1, leftVals_1, tailPier, tailScore, tailLack = paramTup
    tmpFourList = allFourList[:]
    v_1 = 100
    if tailPier[0] == IRON_BRANCH:
        tailType, vList, useJoker_1 = tailPier
        v_1 = vList[0]
        tmpFourList.remove((v_1, useJoker_1))
    
    curPierList = []
    for v_2, useJoker_2 in tmpFourList:
        if v_2 > v_1:
            continue
        leftJoker_2 = leftJoker_1-useJoker_2
        curVals = [v_2]*(4-useJoker_2)
        if leftJoker_2 >= 0 and checkVals(curVals, leftVals_1):
            leftVals_2 = _rmVals(leftVals_1, curVals)
            headPier, headScore, headVals = getMaxHeadPier(leftVals_2, leftJoker_2)
            leftVals_3 = _rmVals(leftVals_2, headVals)
            # leftVals_3 两张牌
            middleVals = leftVals_3[-1:]
            if tailLack > 0:
                tailVals = leftVals_3[:tailLack]
                tailPier[1] = [v_1] + tailVals
            
            middlePier = (IRON_BRANCH, [v_2]+middleVals, useJoker_2)
            totalScore = tailScore+7+headScore
            maxScore, curPierList = updatePierList(totalScore,tailPier,middlePier,headPier,maxScore,curPierList)

    # print 'dealIronBranch_m', maxScore, curPierList
    return maxScore, curPierList

def dealGourd_m(allGourdList, maxScore, paramTup):
    leftJoker_1, leftVals_1, tailPier, tailScore, tailLack = paramTup
    tmpGourdList = allGourdList[:]
    v_0, v_1 = 100, 100
    if tailPier[0] == GOURD:
        tailType, vList, useJoker_1 = tailPier
        v_0, v_1 = vList
        tmpGourdList.remove((v_0, v_1, useJoker_1))

    tailVals = tailPier[1][:] if tailLack > 0 else []

    curPierList = []
    for v_2, v_3, useJoker_2 in tmpGourdList:
        if v_2 > v_0 or (v_2 == v_0 and v_3 > v_1):
            continue
        leftJoker_2 = leftJoker_1-useJoker_2
        curVals = [v_2]*(3-useJoker_2) + [v_3]*2
        if leftJoker_2 >= 0 and checkVals(curVals, leftVals_1):
            leftVals_2 = _rmVals(leftVals_1, curVals)
            headPier, headScore, headVals = getMaxHeadPier(leftVals_2, leftJoker_2)
            # leftVals_3, 1张牌
            if tailLack > 0:
                leftVals_3 = _rmVals(leftVals_2, headVals)
                _tailVals = leftVals_3[:tailLack]
                curTailVals = tailVals[:]+_tailVals
                tailPier[1] = curTailVals

            middlePier = (GOURD, [v_2, v_3], useJoker_2)
            totalScore = tailScore+1+headScore
            maxScore, curPierList = updatePierList(totalScore,tailPier,middlePier,headPier,maxScore,curPierList)
        
    # print 'dealIronBranch_m', maxScore, curPierList
    return maxScore, curPierList

def __dealLeftCards(vals, rmVals, needCount, headList, tailPier):
    leftVals = _rmVals(vals, rmVals)
    if needCount > 0:
        headList.extend(leftVals[:needCount])
        leftVals = leftVals[needCount:]
    if leftVals:
        tailPier[1].extend(leftVals)
    return headList, tailPier

def _dealFlushData(allList, vCount, paramTup):
    curPierList = []
    allList_F, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore, tailLack, isTail = paramTup
    # print '_dealFlushData', tailLack,tailPier
    tailVals = tailPier[1][:] if tailLack > 0 else []
    # print 'asasasasas', allList, vCount, paramTup
    for v_2, useJoker_2 in allList:
        leftJoker_2 = leftJoker_1-useJoker_2
        headList = [v_2]*(vCount-useJoker_2)
        leftVals_2 = _rmVals(leftVals_1, headList)
        flushTup = checkFlush(leftVals_2, allList_F, leftJoker_2)
        if not flushTup:
            continue
        middlePier = flushTup
        lenHead = len(headList)
        if lenHead < 3 or tailLack > 0:
            # print '111111222', leftVals_2, flushTup
            leftVals_3 = _rmVals(leftVals_2, flushTup[3])
            # print leftVals_3
            if lenHead < 3:
                needCount = 3-lenHead-useJoker_2
                headList.extend(leftVals_3[:needCount])
            if tailLack > 0:
                curTailVals = tailVals[:]+leftVals_3[-tailLack:]
                tailPier[1] = curTailVals

        curUseJoker = leftJoker_1 - flushTup[2]
        headPier, headScore = checkHeadPier(headList, curUseJoker)
        if not headPier:
            continue
        # print 'sssss',headPier,headList,curUseJoker, tailPier
        if isTail:
            middleType, middleVals = tailPier[:2]
        else:
            middleType, middleVals = middlePier[:2]
        headType, headVals = headPier[:2]
        isTrue = (middleType > headType or (middleType == headType and middleVals >= headVals) \
            or (middleType < headType == DOUBLE_GHOST and middleVals >= headVals))
        # print 'isTrue', isTrue
        if isTrue:
            totalScore = tailScore+0+headScore
            if isTail:
                maxScore, curPierList = updatePierList(totalScore, middlePier, tailPier, headPier, maxScore, curPierList)
            else:
                maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)
    # print '_dealFlushData', maxScore, curPierList
    return maxScore, curPierList

def dealFlush(allList_F, maxScore, paramTup, isTail=False):
    leftJoker_1, leftVals_1, tailPier, tailScore, tailLack = paramTup
    curType = tailPier[0]
    # print 'dealFlush', tailLack, tailPier, leftVals_1
    curPierList = []
    count2vals = getCount2Vals(leftVals_1)
    l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1 = getL1_7(count2vals)
    if l7_1 or l6_1 or l5_1 or l4_1 or (l3_1 and l2_1):
        return maxScore, curPierList

    paramTup = (allList_F, leftJoker_1, leftVals_1, tailPier, tailScore, 0, tailLack, isTail)
    # print '1111111111111', curType, isTail, TRIPLET, leftJoker_1
    if curType >= TRIPLET:
        allThreeList_1 = getAllTriplet(l3_1, l2_1, l1_1, leftJoker_1)
        # print '2222222222', allThreeList_1
        _maxScore, curPierList = _dealFlushData(allThreeList_1, 3, paramTup)
        # print '3333333333', _maxScore, curPierList

    if not curPierList:
        allPairList_1 = getAllPairs(l3_1+l2_1, l1_1, leftJoker_1)
        _maxScore, curPierList = _dealFlushData(allPairList_1, 2, paramTup)

    if not curPierList:
        _maxScore, curPierList = _dealFlushData([(0, 0)], 0, paramTup)

    # print 'dealFlush', maxScore, curPierList
    if _maxScore >= maxScore:
        maxScore = _maxScore
        return maxScore, curPierList
    return maxScore, []

def dealStraight_m(allList_S, maxScore, paramTup):
    leftJoker_1, leftVals_1, tailPier, tailScore, tailLack = paramTup
    tailVals = tailPier[1][:] if tailLack > 0 else []
    curPierList = []
    for minVal, useJoker_2, hasValSet, _ in allList_S:
        leftJoker_2 = leftJoker_1-useJoker_2
        if leftJoker_2 >= 0 and checkVals(list(hasValSet), leftVals_1):
            leftVals_2 = _rmVals(leftVals_1, hasValSet)
            headPier, headScore, headVals = getMaxHeadPier(leftVals_2, leftJoker_2)
            if tailLack > 0:
                leftVals_3 = _rmVals(leftVals_2, headVals)
                curTailVals = tailVals[:]+leftVals_3[-tailLack:]
                tailPier[1] = curTailVals
            # if isGt8:
                # leftVal = getIronBranchLeft1Card(leftVals_2)
                # if leftVal == 0:
                    # continue
                # leftVals_2.remove(leftVal)
                # curTailVals = tailVals[:]
                # curTailVals.append(leftVal)
                # tailPier[1] = curTailVals
            
            middlePier = (STRAIGHT, minVal, useJoker_2, hasValSet, '')
            # headPier, headScore = checkHeadPier(leftVals_2, leftJoker_2)
            totalScore = tailScore+0+headScore
            maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)
    # print 'dealStraight_m', maxScore, curPierList
    return maxScore, curPierList

def dealTriplet_m(allThreeList, maxScore, paramTup):
    leftJoker_1, leftVals_1, tailPier, tailScore, tailLack = paramTup
    tailVals = tailPier[1][:] if tailLack > 0 else []
    curPierList = []
    for v_2, useJoker_2 in allThreeList:
        leftJoker_2 = leftJoker_1-useJoker_2
        curVals = [v_2]*(3-useJoker_2)
        if leftJoker_2 >= 0 and checkVals(curVals, leftVals_1):
            leftVals_2 = _rmVals(leftVals_1, curVals)
            headPier, headScore, headVals = getMaxHeadPier(leftVals_2, leftJoker_2)
            if headPier[0] >= TRIPLET and headPier[1] > [v_2]:
                continue
            leftVals_3 = _rmVals(leftVals_2, headVals)
            if tailLack > 0:
                curTailVals = tailVals[:]+leftVals_3[-tailLack:]
                tailPier[1] = curTailVals
            middlePier = (TRIPLET, [v_2]+leftVals_3[:2], useJoker_2)
            totalScore = tailScore+0+headScore
            maxScore, curPierList = updatePierList(totalScore,tailPier,middlePier,headPier,maxScore,curPierList)
    # print 'dealTriplet_m', maxScore, curPierList
    return maxScore, curPierList

def dealTwoPairs_m(l2, l1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore):
    curPierList = []
    if len(l2) >= 2 and leftJoker_1==0:
        valList = l2[:2]
        curVals = valList*2
        if l1:
            rmVals = l1[-1:]
        else:
            rmVals = l2[-1:]
        valList.extend(rmVals)
        curVals.extend(rmVals)
        leftVals_2 = _rmVals(leftVals_1, curVals)
        middlePier = (TWO_PAIRS, valList, 0)
        headPier, headScore = checkHeadPier(leftVals_2, leftJoker_1)
        totalScore = tailScore+0+headScore
        maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)

    # print 'dealTwoPairs_m', maxScore, curPierList
    return maxScore, curPierList

def dealPair_m(l2, l1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore):
    curPierList = []
    if l2:
        valList = l2[:1]
        curVals = valList*2
        useJoker_2 = 0
    else:
        valList = l1[:1]
        curVals = valList[:]
        useJoker_2 = 1

    rmVals = l1[-3:]
    valList.extend(rmVals)
    curVals.extend(rmVals)
    leftVals_2 = _rmVals(leftVals_1, curVals)
    middlePier = (PAIR, valList, useJoker_2)
    headPier, headScore = checkHeadPier(leftVals_2, leftJoker_1)
    totalScore = tailScore+0+headScore
    maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)

    # print 'dealPair_m', maxScore, curPierList
    return maxScore, curPierList

def dealOolong_m(l1, leftJoker_1, leftVals_1, tailPier, tailScore, maxScore):
    if len(l1) == 8:
        curPierList = []
        curVals = l1[:5]
        leftVals_2 = _rmVals(leftVals_1, curVals)
        middlePier = (OOLONG, curVals, 0)
        headPier, headScore = checkHeadPier(leftVals_2, leftJoker_1)
        totalScore = tailScore+0+headScore
        maxScore, curPierList = updatePierList(totalScore, tailPier, middlePier, headPier, maxScore, curPierList)

    # print 'dealOolong_m', maxScore, curPierList
    return maxScore, curPierList

def getMaxHeadPier(vals, jokerCount):
    _len = len(vals) + jokerCount
    if _len < 3:
        return (), 0, []

    if _len == 3:
        tuple, score = checkHeadPier(vals, jokerCount)
        return tuple, score, []

    if jokerCount == 2:
        minVal = min(vals)
        return (DOUBLE_GHOST, [minVal], jokerCount), 20, [minVal]
    count2vals = getCount2Vals(vals)
    l1_1, l2_1, l3_1, l4_1, l5_1, l6_1, l7_1 = getL1_7(count2vals)
    l3_1 = l3_1 + l4_1 + l5_1 + l6_1 + l7_1
    # 冲三
    maxVal, useJoker = _getHeadPierData(l3_1, l2_1, jokerCount)
    if maxVal > 0:
        return (TRIPLET, [maxVal], useJoker), 2, [maxVal]*(3-useJoker)
    # 对子
    maxVal, useJoker = _getHeadPierData(l2_1, l1_1, jokerCount)
    if maxVal > 0:
        l12 = l1_1 + l2_1
        l12.remove(maxVal)
        secondVal = max(l12)
        return (PAIR, [maxVal, secondVal], useJoker), 0, [maxVal]*(2-useJoker)+[secondVal]
    # 乌龙
    curVals = l1_1[:3]
    return (OOLONG, curVals, 0), 0, curVals

def _getHeadPierData(l_b, l_s, jokerCount):
    maxVal = 0
    useJoker = 0
    if l_b:
        maxVal = max(l_b)
    if l_s and jokerCount == 1:
        maxLs = max(l_s)
        if maxLs > maxVal:
            maxVal = maxLs
            useJoker = 1
    return (maxVal, useJoker)

def checkHeadPier(vals, jokerCount):
    """
    """
    if len(vals) + jokerCount != 3:
        return (), 0

    if jokerCount == 2:
        return (DOUBLE_GHOST, vals[0:1], jokerCount), 20

    valSet = set(vals)
    lenVS = len(valSet)
    if lenVS == 1:
        return (TRIPLET, vals[0:1], jokerCount), 2

    vals.sort(reverse=True)
    if lenVS == 2:
        valList = [vals[0], vals[-1]]
        if vals.count(valList[-1]) == 2:
            valList.reverse()
        return (PAIR, valList, jokerCount), 0

    return (OOLONG, vals, 0), 0

def checkFlush(checkList, allFlushList, jokerCount):
    """
    验证最后剩的n(5,6,8)张牌是否成同花,返回最大的同花
    """
    for vals, useJoker_2, color in allFlushList:
        if jokerCount-useJoker_2 >= 0:
            flushVals = getListIntersection(checkList, vals)
            lenFlush = len(flushVals)
            if lenFlush + jokerCount >= 5:
                useJoker = 5 - lenFlush
                if useJoker < 0:
                    useJoker = 0
                # valList = [VAL_A]*useJoker
                _flushVals = flushVals[:5-useJoker]
                # valList.extend(_flushVals)
                valList = dealFlushUseJoker(_flushVals, useJoker)
                return (FLUSH, valList, useJoker, _flushVals, color)
    return []

def checkDoubleFlush(checkList, allFlushList, jokerCount):
    """
    判断10张牌可以组成两个同花
    """
    flushList = []
    allFlushVals = []
    # print 'checkDoubleFlush', allFlushList
    for vals, useJoker_2, color in allFlushList:
        if jokerCount-useJoker_2 >= 0:
            flushVals = getListIntersection(checkList, vals)
            lenFlush = len(flushVals)
            if lenFlush + jokerCount >= 10:
                useJoker = 10 - lenFlush
                if useJoker < 0:
                    useJoker = 0
                threeLs, pCount, pairLs, oneLs = dealFlushVals(flushVals)
                jokers = []
                if useJoker > 0:
                    if pairLs and useJoker == 1:
                        jVal = pairLs[0]
                    elif oneLs:
                        jVal = oneLs[0]
                    if jVal:
                        jokers = [jVal]*useJoker
                        _flushVals = jokers + flushVals
                        # _flushVals.sort(reverse = True)
                        threeLs, pCount, pairLs, oneLs = dealFlushVals(_flushVals)
                if threeLs and pairLs:
                    return []
                if len(threeLs) == 1:
                    firstList = threeLs*3 + oneLs[-2:]
                    secondList = oneLs[:5]
                elif pairLs:
                    if pCount == 1:
                        firstList = pairLs*2 + oneLs[-3:]
                        secondList = oneLs[:5]
                    elif pCount == 2:
                        firstList = pairLs[:1]*2 + oneLs[-3:]
                        secondList = pairLs[1:2]*2 + oneLs[:3]
                    elif pCount == 3:
                        firstList = pairLs[:1]*2 + pairLs[2:3]*2 + oneLs[-1:]
                        secondList = pairLs[1:2]*2 + oneLs[:3]
                    elif pCount == 4:
                        firstList = pairLs[:1]*2 + pairLs[2:3]*2 + oneLs[-1:]
                        secondList = pairLs[1:2]*2 + pairLs[3:4]*2 + oneLs[:1]
                    else:
                        firstList = pairLs[:1]*2 + pairLs[2:3]*2 + pairLs[4:]
                        secondList = pairLs[1:2]*2 + pairLs[3:4]*2 + pairLs[4:]
                else:
                    firstList = oneLs[:10:2]
                    secondList = oneLs[1:10:2]
                if jokers:
                    hasVals_1 = _rmVals(firstList, jokers)
                else:
                    hasVals_1 = firstList[:]

                # _flushVals = [VAL_A]*useJoker
                # _flushVals.extend(flushVals)
                # firstList = _flushVals[:10:2]
                # secondList = _flushVals[1:10:2]
                # if useJoker == 2:
                    # hasVals_1 = firstList[1:]
                    # hasVals_2 = secondList[1:]
                    # useJoker_1 = useJoker_2 = 1
                # elif useJoker == 1:
                    # hasVals_1 = firstList[1:]
                    # hasVals_2 = secondList
                    # useJoker_1 = 1
                    # useJoker_2 = 0
                # else:
                    # hasVals_1 = firstList
                    # hasVals_2 = secondList
                    # useJoker_1 = useJoker_2 = 0
                # print 'flushList111'
                return ((FLUSH, firstList,useJoker,hasVals_1,color), (FLUSH,secondList,0,secondList[:], color))

            if lenFlush + jokerCount >= 5:
                useJoker = 5 - lenFlush
                if useJoker < 0:
                    useJoker = 0
                # valList = [VAL_A]*useJoker
                _flushVals = flushVals[:5-useJoker]
                # valList.extend(_flushVals)
                allFlushVals.extend(_flushVals)
                jokerCount -= useJoker
                valList = dealFlushUseJoker(_flushVals, useJoker)
                flushList.append((FLUSH, valList, useJoker, _flushVals, color))
    if len(flushList) == 2 and checkVals(allFlushVals, checkList):
        if flushList[0][1] < flushList[1][1]:
            flushList.reverse()
        # print 'allFlushList2', flushList
        return flushList
    return []

def exChange(a, b):
    return b, a


def getAllFiveHeads(l5, l4, l3, jokerCount):
    fiveList = [(v, 0) for v in l5]
    if jokerCount >= 1:
        fiveList.extend([(v, 1) for v in l4])
    if jokerCount >= 2:
        fiveList.extend([(v, 2) for v in l3])
    # print 'getAllFiveHeads', fiveList
    return fiveList

def getAllIronBranch(l4, l3, l2, jokerCount):
    fourList = [(v, 0) for v in l4]
    if jokerCount >= 1:
        fourList.extend([(v, 1) for v in l3])
    if jokerCount >= 2:
        fourList.extend([(v, 2) for v in l2])
    # print 'getAllIronBranch', fourList
    return fourList

def getAllGourd(l3, l2, l1, jokerCount):
    gourdList = []
    lenL3 = len(l3)
    if lenL3 >= 2:
        for v1 in l3:
            tmpL3 = l3[:]
            tmpL3.remove(v1)
            gourdList.extend([(v1, v2, 0) for v2 in tmpL3])
            gourdList.extend([(v1, v2, 0) for v2 in l2])
    elif lenL3 == 1:
        v1 = l3[0]
        gourdList.extend([(v1, v2, 0) for v2 in l2])
    if jokerCount > 0:
        for v1 in l2:
            tmpL2 = l2[:]
            tmpL2.remove(v1)
            gourdList.extend([(v1, v2, 1) for v2 in tmpL2 if v1 > v2])
            gourdList.extend([(v1, v2, 1) for v2 in l3 if v1 > v2])
    # print 'getAllGourd', gourdList
    return gourdList

def getAllTriplet(l3, l2, l1, jokerCount):
    threeList = [(v, 0) for v in l3]
    if jokerCount >= 1:
        threeList.extend([(v, 1) for v in l2])
    if jokerCount >= 2:
        threeList.extend([(v, 2) for v in l1])
    # print 'getAllTriplet', threeList
    return threeList

def getAllPairs(l2, l1, jokerCount):
    pairList = [(v, 0) for v in l2]
    if jokerCount > 0:
        pairList.extend([(v, 1) for v in l1])
    # print 'getAllPairs', pairList
    return pairList


def getMaxFlushList(color2vals):
    """
    获得每种花色的最大同花
    """
    maxFlushList = []
    for color, vals in color2vals.items():
        # vals 从大到小已排序
        if len(vals) >= 5:
            maxFlushList.append(vals[:5])
    # print 'getMaxFlushList', maxFlushList
    return maxFlushList

def getListIntersection(ls_1, ls_2):
    """
    获得两个列表的交集，包含重复值
    """
    interVals = []
    for v in set(ls_1):
        if v in ls_2:
            minCount = min(ls_1.count(v), ls_2.count(v))
            interVals.extend([v]*minCount)
    interVals.sort(reverse=True)
    # print 'getListIntersection', interVals
    return interVals

def checkVals(vals, allVals):
    for val in set(vals):
        if vals.count(val) > allVals.count(val):
            return False
    return True

def hasFlushTup(vals, jokerCount, color=''):
    """
    获取存在同花的列表
    """
    lenVals = len(vals)
    rsltList = []
    if lenVals+jokerCount >= 5:
        useJoker = 5-lenVals
        if useJoker < 0:
            useJoker = 0
        rsltList = [vals, useJoker, color]
    # print 'hasFlushTup', rsltList
    return rsltList

def getOneJoint(vals, jokerCount, color=''):
    valSet = set(vals)
    _len = len(valSet)+jokerCount
    if _len < 5:
        return []
    jointList = []
    if VAL_A in valSet:
        rsltTup = checkJoint(STRAIGHT_1_5, valSet, jokerCount, color)
        if rsltTup:
            jointList.append(rsltTup)
    minVals = [v for v in valSet if v < 10]
    minVals.append(10)
    minVals.sort()
    for val in minVals:
        rsltTup = checkJoint(xrange(val, val+5), valSet, jokerCount, color)
        if rsltTup:
            jointList.append(rsltTup)
    # jointList = sorted(jointList, key=lambda x:x[0], reverse = True)
    # print 'getOneJoint', jointList
    return jointList

def getTwoJoint(vals, jokerCount, color=''):
    """
    """
    jointList = getOneJoint(vals, jokerCount, color)
    if not jointList:
        return [], []
    jointList = joinListSort(jointList)
    twoJointList = []
    for jointTup in jointList:
        minVal, useJoker, hasValSet, _ = jointTup
        jokerCount -= useJoker
        _vals = _rmVals(vals, hasValSet)
        jointList_2 = getOneJoint(_vals, jokerCount, color)
        if not jointList_2:
            continue
        jointList_2 = joinListSort(jointList_2)
        for jointTup_2 in jointList_2:
            minVal_2 = jointTup_2[0]
            if minVal_2 <= minVal:
                twoJointList.append((jointTup, jointTup_2))
    return twoJointList, jointList

def checkJoint(tmpList, valSet, jokerCount, color):
    valSet_n = set(tmpList)&valSet
    lenVS_n = len(valSet_n)
    if lenVS_n + jokerCount >= 5:
        useJoker = 5-lenVS_n
        minVal = min(tmpList)
        if minVal == 2 and VAL_A in tmpList:
            minVal = 1
        return (minVal, useJoker, valSet_n, color)
    return ()

def _isStraight_1(type, val):
    return (type in [STRAIGHT, STRAIGHT_FLUSH] and val == 1)

def __compare_1(l, r):
    l0, l1, l2, l3 = l[0], l[1], l[2], l[3]
    r0, r1, r2, r3 = r[0], r[1], r[2], r[3]
    l10, l20, l30 = l1[0], l2[0], l3[0]
    l11, l21, l31 = l1[1], l2[1], l3[1]
    r10, r20, r30 = r1[0], r2[0], r3[0]
    r11, r21, r31 = r1[1], r2[1], r3[1]
    # print '__compare_1',l10, l11, l20, l21, l30, l31
    if _isStraight_1(l10, l11):
        l11 = 9.5
    if _isStraight_1(r10, r11):
        r11 = 9.5
    if _isStraight_1(l20, l21):
        l21 = 9.5
    if _isStraight_1(r20, r21):
        r21 = 9.5
    if l10 == r10 == FLUSH:
        l11 = dealFlushVals(l11)
        r11 = dealFlushVals(r11)
    if l20 == r20 == FLUSH:
        l21 = dealFlushVals(l21)
        r21 = dealFlushVals(r21)
    if l0 > r0:
        return 1
    elif l0 == r0:
        if l10 > r10:
            return 1
        elif l10 == r10:
            if l20 > r20:
                return 1
            elif l20 == r20:
                if l30 > r30:
                    return 1
                elif l30 == r30:
                    if l11 > r11:
                        return 1
                    elif l11 == r11:
                        if l21 > r21:
                            return 1
                        elif l21 == r21:
                            if l31 > r31:
                                return 1
                            return -1
                        return -1
                    return -1
                return -1
            return -1
        return -1
    return -1

def __compare_2(l, r):
    l0, l1 = l[0], l[1]
    r0, r1 = r[0], r[1]
    if l0 == 1:
        l0 = 9.5
    if r0 == 1:
        r0 = 9.5
    if l1 > r1:
        return 1
    elif l1 == r1:
        return 1 if l0 < r0 else -1
    else:
        return -1

def allPierSort(allPierList):
    # print 'allPierSortss', allPierList
    allPierList = sorted(allPierList, cmp = __compare_1, reverse=True)
    # print 'allPierSort', allPierList
    return allPierList

def joinListSort(joinList):
    joinList = sorted(joinList, cmp = __compare_2)
    # joinList = sorted(sorted(joinList, key=lambda x:x[0], reverse = True), key=lambda x:x[1])
    # print 'joinListSort', joinList
    return joinList
#-----------------------------------------------------

# ===================================================== 类

class CardsModel(object):
    """
    牌型基类
    """
    def __init__(self, cards, type, vals=0, joker2Crads=[]):
        self.cards = cards
        self.type = type
        self.vals = vals
        self.joker2Crads = joker2Crads

    # ">"
    def __gt__(self, m):
        return self.type > m.type or (self.type == m.type and self.vals > m.vals)

    # "=="
    def __eq__(self, m):
        return self.type == m.type and self.vals == m.vals

    # "<"
    def __lt__(self, m): return not self.__gt__(m)

    def __repr__(self):
        return type2Texts[self.type] + ', cards(%s), vals(%s)'%(self.get_cardStr(), self.vals)
    __str__ = __repr__

    def get_type(self):
        return self.type

    def get_cards(self):
        return self.cards

    def get_cardStr(self):
        # print '\nself.joker2Crads', self.joker2Crads
        # if self.joker2Crads:
            # return ','.join(self.cards)+';'+','.join(self.joker2Crads)
        return ','.join(self.cards)

class SpecialType(CardsModel):
    def __gt__(self, m):
        if self.isEq(m):
            return False
        return self.type > m.type

    def isEq(self, m):
        return (self.type in FIRST_EQ and m.type in FIRST_EQ) or \
            (self.type in SECONED_EQ and m.type in SECONED_EQ)

class FiveHeads(CardsModel): pass

class StraightFlush(CardsModel):
    def __gt__(self, m):
        if self.type > m.type:
            return True
        if self.type == m.type:
            selfVal = self.vals[0]
            otherVal = m.vals[0]
            selfVal = dealAS(selfVal)
            otherVal = dealAS(otherVal)
            return selfVal > otherVal

class IronBranch(CardsModel): pass

class Gourd(CardsModel): pass

class Flush(CardsModel):
    def __gt__(self, m):
        if self.type > m.type:
            return True
        if self.type == m.type:
            return dealFlushVals(self.vals) > dealFlushVals(m.vals)

class Straight(CardsModel):
    def __gt__(self, m):
        if self.type > m.type:
            return True
        if self.type == m.type:
            selfVal = self.vals[0]
            otherVal = m.vals[0]
            selfVal = dealAS(selfVal)
            otherVal = dealAS(otherVal)
            return selfVal > otherVal

class Triplet(CardsModel):
    def __gt__(self, m):
        if m.type == DOUBLE_GHOST and len(self.vals) > 1:
            return self.vals > m.vals
        return super(Triplet, self).__gt__(m)

class TwoPairs(CardsModel): pass

class Pair(CardsModel): pass

class Oolong(CardsModel): pass

class DoubleGhost(CardsModel):
    def __gt__(self, m):
        if m.type == TRIPLET and len(m.vals) > 1:
            return self.vals > m.vals
        return super(DoubleGhost, self).__gt__(m)

class CardsInvalid(CardsModel):
    def __gt__(self, m):
        return False

# ======================================================test
def cardSort(cards):
    if not cards:
        return cards
    cards = sorted(cards, key=lambda x:x[1] , reverse = True)
    sortedCards = sorted(cards, key=lambda x:card2val[x[0]] , reverse = True)
    return sortedCards

# ----------------------------------------- (测试)
if __name__ == '__main__':
    # 测试函数 CardsModelFactory()
    # cStr = 'Ac,Lj,Jc,Bj,5c'
    # curCards = cStr.split(',')
    # rsult = CardsModelFactory(curCards)
    # print rsult.__repr__()
    # print CardsModelFactory(['Aa','2a','3a','4b','5a']) > CardsModelFactory(['9b','Tc','Jb','Qb','Kb'])
    
    # 测试函数 getDefaultType()
    # 牌型测试
    # cStr = 'Ad,Jd,Jd,Jc,Tc,9c,8c,7c,6c,5d,4d,3b,2a'
    # curCards = cStr.split(',')
    curCards = ['Bj', 'Lj', 'Ad', 'Kb', 'Ka', 'Td', '8d', '6d', '5b', '4d', '3d', '3c', '3a']
    curCards = cardSort(curCards)
    rsult = getDefaultType(curCards)
    rsult.reverse()
    ins_0 = rsult[0]
    ins_1 = rsult[1]
    ins_2 = rsult[2]
    print ins_0.__repr__(), ins_1.__repr__(), ins_2.__repr__()

    # 效率测试
    # cardPool = ['Ad', 'Ac', 'Ab', 'Aa', 'Kd', 'Kc', 'Kb', 'Ka', \
        # 'Jd', 'Jc', 'Jb', 'Ja', 'Qd', 'Qc', 'Qb', 'Qa', '3d', '3c', '3b', '3a', \
        # '2d', '2c', '2b', '2a', '5d', '5c', '5b', '5a', '4d', '4c', '4b', '4a', \
        # '7d', '7c', '7b', '7a', '6d', '6c', '6b', '6a', '9d', '9c', '9b', '9a', \
        # '8d', '8c', '8b', '8a', 'Td', 'Tc', 'Tb', 'Ta', 'Lj', 'Bj', \
        # 'Ad', 'Ac', 'Ab', 'Kd', 'Kc', 'Kb', 'Qd', 'Qc', 'Qb', 'Jd', 'Jc']
    # random.shuffle(cardPool)
    # cards = cardPool[:]
    # allList = []
    # for i in xrange(100):
        # if not cards:
            # random.shuffle(cardPool)
            # cards = cardPool[:]
        # random.shuffle(cards)
        # curCards = cards[:13]
        
        # cards = cards[13:]
        # curCards = cardSort(curCards)
        # allList.append(curCards)
        # print '22222222222', len(curCards), curCards
    # aaa = []
    # t_s = getTimestamp()
    # for c in allList:
        # aaa.append(getDefaultType(c))
    # t_e = getTimestamp()
    # print 'time', t_e-t_s
    # for j in aaa:
        # if j:
            # j.reverse()
            # ins_0 = j[0]
            # ins_1 = j[1]
            # ins_2 = j[2]
            # print ins_0.get_cardStr(), ins_1.get_cardStr(), ins_2.get_cardStr()

    # 测试函数 getSpecialType()
    # cards = 'Ad,Kd,Qd,Qd,Td,9d,8d,7d,6c,5c,4c,3c,7c'
    # cards = 'Ad,Ad,Ad,Ad,Ad,Ab,Ad,7d,7c,6c,5c,4c,3c'
    # cards = 'Ad,Ad,Ad,Ad,Ad,Ab,Kd,Kd,Kc,Kc,Kc,Kc,3c'
    # cards = 'Ad,Ad,Ad,Ad,Kd,Kb,Kd,Kd,2c,2c,2c,2c,3c'
    cards = 'Ad,2d,3d,2c,3c,5c,5c,6c,4b,5b,6b,7b,8b'
    clist = cardSort(cards.split(','))
    print 'cdcdcdc', clist
    # clist = ['Ac', 'Kc', 'Qc', 'Jd', 'Jc', 'Td', '9d', '8d', '7d', '5c', '4c', '3c', '2c']
    aaarslt = getSpecialType(clist, True)
    print aaarslt.__repr__()
    # clist = ['Ab', 'Qb', 'Td', 'Tc', 'Ta', '8d', '6c', '6b', '5c', '5a', '4d', '3c', '3a']
    # aaarslt = getSpecialType(clist, True)
    # print aaarslt.__repr__()



    pass
    # 待完成