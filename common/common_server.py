# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: Server factory
"""

from twisted.internet import reactor, threads

import consts
from log import log, LOG_LEVEL_RELEASE, LOG_LEVEL_ERROR
import net_resolver_pb
from server import Server
import redis_batch
import redis_instance

from common_db_define import *
from card_define import *
from pb_utils import *
from common.db_utils import isServiceOutDate, userDBLogin, userDBLogout
from common.protocols.poker_consts import *
from datetime import datetime
from common.logic.global_control import GlobalControl
from common.i18n.i18n import initializeGame, isValidLang, getLangInst
from peer import Peer
from base_server import BaseServer

import poker_pb2
import replay4proto_pb2

import traceback
from redis.exceptions import RedisError
import time

import random
import math

import urllib2
import urllib
import socket
import xml.dom.minidom
from common.pyDes import des, PAD_PKCS5
import md5
import json
import copy
import re
import struct

class CommonServer(BaseServer):
    def __init__(self, *args, **kwargs):
        super(CommonServer, self).__init__(*args, **kwargs)

    def registerProtocolResolver(self):
        unpacker = net_resolver_pb.Unpacker
        self.recverMgr.registerCommands( (\
            unpacker(poker_pb2.C_S_REFRESH_DATA, poker_pb2.C_S_RefreshData, self.onTryRefresh), \
            unpacker(poker_pb2.C_S_GAME_START, poker_pb2.C_S_GameStart, self.onGameStart), \
            unpacker(poker_pb2.C_S_DO_ACTION, poker_pb2.C_S_DoAction, self.onDoAction), \
            unpacker(poker_pb2.C_S_READY_NEXT, poker_pb2.C_S_ReadyNext, self.onReadyNext), \
            unpacker(poker_pb2.C_S_GET_OLD_BALANCE, poker_pb2.C_S_GetOldBalance, self.onGetOldBalance), \
            ) )
        packer = net_resolver_pb.Packer
        self.senderMgr.registerCommands( (\
            packer(poker_pb2.S_C_REFRESH_DATA, poker_pb2.S_C_RefreshData), \
            packer(poker_pb2.S_C_SET_START, poker_pb2.S_C_SetStart), \
            packer(poker_pb2.S_C_DEAL_CARDS, poker_pb2.S_C_DealCards), \
            packer(poker_pb2.S_C_TURN_ACTION, poker_pb2.S_C_TurnAction), \
            packer(poker_pb2.S_C_DO_ACTION_RESULT, poker_pb2.S_C_DoActionResult), \
            packer(poker_pb2.S_C_BALANCE, poker_pb2.S_C_Balance), \
            packer(poker_pb2.S_C_GAME_START_RESULT, poker_pb2.S_C_GameStartResult), \
            packer(poker_pb2.S_C_OLD_BALANCE, poker_pb2.S_C_OldBalance), \
        ) )

        super(CommonServer, self).registerProtocolResolver()

    def onTryRefresh(self, player, req):
        '''
        刷新数据
        '''
        game = player.game


        log(u"[try refresh]nickname[%s] room[%s]."%(player.nickname, game.roomId), LOG_LEVEL_RELEASE)

        self.sendRefreshData(game, player)

    def fillRefreshFail(self, player, resp):
        resp.result = False
        errorStr = '未加入游戏或游戏已结束，刷新失败'.decode('utf-8')
        resp.reason = errorStr
        log(u"[sendRefreshFail][error]nickname[%s] is not in game."%(player.nickname), LOG_LEVEL_RELEASE)

    def sendRefreshData(self, game, player):
        resp = poker_pb2.S_C_RefreshData()
        if not game:
            self.fillRefreshFail(player, resp)
            self.sendOne(player, resp)
            return

        self.tryRefresh(game, player, resp)
        self.sendOne(player, resp)

    def tryRefresh(self, game, player, resp):
        side = player.chair
        resp.result = True

        resp.data.gameInfo.result = True
        resp.data.gameInfo.isRefresh = False
        pbPlayerInfo(resp.data.gameInfo.selfInfo, game, side, isNeedMyData = True)
        pbRoomInfo(resp.data.gameInfo.roomInfo, self, game)
        resp.data.Countdown = 15
        for gamePlayer in game.getPlayers():
            # if not gamePlayer:
                # continue
            playerSide = gamePlayer.chair
            playerGameData = resp.data.playerDatas.add()
            playerGameData.side = playerSide
            playerGameData.isOnline = gamePlayer.isOnline
            game.getActionedCards(playerGameData.cardDatas, playerSide, side)
            playerData = resp.data.gameInfo.roomInfo.playerList.add()
            pbPlayerInfo(playerData, game, playerSide)

        resp.data.currentSide = game.curPlayerSide
        if game.dealerSide != -1:
            resp.data.dealerSide = game.dealerSide
        else:
            resp.data.dealerSide = 0
        resp.data.stage = game.stage

        #allowAction
        if game.curActioningSide == side:
            game.fillAllowAction(resp.data.allowAction)

        resp.data.dissolveStage = 0
        if game.dissolvePlayerSide >= 0:
            resp.data.dissolveStage = 1
        if game.dissolve[side] != None:
            resp.data.dissolveStage = 2
        if resp.data.dissolveStage:
            for otherPlayer in game.getPlayers():
                voteData = resp.data.voteData.vote.add()
                dissolveSide = otherPlayer.chair
                if game.dissolve[dissolveSide] != None:
                    voteData.result = game.dissolve[dissolveSide]
                voteData.nickname = otherPlayer.nickname
            resp.data.voteData.nickname = game.players[game.dissolvePlayerSide].nickname
            resp.data.voteData.dissolveSide = game.dissolvePlayerSide
            dissovedCounterMs = int((game.dissovedCounterMs - self.getTimestamp()) / 1000)
            if dissovedCounterMs >= 0:
                resp.data.voteData.waitTime = dissovedCounterMs
            else:
                resp.data.voteData.waitTime = 0

    def onDoAction(self, player, req):
        if not player.game:
            log(u'[try do action][error]nickname[%s] is not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        log(u'[try do action]room[%s]nickname[%s] action[%s] datas[%s].'%(player.game.roomId, player.nickname, req.action, req.datas), LOG_LEVEL_RELEASE)
        player.game.onDoAction(player, req.action, req.datas, req.num)

    def onGameStart(self, player, req):


        if not player.game:
            log(u'[try start game][error]nickname[%s] is not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        self.dynamic.startGame(player.game, self, player)
        redis = self.getPublicRedis()
        redis.hset(ROOM2SERVER % (player.game.roomId), "gameState", 1)
        log(u'[try start game]nickname[%s] room[%s].'%(player.nickname, player.game.roomId), LOG_LEVEL_RELEASE)
        player.game.onGameStart(player)

    def onReadyNext(self, player, req): #关闭结算窗口
        if not player.game:
            log(u'[ready next][error]nickname[%s] not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return
        redis = self.getPublicRedis()
        redis.hset(ROOM2SERVER % (player.game.roomId), "gameState", 1)
        log(u'[ready next]nickname[%s] room[%s].'%(player.nickname, player.game.roomId), LOG_LEVEL_RELEASE)
        player.game.onReady2NextGame(player)

    def onGetOldBalance(self, player, req): #获得上局回放数据
        oldBalanceData = None
        if player.game:
            oldBalanceData = player.game.oldBalanceData
        resp = poker_pb2.S_C_OldBalance()
        if oldBalanceData:
            log(u'[on get old balance]get old balance succeed.', LOG_LEVEL_RELEASE)
            resp.balance.CopyFrom(oldBalanceData)
        self.sendOne(player, resp)

