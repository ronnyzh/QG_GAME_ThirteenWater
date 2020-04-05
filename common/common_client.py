#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    Client
"""

from log import log, LOG_LEVEL_RELEASE
import net_resolver_pb
from client import Client
import redis_instance

import baseProto_pb2
import poker_pb2

import time
import random

class CommonClient(Client):

    def __init__(self, *args, **kwargs):
        if 'account' in kwargs:
            self.account = kwargs['account']
            del kwargs['account']
        if 'passwd' in kwargs:
            self.passwd = kwargs['passwd']
            del kwargs['passwd']
        if 'regAction' in kwargs:
            self.regAction = kwargs['regAction']
            del kwargs['regAction']
        if 'roomId' in kwargs:
            self.roomId = kwargs['roomId']
            del kwargs['roomId']
        super(CommonClient, self).__init__(*args, **kwargs)

        self.peer = None #链接的服务器
        self.cards = [] #手牌列表
        self.side = -1 #位置

    def onAddPeer(self, peer):
        self.peer = peer

    def onRemovePeer(self, peer):
        self.peer = None

    def isValidPacket(self, msgName):
        return True

    def registerProtocolResolver(self):
        packer = net_resolver_pb.Packer
        self.senderMgr.registerCommands( (\
            packer(baseProto_pb2.C_S_CONNECTING, baseProto_pb2.C_S_Connecting), \
            packer(baseProto_pb2.C_S_DEBUG_CONNECTING, baseProto_pb2.C_S_DebugConnecting), \
            packer(baseProto_pb2.C_S_EXIT_ROOM, baseProto_pb2.C_S_ExitRoom), \
            packer(baseProto_pb2.C_S_PING, baseProto_pb2.C_S_Ping), \
            packer(baseProto_pb2.C_S_TALK, baseProto_pb2.C_S_Talk), \
            packer(baseProto_pb2.C_S_GM_CONTROL, baseProto_pb2.C_S_GMControl), \
            packer(baseProto_pb2.C_S_DISSOLVE_ROOM, baseProto_pb2.C_S_DissolveRoom), \
            packer(baseProto_pb2.C_S_DISSOLVE_VOTE, baseProto_pb2.C_S_DissolveVote), \
            packer(baseProto_pb2.C_S_DEBUG_PROTO, baseProto_pb2.C_S_DebugProto), \
            packer(baseProto_pb2.C_S_GPS, baseProto_pb2.C_S_Gps), \
            
            packer(poker_pb2.C_S_REFRESH_DATA, poker_pb2.C_S_RefreshData), \
            packer(poker_pb2.C_S_GAME_START, poker_pb2.C_S_GameStart), \
            packer(poker_pb2.C_S_DO_ACTION, poker_pb2.C_S_DoAction), \
            packer(poker_pb2.C_S_READY_NEXT, poker_pb2.C_S_ReadyNext), \
            
            ) )
        unpacker = net_resolver_pb.Unpacker
        self.recverMgr.registerCommands( (\
            unpacker(baseProto_pb2.S_C_CONNECTED, baseProto_pb2.S_C_Connected, self.onLoginSucceed), \
            unpacker(baseProto_pb2.S_C_JOIN_ROOM, baseProto_pb2.S_C_JoinRoom, self.onJoinGameResult), \
            unpacker(baseProto_pb2.S_C_DISCONNECTED, baseProto_pb2.S_C_Disconnected, self.onDisconnected), \
            unpacker(baseProto_pb2.S_C_EXIT_ROOM, baseProto_pb2.S_C_ExitRoom, self.onExitRoom), \
            unpacker(baseProto_pb2.S_C_REFRESH_ROOM_CARD, baseProto_pb2.S_C_RefreshRoomCard, self.onRefreshRoomCard), \
            unpacker(baseProto_pb2.S_C_NOTICE, baseProto_pb2.S_C_Notice, self.onNotice), \
            unpacker(baseProto_pb2.S_C_PING, baseProto_pb2.S_C_Ping, self.onPing), \
            unpacker(baseProto_pb2.S_C_TALK, baseProto_pb2.S_C_Talk, self.onTalk), \
            unpacker(baseProto_pb2.S_C_ONLINE_STATE, baseProto_pb2.S_C_OnlineState, self.onOnlineState), \
            unpacker(baseProto_pb2.S_C_GM_CONTROL, baseProto_pb2.S_C_GMControl, self.onGMControl), \
            unpacker(baseProto_pb2.S_C_DISSOLVE_VOTE, baseProto_pb2.S_C_DissolveVote, self.dissolveVote), \
            unpacker(baseProto_pb2.S_C_DISSOLVE_VOTE_RESULT, baseProto_pb2.S_C_DissolveVoteResult, self.onDissolveVoteResult), \
            unpacker(baseProto_pb2.S_C_DEBUG_PROTO, baseProto_pb2.S_C_DebugProto, self.onDebugProto), \
            unpacker(baseProto_pb2.S_C_GPS, baseProto_pb2.S_C_Gps, self.onGps), \
            unpacker(baseProto_pb2.S_C_EXIT_ROOM_RESULT, baseProto_pb2.S_C_ExitRoomResult, self.onExitRoomResult), \
            
            unpacker(poker_pb2.S_C_REFRESH_DATA, poker_pb2.S_C_RefreshData, self.onRefreshData), \
            unpacker(poker_pb2.S_C_SET_START, poker_pb2.S_C_SetStart, self.onSetStart), \
            unpacker(poker_pb2.S_C_DEAL_CARDS, poker_pb2.S_C_DealCards, self.onDealCards), 
            unpacker(poker_pb2.S_C_TURN_ACTION, poker_pb2.S_C_TurnAction, self.onTurnAction), \
            unpacker(poker_pb2.S_C_DO_ACTION_RESULT, poker_pb2.S_C_DoActionResult, self.onDoActionResult), \
            
            unpacker(poker_pb2.S_C_BALANCE, poker_pb2.S_C_Balance, self.onBalance), \
            unpacker(poker_pb2.S_C_GAME_START_RESULT, poker_pb2.S_C_GameStartResult, self.onGameStartResult), \
            
        ) )


    def onLoginSucceed(self, server, resp):
        print 'onLoginSucceed', resp

        self.side = resp.myInfo.selfInfo.side
        self.roomId = resp.myInfo.roomInfo.roomId

    def onJoinGameResult(self, server, resp):
        print 'onJoinGameResult', resp

        if resp.isFull:
            proto = poker_pb2.C_S_GameStart()
            self.sendOne(server, proto)

    def onDisconnected(self, server, resp):
        print 'onDisconnected', resp

    def onExitRoom(self, server, resp):
        print 'onExitRoom', resp

    def onRefreshData(self, server, resp):
        print 'onRefreshData', resp

    def onRefreshRoomCard(self, server, resp):
        print 'onRefreshRoomCard', resp

    def onNotice(self, server, resp):
        print 'onNotice', resp

    def onPing(self, server, resp):
        pass

    def onTalk(self, server, resp):
        print 'onTalk', resp

    def onOnlineState(self, server, resp):
        pass

    def onGMControl(self, server, resp):
        print 'onGMControl', resp

    def onSetStart(self, server, resp):
        print 'onSetStart', resp

    def onDealCards(self, server, resp):
        print 'onDealCards', resp

        cardsStr = resp.cards
        self.cards.extend(cardsStr.split(','))
        self.cards.sort()
        print self.cards

    def onTurnAction(self, server, resp):
        print 'onAllowAction', resp

        req = poker_pb2.C_S_RefreshData()
        
        self.sendOne(server, req)
        
        # req1 = poker_pb2.C_S_DoAction()
        # req1.action = 1
        # req1.num = resp.num
        # cardsStr = self.discardCards()
        # req1.datas.extend([cardsStr])
        # self.sendOne(server, req1)

    def onDoActionResult(self, server, resp):
        print 'onDoActionResult', resp

    def dissolveVote(self, server, resp):
        print 'dissolveVote', resp

        proto = poker_pb2.C_S_DissolveVote()
        proto.result = True
        self.sendOne(server, proto)

    def onDissolveVoteResult(self, server, resp):
        print 'onDissolveVoteResult', resp

    def onBalance(self, server, resp):
        print 'onBalance', resp

    def onDebugProto(self, server, resp):
        print 'onDebugProto', resp

    def onGps(self, server, resp):
        print 'onGps', resp

    def onExitRoomResult(self, server, resp):
        print 'onExitRoomResult', resp

    def onGameStartResult(self, server, resp):
        print 'onGameStartResult', resp



