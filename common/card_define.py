# -*- coding:utf-8 -*-
#!/bin/python

import re


CARD2SCORES = {
        'T'         :       10,
        'J'         :       11,
        'Q'         :       12,
        'K'         :       13,
        'A'         :       1
}

DIAMOND = 'a' #方块
CLUB = 'b' #梅花
HEART = 'c' #红心
SPADE = 'd' #黑桃

BLACK_COLOR = (CLUB, SPADE)
RED_COLOR = (DIAMOND, HEART)

#大小王
LITTLE_JOKER = 'Lj'
BIG_JOKER = 'Bj'
JOKER_LIST = [LITTLE_JOKER, BIG_JOKER]
JOKER_VALS = [16, 17]
JOKER_VALS_SET = set(JOKER_VALS)
LITTLE_VAL = 16
BIG_VAL = 17

#万能牌
WILD_CARD = 'w'
#GM
GET_CARDS = 1

#ACTION
PASS = 0
DISCARD = 1

def getVal2Card():
    val2card_map = {}
    for i in xrange(3, 10):
        val2card_map[i] = str(i)
    val2card_map[10] = 'T'
    val2card_map[11] = 'J'
    val2card_map[12] = 'Q'
    val2card_map[13] = 'K'
    val2card_map[14] = 'A'
    val2card_map[15] = '2'
    val2card_map[16] = 'L'
    val2card_map[17] = 'B'
    val2card_map[15.5] = 'W'
    return val2card_map

def getCard2Val(val2card_map):
    card2val_map = {}
    for k, v in val2card_map.iteritems():
        card2val_map[v] = k
    return card2val_map


reCards = re.compile(r"[2-9TJQKA][a-dw]|[LBW]j")

val2card_map = getVal2Card()
card2val_map = getCard2Val(val2card_map)
CARDS_SET = set(card2val_map.keys())

card_set = CARDS_SET-set(['L','B','W'])
color_set = set([DIAMOND, CLUB, HEART, SPADE])

