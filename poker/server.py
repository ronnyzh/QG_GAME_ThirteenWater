# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: Server factory
"""

from common.common_server import CommonServer
from common.log import log, LOG_LEVEL_RELEASE, LOG_LEVEL_ERROR
from common import net_resolver_pb
from common.protocols.poker_consts import *
from common import baseProto_pb2
from common.common_db_define import *

from player import Player
from game import Game
from consts import *

from db_define import *

import thirteenWater_poker_pb2
import private_mahjong_pb2
import redis_instance

import copy

class PokerServer(CommonServer):
    protocol = Player

    def __init__(self, *args, **kwargs):
        super(PokerServer, self).__init__(*args, **kwargs)

    def getGameID(self):
        return MY_GAMEID

    def getGameModule(self, *initData):
        return Game(*initData)

    def registerProtocolResolver(self):
        unpacker = net_resolver_pb.Unpacker
        self.recverMgr.registerCommands( (\
              unpacker(thirteenWater_poker_pb2.C_S_ARRANGED_CARDS, thirteenWater_poker_pb2.C_S_ArrangedCards, self.onArrangedCards), \
              unpacker(thirteenWater_poker_pb2.C_S_SET_MULTIPLE, thirteenWater_poker_pb2.C_S_SetMultiple, self.onSetMultiple), \
              unpacker(thirteenWater_poker_pb2.C_S_GET_ARRANGED_CARDS, thirteenWater_poker_pb2.C_S_GetArrangedCards, self.onGetArrangedCards), \
            ) )
        packer = net_resolver_pb.Packer
        self.senderMgr.registerCommands( (\
            packer(thirteenWater_poker_pb2.S_C_REFRESH_DATAS, thirteenWater_poker_pb2.S_C_RefreshDatas), \
            packer(thirteenWater_poker_pb2.S_C_NEW_DEAL_CARDS, thirteenWater_poker_pb2.S_C_NewDealCards), \
            packer(thirteenWater_poker_pb2.S_C_ARRANGED_CARDS, thirteenWater_poker_pb2.S_C_ArrangedCards), \
            packer(thirteenWater_poker_pb2.S_C_COMPARE, thirteenWater_poker_pb2.S_C_Compare), \
            packer(thirteenWater_poker_pb2.S_C_SET_MULTIPLE, thirteenWater_poker_pb2.S_C_SetMultiple), \
            packer(thirteenWater_poker_pb2.S_C_MULTIPLE_RESULT, thirteenWater_poker_pb2.S_C_MultipleResult), \
            packer(thirteenWater_poker_pb2.S_C_SEND_OK_DATA, thirteenWater_poker_pb2.S_C_SendOkData), \
            packer(thirteenWater_poker_pb2.S_C_MY_ARRANGED_CARDS, thirteenWater_poker_pb2.S_C_MyArrangedCards), \
            packer(private_mahjong_pb2.S_C_BANINTERACTION, private_mahjong_pb2.S_C_BanInteraction),
        ) )

        super(PokerServer, self).registerProtocolResolver()

    def onArrangedCards(self, player, req):
        if not player.game:
            log(u'[onArrangedCards][error] player[%s] not in game.'%(player), LOG_LEVEL_RELEASE)
            return

        log(u'[onArrangedCards]player[%s] req[%s].'%(player, req), LOG_LEVEL_RELEASE)

        player.game.onArrangedCards(player, req.cards, req.cardTypes)

    def onSetMultiple(self, player, req):
        if not player.game:
            log(u'[onSetMultiple][error] player[%s] not in game.'%(player), LOG_LEVEL_RELEASE)
            return

        log(u'[onSetMultiple]player[%s] req[%s].'%(player, req), LOG_LEVEL_RELEASE)

        player.game.onSetMultiple(player, req.multiple)

    def onGetArrangedCards(self, player, req):
        if not player.game:
            log(u'[onGetArrangedCards][error] player[%s] not in game.'%(player), LOG_LEVEL_RELEASE)
            return

        log(u'[onGetArrangedCards]player[%s] req[%s].'%(player, req), LOG_LEVEL_RELEASE)

        player.game.onGetArrangedCards(player)

    def onTryRegSucceed(self, player, cache, isReg, session, roomSetting, mode, isSendMsg = True):
        if cache in self.loginLocks:
            del self.loginLocks[cache]

        if not player or not player.hashKey:
            log(u"[try login][error]not found player hashKey.", LOG_LEVEL_RELEASE)
            return

        redis = self.getPublicRedis()

        #获得所属地区
        # tableIP2CountryCode = FORMAT_IP2REGIONCODE%(player.ip)
        # region = redis.get(tableIP2CountryCode)
        # if region:
            # player.region = region.decode('utf-8')
        # else:
            # player.region = ''

        player.nickname = player.nickname.decode('utf-8')

        resp = baseProto_pb2.S_C_Connected()
        resp.result = True
        resp.curTimestamp = self.getTimestamp()
        resp.myInfo.result = True
        resp.myInfo.isRefresh = False

        log(u"[try login]account[%s] login succeed, nickname[%s]."%(player.account, player.nickname), LOG_LEVEL_RELEASE)

        #断线重连
        exitPlayerData = EXIT_PLAYER%(player.account)
        if redis.exists(exitPlayerData):
            ip, port, roomId, side = redis.hmget(exitPlayerData, ('ip', 'port', 'game', 'side'))
            side = int(side)
            if ip == self.ip and port == self.port and roomId in self.globalCtrl.num2game.keys():
                resp.myInfo.isRefresh = True 

                redis.delete(exitPlayerData)
                game = self.globalCtrl.num2game[roomId]
                playerRobit = game.players[side]
                log(u"[try login]try join room[%s] again."%(roomId), LOG_LEVEL_RELEASE)

                #player.doReconnect(playerMirror)
                game.setPlayerCopy(player, playerRobit)
                game.exitPlayers.remove(side)
                # game.notLeaveGame(side)
                player.isOnline = True
                _resp = baseProto_pb2.S_C_OnlineState()
                _resp.changeSide = player.chair
                _resp.isOnline = player.isOnline
                game.sendExclude((player,), _resp)

                #房间信息入库
                self.savePlayerGameData(player, game.roomId)
            else:
                if ip == self.ip and port == self.port:
                    redis.delete(exitPlayerData)
                log(u"[try login][error]game[%s %s %s] is not in this server[%s]."%(ip, port, roomId, self.serviceTag), LOG_LEVEL_RELEASE)
                resp.result = False
                str = '找不到房间'.decode('utf-8')
                resp.reason = str
                self.sendOne(player, resp)
                return

        log(u"[try login]roomCards[%s] sex[%s]."%(player.roomCards, player.sex), LOG_LEVEL_RELEASE)

        self.account2players[player.account] = player

        self.userDBOnLogin(player, isReg)

        if resp.myInfo.isRefresh: #重连
            #一控四
            if player.game.controlPlayerSide == player.chair:
                log(u'[try control all again]nickname[%s] chair[%s] game[%s] controlSide[%s].'\
                        %(player.nickname, player.chair, player.game, player.game.controlPlayerSide), LOG_LEVEL_RELEASE)
                self.tryConnectingRobot(player.game, player)
                player.isControlByOne = True
            else:
                self.sendOne(player, resp)
            return

        self.tryRoomAction(player, resp, session, roomSetting, mode, isSendMsg = isSendMsg)

    def sendRefreshData(self, game, player):
        resp = thirteenWater_poker_pb2.S_C_RefreshDatas()
        if not game:
            self.fillRefreshFail(player, resp)
            self.sendOne(player, resp)
            return

        resp.result = True
        self.tryRefresh(game, player, resp.refreshData)

        curStage = game.gameStage
        print 'sendRefreshData', curStage

        resp.gameStage = curStage

        # 上层
        if game.hasDoODealer:
            if curStage == CHOOSE_MULTIPLE_S and player.multiple == 0:
                resp.chooseMultiple.canChoose.extend(game.getCanChooseMultiple())
            if curStage >= CHOOSE_MULTIPLE_S:
                for _player in game.getPlayers():
                    multipleData = resp.multipleList.add()
                    multipleData.side = _player.chair
                    multipleData.multiple = _player.multiple

        if curStage == DEALING_E:
            resp.cards = ','.join(player.handleMgr.cards)
            resp.defultCards = ','.join(player.defaultCards)
            type = player.getSpecialType()
            resp.specialType = type
            resp.typeScore = game.getSpecialScore(type, -1)
            resp.startTime = game.startTime
            resp.waitCompareSides.extend(game.hasArrangedSides)
        elif curStage >= COMPARE_S:
            oldBalanceData = game.oldBalanceData
            resp.balanceData.CopyFrom(oldBalanceData)
            resp.okList.extend(game.okList)
            print 'sendRefreshData1', oldBalanceData, resp.balanceData

        log(u'[sendRefreshData] resp[%s]'%(resp), LOG_LEVEL_RELEASE)
        self.sendOne(player, resp)

        if player.game.banInteraction:
            resp = private_mahjong_pb2.S_C_BanInteraction()
            resp.result = True
            self.sendOne(player, resp)

