#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    游戏配置
"""

from common.log import log
from common.gameobject import GameObject
from common import consts
from common.common_db_define import *
from common.protocols.poker_consts import *
from common.protocols import *
# from common.data.fish_levels import FISH_LEVELS_DATA

import redis_instance

from datetime import datetime

import random
import math
MAX_LOSE_COIN = 100000.0
ODDS_OUT = 10000.0
#MAX_TAN_DELTA = 1.41
#MAX_TAN = math.tan(MAX_TAN_DELTA)
ODDS_NAGATIVE_OFFSET = 0.01
ODDS_MIN = 0.2
#单个玩家最高赢输比2%
MAX_PLAYER_PROFIT_RATE = 0.02
ODDS_NORMAL = 0.72
ODDS_LIMIT = 0.5

TICK_GAMES_COUNT = 10

# GAME_NUM = 1000

class GlobalControl(GameObject):
    def __init__(self):
        self.loadRoomInfo()
        self.num2game = {}

        self.currencyAgentCashRefreshLock = False

        self.outCoinAccountsPool = {}
        self.inCoinAccountsPool = {}

    def loadRoomInfo(self):
        self.tickGameIdx = 0
        self.gameList = []

    def getEmptyGames(self):
        return [game for game in self.gameList if (game.getEmptyChair() != consts.SIDE_UNKNOWN)]

    def getTickGames(self):
        countGames = len(self.gameList)
        #log('games count[%d] tickIdx[%d]'%(countGames, self.tickGameIdx))
        if countGames <= 0:
            return []
        if self.tickGameIdx >= countGames:
            self.tickGameIdx = 0
        ret = self.gameList[self.tickGameIdx:self.tickGameIdx+TICK_GAMES_COUNT]
        self.tickGameIdx += TICK_GAMES_COUNT
        return ret

    def addGame(self, game, gameId):
        redis = redis_instance.getInst(PUBLIC_DB)

        #test
        roomId = redis.spop('gameTestNnm:set')
        if not roomId:
            roomId = redis.spop(GAME_ROOM_SET)
        # if not roomId:
            # numSet = xrange(MAX_COUNT)
            # redis = redis_instance.getInst(PRIVATE_DB)
            # redis.set(MAX_ROOM_NUM, MAX_COUNT)
            # redis.sadd(GAME_ROOM_SET, *numSet)
            # roomId = redis.spop(GAME_ROOM_SET)
        if not roomId:
            return False
        gameTable = GAME_TABLE%(gameId)
        gameName = redis.hget(gameTable,'name')
        if gameName:
            game.roomName = gameName
        game.roomId = "%06d"%(int(roomId))
        game.roomId = passwd = "%06d"%(int(roomId))
        game.gameName = gameName
        self.num2game[game.roomId] = game
        self.gameList.append(game)
        return True

    def addClubGame(self, game, gameId, roomId):
        """ 新增俱乐部房间

        """
        redis = redis_instance.getInst(PUBLIC_DB)
        #test
        # roomId = redis.spop('gameTestNnm:set')
        # if not roomId:
        #     roomId = redis.spop(GAME_ROOM_SET)
        # if not roomId:
            # numSet = xrange(MAX_COUNT)
            # redis = redis_instance.getInst(PRIVATE_DB)
            # redis.set(MAX_ROOM_NUM, MAX_COUNT)
            # redis.sadd(GAME_ROOM_SET, *numSet)
            # roomId = redis.spop(GAME_ROOM_SET)
        if not roomId:
            return False
        gameTable = GAME_TABLE%(gameId)
        gameName = redis.hget(gameTable,'name')
        if gameName:
            game.roomName = gameName
        game.roomId = "%06d"%(int(roomId))
        game.roomId = passwd = "%06d"%(int(roomId))
        game.gameName = gameName
        self.num2game[game.roomId] = game
        self.gameList.append(game)
        return True


    def removeGame(self, game):
        if game.roomId in self.num2game:
            del self.num2game[game.roomId]
            num = game.roomId
            redis = redis_instance.getInst(PUBLIC_DB)
            redis.sadd(GAME_ROOM_SET, num)
        if game in self.gameList:
            self.gameList.remove(game)
