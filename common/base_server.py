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
import autoCreateRoom_pb2
import clubOpenRoom_pb2
from common_db_define import *
from card_define import *
from pb_utils import *
from common.db_utils import isServiceOutDate, userDBLogin, userDBLogout
from common.protocols.poker_consts import *
from datetime import datetime
from common.logic.global_control import GlobalControl
from common.i18n.i18n import initializeGame, isValidLang, getLangInst
from peer import Peer

import baseProto_pb2
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

import trasfer_pb2

SERVICE_PROTOCOLS_INTERVAL_TICK = 1000 #刷新后台协议的轮询时间
SERVICE_STOP_SECS = 60 * 15 #还有人在服务器内等待的时间
# SERVICE_STOP_SECS = 10 #还有人在服务器内等待的时间
WAIT_END_SECS = 10 #全部玩家被T出后等待多久关闭服务器
#排行榜请求处理线程数
class BaseServer(Server):
    def __init__(self, *args, **kwargs):
        assert 'serviceTag' in kwargs
        self.serviceTag = kwargs['serviceTag']
        del kwargs['serviceTag']
        super(BaseServer, self).__init__(*args, **kwargs)
        self.ip = self.serviceTag.split(':')[1]
        self.port = self.serviceTag.split(':')[2]

    def clubOpenRoom(self, player, resp):
        """ 自动创建房间

        :param player:
        :param resp:
        :return:
        """
        auto_id = resp.id
        rule = resp.rule
        timestamp = resp.timestamp
        account = resp.account
        ag = resp.ag
        ruleText = resp.ruleText
        club_number = resp.clubNumber
        room_id = resp.roomId

        redis = self.getPublicRedis()
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        table = redis.get(account2user_table)
        ownnerNickname = redis.hget(table, 'nickname')
        uid = table.split(':')[-1]
        params = eval(rule)
        isHidden = int(params[-1])
        del params[-1]
        rule = str(params)
        needRoomCards = int(params[-2])
        times = self.getTimestamp()
        roomCards = redis.incrby(USER4AGENT_CARD%(ag, uid), -needRoomCards)
        if roomCards < 0:
            roomCards = redis.incrby(USER4AGENT_CARD%(ag, uid), needRoomCards)
            log('[on create game for other][error]roomCards[%s] is not enough[%s]'%(roomCards, needRoomCards), LOG_LEVEL_RELEASE)
            return

        _game = self.getGameModule(self, rule)
        addResult = self.globalCtrl.addClubGame(_game, self.ID, room_id)

        if not addResult:
            log(u'[try create auto game for other][error]no rooms!!!.', LOG_LEVEL_RELEASE)
            return

        ymd = datetime.now().strftime("%Y-%m-%d")
        useDatas = [-needRoomCards, 2, roomCards, _game.roomId]
        useStr = ';'.join(map(str, useDatas))
        pipe = redis.pipeline()
        pipe.lpush(PLAYER_DAY_USE_CARD % (uid, ymd), useStr)
        pipe.expire(PLAYER_DAY_USE_CARD % (uid, ymd), SAVE_PLAYER_DAY_USE_CARD_TIME)

        roomDataKey = OTHER_ROOM_DATA%(account, times, _game.roomId)
        _game.ownner = account
        _game.parentAg = ag
        _game.otherRoomTable = roomDataKey
        if isHidden:
            _game.isHidden = True
        # pipe = redis.pipeline()
        pipe.hmset(ROOM2SERVER%(_game.roomId),
            {
                'ip'         :       self.ip,
                'port'       :       self.port,
                'ag'         :       ag,
                'gameid'     :       self.ID,
                'hidden'     :       isHidden,
                'dealer'     :       ownnerNickname,
                'playerCount':       0,
                'maxPlayer'  :       _game.maxPlayerCount,
                'gameName'   :       _game.roomName,
                'baseScore'  :       eval(rule)[-1],
                'ruleText'   :       _game.ruleDescs,
                "auto_id"    :       auto_id,
                "club_number":       club_number
            }
        )
        pipe.sadd(AG2SERVER%("%s-%s" % (ag, club_number)), _game.roomId)
        pipe.sadd(SERVER2ROOM%(self.serviceTag), _game.roomId)
        pipe.hincrby(self.table, 'roomCount', 1)
        pipe.hmset(roomDataKey,
            {
                'roomId'        :     _game.roomId,
                'name'          :     _game.roomName,
                'gameType'      :     0,
                'minNum'        :     0,
                'maxNum'        :     _game.maxPlayerCount,
                'time'          :     times,
                'rule'          :     _game.ruleDescs,
                'roomType'      :     isHidden,
                'gameid'        :     self.ID,
                "auto_id"       :     auto_id,
                "club_number"   :     club_number
            }
        )
        # pipe.expire(roomDataKey, 1 * 24 * 60 * 60)
        pipe.lpush(MY_OTHER_ROOMS%(account), roomDataKey)
        pipe.execute()
        log(u'[try auto create game for other]create game succeed, account[%s] room[%s].'%(account, _game.roomId), LOG_LEVEL_RELEASE)


    def startFactory(self):
        """
        启动完成才初始化数据
        """
        self.account2players = {}
        self.account2Sid = {}
        self.trialAccountPool = []
        self.trialAccountSet = []
        self.loginLocks = {}

        self.accountValidator = re.compile(r'^[a-zA-Z]\w{3,17}$')
        self.passwdValidator = re.compile(r'^.{8,20}$')

        redis = self.getPublicRedis()
        while 1:
            try:
                redis.get(FORMAT_IP2CONTRYCODE)
            except RedisError, e:
                log('Wait for redis error[%s]'%(e))
                time.sleep(5)
            else:
                break

        #需要初始化代理和房间号池
        hasRoom = redis.scard(GAME_ROOM_SET)
        # hasAgent = redis.hexists(FORMAT_ADMIN_ACCOUNT_TABLE%('CHNWX'), 'name')
        if not hasRoom:
            log('need init: room[%s]:[%s]'%('setRoomSet.py', hasRoom), LOG_LEVEL_RELEASE)
            e = None
            assert e

        #load game config
        self.globalCtrl = GlobalControl()

        #关闭服务时间戳,时间戳为非0则不允许玩家连入游戏了
        #关闭阶段1:倒计时10秒断开所有玩家连接
        #关闭阶段2:30秒后关闭服务
        self.gameCloseTimestamp = 0
        self.isClosed = False
        self.isWaitEnd = False
        self.isEnding = False

        #读取服务信息时间戳
        self.lastResovledServiceProtocolsTimestamp = 0
        self.resovledServiceProtocolsLock = False

        #货币及相关代理彩池刷新
        self.currency, _, _ = self.serviceTag.split(':')
        self.currencyAgentCashRefreshTimestamp = 0

        initializeGame()
        self.ID = self.getGameID()

        self.table = FORMAT_GAME_SERVICE_TABLE%(self.ID, self.serviceTag)
        self.serviceProtocolTable = FORMAT_SERVICE_PROTOCOL_TABLE%(self.ID, self.serviceTag)
        pipe = redis.pipeline()
        pipe.hset(self.table, 'playerCount', 0)
        pipe.hset(self.table, 'roomCount', 0)
        pipe.delete(SERVER2ROOM%self.serviceTag)
        pipe.rpush(FORMAT_GAME_SERVICE_SET%(self.ID), self.table)

        #清空原服务器下的所有断线重连信息
        serverExitPlayer = SERVER_EXIT_PLAYER%(self.serviceTag, self.ID)
        # if redis.exists(serverExitPlayer):
            # exitPlayerList = redis.smembers(serverExitPlayer)
            # for exitPlayer in exitPlayerList:
                # if redis.exists(EXIT_PLAYER%(exitPlayer)):
                    # pipe.delete(EXIT_PLAYER%(exitPlayer))
        pipe.delete(serverExitPlayer)
        pipe.execute()

    def getGameModule(self, *initData):
        raise 'abstract interface'

    def getGameID(self):
        raise 'abstract interface'

    def isValidPacket(self, msgName):
        return True

    def autoCreateRoom(self, player, resp):
        """ 自动创建房间

        :param player:
        :param resp:
        :return:
        """
        auto_id = resp.id
        rule = resp.rule
        timestamp = resp.timestamp
        account = resp.account
        ag = resp.ag
        ruleText = resp.ruleText
        club_number = resp.clubNumber
        redis = self.getPublicRedis()

        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        table = redis.get(account2user_table)
        ownnerNickname = redis.hget(table, 'nickname')
        uid = table.split(':')[-1]
        params = eval(rule)
        isHidden = int(params[-1])
        del params[-1]
        rule = str(params)
        needRoomCards = int(params[-2])
        times = self.getTimestamp()
        roomCards = redis.incrby(USER4AGENT_CARD%(ag, uid), -needRoomCards)
        if roomCards < 0:
            roomCards = redis.incrby(USER4AGENT_CARD%(ag, uid), needRoomCards)
            log('[on create game for other][error]roomCards[%s] is not enough[%s]'%(roomCards, needRoomCards), LOG_LEVEL_RELEASE)
            return

        _game = self.getGameModule(self, rule)
        addResult = self.globalCtrl.addGame(_game, self.ID)

        if not addResult:
            log(u'[try create auto game for other][error]no rooms!!!.', LOG_LEVEL_RELEASE)
            return
        ymd = datetime.now().strftime("%Y-%m-%d")
        useDatas = [-needRoomCards, 2, roomCards, _game.roomId]
        useStr = ';'.join(map(str, useDatas))
        pipe = redis.pipeline()
        pipe.lpush(PLAYER_DAY_USE_CARD % (uid, ymd), useStr)
        pipe.expire(PLAYER_DAY_USE_CARD % (uid, ymd), SAVE_PLAYER_DAY_USE_CARD_TIME)

        roomDataKey = OTHER_ROOM_DATA%(account, times, _game.roomId)
        _game.ownner = account
        _game.parentAg = ag
        _game.otherRoomTable = roomDataKey
        if isHidden:
            _game.isHidden = True
        # pipe = redis.pipeline()
        pipe.hmset(ROOM2SERVER%(_game.roomId),
            {
                'ip'         :       self.ip,
                'port'       :       self.port,
                'ag'         :       ag,
                'gameid'     :       self.ID,
                'hidden'     :       isHidden,
                'dealer'     :       ownnerNickname,
                'playerCount':       0,
                'maxPlayer'  :       _game.maxPlayerCount,
                'gameName'   :       _game.roomName,
                'baseScore'  :       eval(rule)[-1],
                'ruleText'   :       _game.ruleDescs,
                "auto_id"    :       auto_id,
                "club_number":       club_number
            }
        )
        pipe.sadd(AG2SERVER%("%s-%s" % (ag, club_number)), _game.roomId)
        pipe.sadd(SERVER2ROOM%(self.serviceTag), _game.roomId)
        pipe.hincrby(self.table, 'roomCount', 1)
        pipe.hmset(roomDataKey,
            {
                'roomId'        :     _game.roomId,
                'name'          :     _game.roomName,
                'gameType'      :     0,
                'minNum'        :     0,
                'maxNum'        :     _game.maxPlayerCount,
                'time'          :     times,
                'rule'          :     _game.ruleDescs,
                'roomType'      :     isHidden,
                'gameid'        :     self.ID,
                "club_number"   :     club_number
            }
        )
        # pipe.expire(roomDataKey, 1 * 24 * 60 * 60)
        pipe.lpush(MY_OTHER_ROOMS%(account), roomDataKey)
        pipe.execute()
        log(u'[try auto create game for other]create game succeed, account[%s] room[%s].'%(account, _game.roomId), LOG_LEVEL_RELEASE)



    def registerProtocolResolver(self):
        unpacker = net_resolver_pb.Unpacker
        self.recverMgr.registerCommands( (\
            unpacker(baseProto_pb2.C_S_CONNECTING, baseProto_pb2.C_S_Connecting, self.onReg), \
            unpacker(baseProto_pb2.C_S_DEBUG_CONNECTING, baseProto_pb2.C_S_DebugConnecting, self.onDebugReg), \
            unpacker(baseProto_pb2.C_S_EXIT_ROOM, baseProto_pb2.C_S_ExitRoom, self.onExitGame), \
            unpacker(baseProto_pb2.C_S_PING, baseProto_pb2.C_S_Ping, self.onPing), \
            unpacker(baseProto_pb2.C_S_TALK, baseProto_pb2.C_S_Talk, self.onTalk), \
            unpacker(baseProto_pb2.C_S_GM_CONTROL, baseProto_pb2.C_S_GMControl, self.onGMControl), \
            unpacker(baseProto_pb2.C_S_DISSOLVE_ROOM, baseProto_pb2.C_S_DissolveRoom, self.onDissolveRoom), \
            unpacker(baseProto_pb2.C_S_DISSOLVE_VOTE, baseProto_pb2.C_S_DissolveVote, self.onDissolveVote), \
            unpacker(baseProto_pb2.C_S_DEBUG_PROTO, baseProto_pb2.C_S_DebugProto, self.onDebugProto), \
            unpacker(baseProto_pb2.C_S_GPS, baseProto_pb2.C_S_Gps, self.onSetGps), \
            unpacker(autoCreateRoom_pb2.S_S_AUTOCREATEROOM, autoCreateRoom_pb2.S_S_AutoCreateRoom, self.autoCreateRoom), 
            unpacker(clubOpenRoom_pb2.S_S_CLUBOPENROOM, clubOpenRoom_pb2.S_S_ClubOpenRoom, self.clubOpenRoom),
            ) )
        packer = net_resolver_pb.Packer
        self.senderMgr.registerCommands( (\
            packer(baseProto_pb2.S_C_CONNECTED, baseProto_pb2.S_C_Connected), \
            packer(baseProto_pb2.S_C_JOIN_ROOM, baseProto_pb2.S_C_JoinRoom), \
            packer(baseProto_pb2.S_C_DISCONNECTED, baseProto_pb2.S_C_Disconnected), \
            packer(baseProto_pb2.S_C_EXIT_ROOM, baseProto_pb2.S_C_ExitRoom), \
            packer(baseProto_pb2.S_C_REFRESH_ROOM_CARD, baseProto_pb2.S_C_RefreshRoomCard), \
            packer(baseProto_pb2.S_C_NOTICE, baseProto_pb2.S_C_Notice), \
            packer(baseProto_pb2.S_C_PING, baseProto_pb2.S_C_Ping), \
            packer(baseProto_pb2.S_C_TALK, baseProto_pb2.S_C_Talk), \
            packer(baseProto_pb2.S_C_ONLINE_STATE, baseProto_pb2.S_C_OnlineState), \
            packer(baseProto_pb2.S_C_GM_CONTROL, baseProto_pb2.S_C_GMControl), \
            packer(baseProto_pb2.S_C_DISSOLVE_VOTE, baseProto_pb2.S_C_DissolveVote), \
            packer(baseProto_pb2.S_C_DISSOLVE_VOTE_RESULT, baseProto_pb2.S_C_DissolveVoteResult), \
            packer(baseProto_pb2.S_C_DEBUG_PROTO, baseProto_pb2.S_C_DebugProto), \
            packer(baseProto_pb2.S_C_GPS, baseProto_pb2.S_C_Gps), \
            packer(baseProto_pb2.S_C_EXIT_ROOM_RESULT, baseProto_pb2.S_C_ExitRoomResult), \
            packer(trasfer_pb2.S_S_MYSQL_COMMANDS_DATA, trasfer_pb2.S_S_MysqlCommandsData), \
            ) )
        self.registerServiceProtocols()

    def registerServiceProtocols(self):
        self.serviceProtoCalls = {
            HEAD_SERVICE_PROTOCOL_GAME_CLOSE.split('|')[0]              :       self.onServiceGameClose,
            HEAD_SERVICE_PROTOCOL_MEMBER_REFRESH.split('|')[0]          :       self.onServiceMemberRefresh,
            HEAD_SERVICE_PROTOCOL_AGENT_BROADCAST.split('|')[0]         :       self.onServiceAgentBroadcast,
            HEAD_SERVICE_PROTOCOL_OPERATOR_RESESSION.split('|')[0]      :       self.onServiceReSession,
            HEAD_SERVICE_PROTOCOL_KICK_MEMBER.split('|')[0]             :       self.onServiceKickMember,
            HEAD_SERVICE_PROTOCOL_JOIN_PARTY_ROOM.split('|')[0]         :       self.onJoinPartyRoom,
            HEAD_SERVICE_PROTOCOL_DISSOLVE_ROOM.split('|')[0]           :       self.onDissolvePlayerRoom,
            HEAD_SERVICE_PROTOCOL_CREATE_OTHER_ROOM.split('|')[0]       :       self.onCreateGame4Other,
        }

    def onReg(self, player, req):
        session = req.sid
        log(u'[try reg] sid[%s].'%(req.sid), LOG_LEVEL_RELEASE)

        player.lang = getLangInst()
        respFailed = baseProto_pb2.S_C_Connected()
        respFailed.result = False

        redis = self.getPublicRedis()
        #关闭服务器中
        # if self.gameCloseTimestamp:
            # log(u'[try reg][error]closing server now.', LOG_LEVEL_RELEASE)
            # respFailed.reason = player.lang.MAINTAIN_TIPS
            # self.sendOne(player, respFailed)
            # errMsg = '服务器维护中'.decode('utf-8')
            # player.drop(errMsg)
            # return

        #是否存在转登录cache
        cacheTable = None
        cache = player.hashKey

        if cache in self.loginLocks:
            log(u'[try reg][error][%s] tryReg lock.'%(cache), LOG_LEVEL_RELEASE)
            return
        self.loginLocks[cache] = True

        #cache md5
        cacheTable = FORMAT_USER_HALL_SESSION%(req.sid)
        account, player.operatorSessionId, ip = redis.hmget(cacheTable, ('account', 'sid', 'loginIp'))
        if not account:
            # respFailed.reason = player.lang.LOGIN_TIPS_TIMEOUT
            # self.sendOne(player, respFailed)
            del self.loginLocks[cache]
            player.account = ""
            errorStr = "登录超时.".decode('utf-8')
            player.drop(errorStr, type = 1)
            return
        else:
            player.ip = ip
            player.descTxt = '%s:%s:%s'%(player.protoTag, player.ip, player.port)
            player.cacheTable = cacheTable

        #已登录或注册
        if player.account:
            log(u'[try reg][error]account[%s][%s] is already registered or logon.'%(player.account, account), LOG_LEVEL_RELEASE)
            respFailed.reason = player.lang.REG_TIPS_ALREADY_LOGON
            self.sendOne(player, respFailed)
            del self.loginLocks[cache]
            player.drop("Already logon.", consts.DROP_REASON_INVALID, type = 1)
            return

        if not account:
            log(u"[try reg][error]request account is empty.", LOG_LEVEL_RELEASE)
            respFailed.reason = player.lang.REG_TIPS_EMPTY_ACCOUNT_PASSWD
            self.sendOne(player, respFailed)
            del self.loginLocks[cache]
            player.drop("Empty account.", consts.DROP_REASON_INVALID)
            return

        #验证合法性
#        if not self.accountValidator.match(req.account):
#            log(u"[try reg][error]account invalid.")
#            if req.isLogin:
#                respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT_PASSWD
#            else:
#                respFailed.reason = player.lang.REG_TIPS_INVALID_ACCOUNT
#            self.sendOne(player, respFailed)
#            del self.loginLocks[cache]
#            return
#
#        if not self.passwdValidator.match(req.passwd):
#            log(u"[try reg][error]passwd invalid.")
#            if req.isLogin:
#                respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT_PASSWD
#            else:
#                respFailed.reason = player.lang.REG_TIPS_INVALID_PASSWD
#            self.sendOne(player, respFailed)
#            del self.loginLocks[cache]
#            return

        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        table = redis.get(account2user_table)

        #已存在用户
        if table:
            player.loadDB(table, account = account)
            if player.valid != '1':
                log(u"[try login][error]account[%s] invalid."%(account), LOG_LEVEL_RELEASE)
                respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT
                self.sendOne(player, respFailed)
                del self.loginLocks[cache]
                player.account = ""
                player.drop("Already freezen.", consts.DROP_REASON_INVALID)
                return

            if not cacheTable:
                log(u"[try reg][error]request passwd is empty.", LOG_LEVEL_RELEASE)
                respFailed.reason = player.lang.REG_TIPS_EMPTY_ACCOUNT_PASSWD
                self.sendOne(player, respFailed)
                del self.loginLocks[cache]
                player.account = ""
                player.drop("Password empty.", consts.DROP_REASON_INVALID)
                return

            if cacheTable:
                log(u'[try login for operator]operator[%s] cacheTable[%s] account[%s] sessionId[%s] ip[%s]'%\
                    (player.parentAg, cacheTable, player.account, player.operatorSessionId, ip), LOG_LEVEL_RELEASE)

            #账号已在线
            if account not in self.account2players and redis.sismember(ONLINE_ACCOUNTS_TABLE, account):
                serviceTag = redis.hget(FORMAT_CUR_USER_GAME_ONLINE%(account), 'serviceTag')
                serverIp = serviceTag.split(':')[1]
                serverPort = serviceTag.split(':')[2]
                if serverIp == self.ip and serverPort == self.port:
                    redis.srem(ONLINE_ACCOUNTS_TABLE, account)
                else:
                    date,gameTag = redis.hmget(FORMAT_CUR_USER_GAME_ONLINE % (account), 'date','game')                    
                    if not gameTag:
                        if self.ifMoreThanOneHour(date):
                        #redis.srem(ONLINE_ACCOUNTS_TABLE, account)                        
                            redis.delete(FORMAT_CUR_USER_GAME_ONLINE % (account))
                    log(u"[try login][error]account[%s] is in another server."%(account), LOG_LEVEL_RELEASE)
                    player.account = ''
                    player.drop("Kick for repeated login.", consts.DROP_REASON_REPEAT_LOGIN)
                    del self.loginLocks[cache]
                    return
            if account in self.account2players:# or (redis.hget(table, 'online') == "1"):
                another = self.account2players[account]
                self.onExit(another)
                if account in self.account2Sid and session == self.account2Sid[account]:
                    another.drop("Kick for repeated login.", consts.DROP_REASON_REPEAT_LOGIN, type = 4)
                else:
                    another.drop("Kick for repeated login.", consts.DROP_REASON_REPEAT_LOGIN)
                player.loadDB(table, isInit=False)

#                log(u'[try login][error]account[%s] is already logon.'%(account))
#                respFailed.reason = player.lang.LOGIN_TIPS_ALREADY_LOGON
#                self.sendOne(player, respFailed)
#                del self.loginLocks[cache]
#                player.drop("Already online.", consts.DROP_REASON_INVALID)
#                return

            self.onTryRegSucceed(player, cache, False, session, '', -1)
        else:
            log(u"[try login][error]account[%s] is not existed."%(account), LOG_LEVEL_RELEASE)
            respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT_PASSWD
            self.sendOne(player, respFailed)
            del self.loginLocks[cache]
            player.drop("Account is not exist.", consts.DROP_REASON_INVALID)
            return

    def onDebugReg(self, player, req):
        session = ''
        log(u'[try debug reg]account[%s] passwd[%s] mode[%s] action[%s] rule[%s] roomId[%s].'%\
                (req.account, req.passwd, req.mode, req.roomSetting.action, req.roomSetting.rule, req.roomSetting.roomid), LOG_LEVEL_RELEASE)

        if req.roomSetting.rule:
            rule = eval(req.roomSetting.rule)
            del rule[0]
            req.roomSetting.rule = str(rule)
        player.lang = getLangInst()
        respFailed = baseProto_pb2.S_C_Connected()
        respFailed.result = False

        redis = self.getPublicRedis()
        #关闭服务器中
        # if self.gameCloseTimestamp:
            # log(u'[try reg][error]closing server now.', LOG_LEVEL_RELEASE)
            # respFailed.reason = player.lang.MAINTAIN_TIPS
            # self.sendOne(player, respFailed)
            # player.drop("closing server now.", consts.DROP_REASON_INVALID)
            # return

        #是否存在转登录cache
        cacheTable = None
        cache = player.hashKey

        if cache in self.loginLocks:
            log(u'[try reg][error][%s] tryReg lock.'%(cache), LOG_LEVEL_RELEASE)
            return
        self.loginLocks[cache] = True

        #cache md5
        ip = player.descTxt.split(':')[1]
        account = req.account

        #已登录或注册
        if player.account:
            log(u'[try reg][error]account[%s][%s] is already registered or logon.'%(player.account, account), LOG_LEVEL_RELEASE)
            respFailed.reason = player.lang.REG_TIPS_ALREADY_LOGON
            self.sendOne(player, respFailed)
            del self.loginLocks[cache]
            player.drop("Already logon.", consts.DROP_REASON_INVALID, type = 1)
            return

        if not account:
            log(u"[try reg][error]request account is empty.", LOG_LEVEL_RELEASE)
            respFailed.reason = player.lang.REG_TIPS_EMPTY_ACCOUNT_PASSWD
            self.sendOne(player, respFailed)
            del self.loginLocks[cache]
            player.drop("Empty account.", consts.DROP_REASON_INVALID)
            return

        #验证合法性
#        if not self.accountValidator.match(req.account):
#            log(u"[try reg][error]account invalid.")
#            if req.isLogin:
#                respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT_PASSWD
#            else:
#                respFailed.reason = player.lang.REG_TIPS_INVALID_ACCOUNT
#            self.sendOne(player, respFailed)
#            del self.loginLocks[cache]
#            return
#
#        if not self.passwdValidator.match(req.passwd):
#            log(u"[try reg][error]passwd invalid.")
#            if req.isLogin:
#                respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT_PASSWD
#            else:
#                respFailed.reason = player.lang.REG_TIPS_INVALID_PASSWD
#            self.sendOne(player, respFailed)
#            del self.loginLocks[cache]
#            return

        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        table = redis.get(account2user_table)

        #已存在用户
        if table:
            player.loadDB(table, account = account)
            if player.valid != '1':
                log(u"[try login][error]account[%s] invalid."%(account), LOG_LEVEL_RELEASE)
                respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT
                self.sendOne(player, respFailed)
                del self.loginLocks[cache]
                player.account = ""
                player.drop("Already freezen.", consts.DROP_REASON_INVALID)
                return

            if not req.passwd:
                log(u"[try reg][error]request passwd is empty.", LOG_LEVEL_RELEASE)
                respFailed.reason = player.lang.REG_TIPS_EMPTY_ACCOUNT_PASSWD
                self.sendOne(player, respFailed)
                del self.loginLocks[cache]
                player.account = ""
                player.drop("Password empty.", consts.DROP_REASON_INVALID)
                return

            if player.passwd and player.passwd != md5.new(req.passwd).hexdigest():
                log(u"[try login][error]account[%s] password[%s]-[%s] invalid."%(req.account, player.passwd, req.passwd), LOG_LEVEL_RELEASE)
                respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT_PASSWD
                self.sendOne(player, respFailed)
                del self.loginLocks[cache]
                player.account = ""
                player.drop("Password is not match.", consts.DROP_REASON_INVALID)
                return

            #账号已在线
            if account not in self.account2players and redis.sismember(ONLINE_ACCOUNTS_TABLE, account):
                serviceTag = redis.hget(FORMAT_CUR_USER_GAME_ONLINE%(account), 'serviceTag')
                serverIp = serviceTag.split(':')[1]
                serverPort = serviceTag.split(':')[2]
                if serverIp == self.ip and serverPort == self.port:
                    redis.srem(ONLINE_ACCOUNTS_TABLE, account)
                else:
                    log(u"[try login][error]account[%s] is in another server."%(account), LOG_LEVEL_RELEASE)
                    player.account = ''
                    player.drop("Kick for repeated login.", consts.DROP_REASON_REPEAT_LOGIN)
                    del self.loginLocks[cache]
                    return
            if account in self.account2players:# or (redis.hget(table, 'online') == "1"):
                another = self.account2players[account]
                self.onExit(another)
                another.drop("Kick for repeated login.", consts.DROP_REASON_REPEAT_LOGIN)
                player.loadDB(table, isInit=False)

#                log(u'[try login][error]account[%s] is already logon.'%(account))
#                respFailed.reason = player.lang.LOGIN_TIPS_ALREADY_LOGON
#                self.sendOne(player, respFailed)
#                del self.loginLocks[cache]
#                player.drop("Already online.", consts.DROP_REASON_INVALID)
#                return

            self.onTryRegSucceed(player, cache, False, session, req.roomSetting, req.mode)
        else:
            log(u"[try login][error]account[%s] is not existed."%(account), LOG_LEVEL_RELEASE)
            respFailed.reason = player.lang.LOGIN_TIPS_INVALID_ACCOUNT_PASSWD
            self.sendOne(player, respFailed)
            del self.loginLocks[cache]
            player.drop("Account is not exist.", consts.DROP_REASON_INVALID)
            return

    def onRefreshRoomCards(self, player, req):
        if player.account not in self.account2players:
            return
        player.loadDB(player.table, isInit=False)
        walletProto = baseProto_pb2.S_C_WalletMoney()
        walletProto.roomCards = player.roomCards
        self.sendOne(player, walletProto)

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

    def sendOthersOnlineState(self, player):
        resp = baseProto_pb2.S_C_OnlineState()
        for _player in player.game.getPlayers((player,)):
            if not _player:
                continue
            resp.changeSide = _player.chair
            resp.isOnline = _player.isOnline
            self.sendOne(player, resp)
        
    def tryRoomAction(self, player, resp, session, roomSetting = '', mode = -1, isSendMsg = True):
        if mode == 1: #一控四
            self.tryRoomAction4allPlayer(player, resp, roomSetting.rule, mode)
            return
        isDebug = False
        redis = redis_instance.getInst(PUBLIC_DB)
        SessionTable = FORMAT_USER_HALL_SESSION%(session)
        if redis.exists(SessionTable):
            self.account2Sid[player.account] = session
            account, action, roomid, rule = redis.hmget(SessionTable, 'account', 'action', 'roomid', 'rule')
            redis.hdel(SessionTable, 'action')
        if roomSetting:
            isDebug = True
            action = roomSetting.action
            roomid = roomSetting.roomid
            rule = roomSetting.rule
            if action == 1:
                params = eval(rule)
                needRoomCards = int(params[-2])
                for data in redis.lrange(USE_ROOM_CARDS_RULE%(self.ID), 0, -1):
                    datas = data.split(':')
                    name, cards = datas[0], datas[1]
                    try:
                        playCount = int(datas[2])
                    except:
                        playCount = 0
                    if int(cards) == needRoomCards:
                        break
                params.insert(-2, playCount)
                rule = str(params)
        try:
            action = int(action)
        except:
            action = -1
        log(u'[try reg action]action[%s] roomid[%s] rule[%s].'%(action, roomid, rule), LOG_LEVEL_RELEASE)

        #娱乐模式加入
        if mode == -3:
            self.onJoinGame(player, resp, roomid, isSendMsg = False)
        #加入
        elif action == 0:
            self.onJoinGame(player, resp, roomid, isSendMsg = isSendMsg)
        #创建
        elif action == 1:
            log(u'[try createGame] player[%s] resp[%s] rule[%s] isDebug[%s]'%(player.nickname,resp,rule,isDebug))
            self.onCreateGame(player, resp, rule, isDebug)
        elif action == -1:
            messsageStr = '房间不存在或已解散'.decode('utf-8')
            player.drop(messsageStr, type = 2)


    def tryRoomAction4allPlayer(self, player, resp, rule, mode):
        '''
        一控四
        '''
        #test
        rule = '[8]'
        self.createGame(player, resp, rule, isSendMsg = False)

        self.tryConnectingRobot(player.game, player)
        player.isControlByOne = True

    def tryConnectingRobot(self, game, player):
        game.controlPlayerSide = player.chair
        otherPlayerResp = baseProto_pb2.C_S_DebugConnecting()
        otherPlayerResp.roomSetting.action = 0
        otherPlayerResp.mode = 0
        otherPlayerResp.roomSetting.roomid = game.roomId
        redis = self.getPublicRedis()
        for i in xrange(game.maxPlayerCount - 1):
            otherPlayer = game.getRobot()
            account = player.account[:-1] + str(int(player.account[-1]) + i + 1)
            account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
            table = redis.get(account2user_table)
            otherPlayer.loadDB(table)
            otherPlayer.controlPlayer = player
            otherPlayer.ip = ''
            otherPlayer.lang = getLangInst()
            otherPlayer.factory = self
            otherPlayer.hashKey = 'debug'
            if i != game.maxPlayerCount - 2:
                self.onTryRegSucceed(otherPlayer, '', False, '', otherPlayerResp.roomSetting, otherPlayerResp.mode, isSendMsg = False)
            else:
                self.onTryRegSucceed(otherPlayer, '', False, '', otherPlayerResp.roomSetting, otherPlayerResp.mode)
            otherPlayer.isControlByOne = True

    def onCreateGame(self, player, resp, roomSetting, isDebug = False):
        if player.endType == 'waitEndSucceed':
            player.drop("close game server", consts.DROP_REASON_CLOSE_SERVER, type = 2)
            return
        elif player.endType == 'waitEnd':
            self.onExit(player)
            player.drop("close game server", consts.DROP_REASON_CLOSE_SERVER, type = 2)
            return

        if player.game:
            log(u'[try create game][error]nickname[%s] already in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        log(u'[try create game]nickname[%s].'%(player.nickname), LOG_LEVEL_RELEASE)

        redis = self.getPublicRedis()
        if player.roomCards <= 0 and not isDebug:
            log(u'[try create game][error]nickname[%s] has no roomCard.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        createGameParams = (player, resp, roomSetting)
        reactor.callFromThread(self.createGame, *createGameParams)

    def createGame(self, player, resp, roomSetting = '[1]', isSendMsg = True):
        _game = self.getGameModule(self, roomSetting)
        redis = self.getPublicRedis()
        isHidden = redis.hget(player.cacheTable, 'hidden')
        try:
            if int(isHidden):
                _game.isHidden = True
        except:
            pass
        addResult = self.globalCtrl.addGame(_game, self.ID)

        if not addResult:
            log(u'[try create game][error]no rooms!!!.', LOG_LEVEL_RELEASE)
            errorMessage = '房间已满'.decode(LANG_CODE)
            resp.result = False
            resp.myInfo.result = False
            resp.myInfo.reason = errorMessage
            resp.reason = errorMessage
            self.sendOne(player, resp)
            return

        redis.hmset(ROOM2SERVER%(_game.roomId),
            {
                'ip'         :       self.ip,
                'port'       :       self.port,
                'ag'         :       player.parentAg,
                'gameid'     :       self.ID,
                'hidden'     :       redis.hget(player.cacheTable, 'hidden'),
                'dealer'     :       player.nickname,
                'playerCount':       0,
                'maxPlayer'  :       _game.maxPlayerCount,
                'gameName'   :       _game.roomName,
                'baseScore'  :       eval(roomSetting)[-1],
                'ruleText'   :       _game.ruleDescs,
            }
        )
        redis.sadd(AG2SERVER%(player.parentAg), _game.roomId)
        redis.sadd(SERVER2ROOM%(self.serviceTag), _game.roomId)
        redis.hincrby(self.table, 'roomCount', 1)
        _game.onJoinGame(player, resp, isSendMsg)

        log(u'[try create game]create game succeed, nickname[%s] room[%s].'%(player.nickname, _game.roomId), LOG_LEVEL_RELEASE)

    def onJoinGame(self, player, resp, roomId, isSendMsg = True):
        if player.endType == 'waitEndSucceed':
            player.drop("close game server", consts.DROP_REASON_CLOSE_SERVER, type = 2)
            return
        elif player.endType == 'waitEnd':
            self.onExit(player)
            player.drop("close game server", consts.DROP_REASON_CLOSE_SERVER, type = 2)
            return

        log(u'[try join game]nickname[%s] room[%s].'%(player.nickname, roomId), LOG_LEVEL_RELEASE)
        errorMessage = {
            'notFound':'房间不存在或已解散'.decode(LANG_CODE),
            'passwdError':'密码错误'.decode(LANG_CODE),
            'isFull':'房间已满'.decode(LANG_CODE),
            'notInto': "有相同IP不能加入".decode(LANG_CODE),
            'notIntoOther': "房间有不能与你同台的玩家,请阁下更换其它房间".decode(LANG_CODE),
        }
        roomId = roomId.upper() 
        if roomId not in self.globalCtrl.num2game:
            log(u'[try join game][error]room[%s] is not found, game set[%s].'%(roomId, self.globalCtrl.num2game), LOG_LEVEL_RELEASE)
            if isSendMsg:
                resp.result = False
                resp.myInfo.result = False
                resp.myInfo.reason = errorMessage['notFound']
                resp.reason = errorMessage['notFound']
                self.sendOne(player, resp)
            return

        game = self.globalCtrl.num2game[roomId]

        if game.allowSameIpNotInto:
            ipList = set()
            for _player in game.players:
                if not _player:
                    continue

                if _player.account != player.account:
                    ipList.add(_player.ip)
            if player.ip in ipList:
                resp.result = False
                resp.myInfo.result = False
                resp.myInfo.reason = errorMessage['notInto']
                resp.reason = errorMessage['notInto']
                self.sendOne(player, resp)
                return

        # 禁止进入的规则
        redis = self.getPublicRedis()
        club_number = redis.hget(ROOM2SERVER%(roomId), "club_number")
        if club_number:
            signTable = "club:userbanList:%s:hset" % club_number
            curUserBanList = redis.hget(signTable, player.uid)
            if not curUserBanList:
                curUserBanList = set()
            else:
                curUserBanList = eval(curUserBanList)
            _sign = 0
            for _player in game.players:
                if not _player:
                    continue
                if _player.uid in curUserBanList:
                    _sign = 1
                    break
                banList = redis.hget(signTable, _player.uid)
                if not banList:
                    banList = set()
                else:
                    banList = eval(banList)
                if player.uid in banList:
                    _sign = 1
                    break

            if _sign:
                resp.result = False
                resp.myInfo.result = False
                resp.myInfo.reason = errorMessage['notIntoOther']
                resp.reason = errorMessage['notIntoOther']
                self.sendOne(player, resp)
                return


        if game.getEmptyChair() == consts.SIDE_UNKNOWN:
            log(u'[try join game][error]room[%s] is full.'%(roomId), LOG_LEVEL_RELEASE)
            if isSendMsg:
                resp.result = False
                resp.myInfo.result = False
                resp.myInfo.reason = errorMessage['isFull']
                resp.reason = errorMessage['isFull']
                self.sendOne(player, resp)
            return

        result = self.dynamic.joinRoom(game, self, player, resp)
        if not result:
            return
        self.tryJoinGame(player, resp, game, isSendMsg)

        self.tryJoinGame(player, resp, game, isSendMsg)

    def tryJoinGame(self, player, resp, game, isSendMsg):
        if player.game:
            log(u'[try join game][error]nickname[%s] already in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        game.onJoinGame(player, resp, isSendMsg)

    def onPing(self, player, game):
        player.isOnline = True
        player.lastPingTimestamp = self.getTimestamp()
        resp = baseProto_pb2.S_C_Ping()
        self.sendOne(player, resp)
        player.OnRefresh()
        log(u'[onPing]nickname[%s] isOnline[%s] lastOnlineState[%s]'%(player.nickname,player.isOnline,player.lastOnlineState), LOG_LEVEL_RELEASE)

    def onExitGame(self, player, req = None, sendMessage = True):
        if not player.game:
            log(u'[try exit game][error]nickname[%s] is not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        byPlayer = False
        if req != None:
            log(u'[try exit game]exit by player.', LOG_LEVEL_RELEASE)
            byPlayer = True

        log(u'[try exit game]nickname[%s] room[%s].'%(player.nickname, player.game.roomId), LOG_LEVEL_RELEASE)
        if not byPlayer or player.game.stage == WAIT_START:
            player.game.onExitGame(player, sendMessage, byPlayer)
        else:
            log(u'[try exit game][error]room[%s] is start.'%(player.game.roomId), LOG_LEVEL_RELEASE)
            # player.drop("Net is not good.")
            resp = baseProto_pb2.S_C_ExitRoomResult()
            resp.result = False
            self.sendOne(player, resp)

    def onModifyName(self, player, req):
        pass

    def onDissolveRoom(self, player, req):
        if not player.game:
            log(u'[try dissolve game][error]nickname[%s] is not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        player.game.onDissolveRoom(player)

    def onDissolveVote(self, player, req):
        if not player.game:
            log(u'[try dissolve vote][error]nickname[%s] is not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        log(u'[try dissolve vote]nickname[%s] vote[%s] room[%s].'%(player.nickname, req.result, player.game.roomId), LOG_LEVEL_RELEASE)

        player.game.onDissolveVote(player, req.result)

    def onGMControl(self, player, req):
        if not player.game:
            log(u'[try control][error]nickname[%s] is not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        errorMessage ={
            'packError':'命令格式错误'.decode(LANG_CODE),
            'gameError':'未加入游戏'.decode(LANG_CODE)
        }

        log(u'[try control]nickname[%s] want to control game.'%(player.nickname), LOG_LEVEL_RELEASE)
        if not player.isGM:
            log(u'[try control][error]nickname[%s] is not GM.'%(player.nickname), LOG_LEVEL_RELEASE)
            return
        commands = req.GMMessage.split(',')
        if not commands:
            self.sendGMErr(player,errorMessage['packError'])
            log(u'[try control][error]control failed, no command.', LOG_LEVEL_RELEASE)
            return

        #记录GM命令
        curTime = datetime.now()
        dateTimeStr = curTime.strftime("%Y-%m-%d %H:%M:%S")
        GMControlData = {'time':dateTimeStr, 'gamId':self.ID, 'roomId': player.game.roomId, 'message':req.GMMessage}
        redis = self.getPublicRedis()
        redis.lpush(GM_CONTROL_DATA%player.uid, GMControlData)
        redis.ltrim(GM_CONTROL_DATA%player.uid, 0, GM_CONTROL_DATA_MAX_LEN)

        for command in commands:
            try:
                type, data = command.split(':')
                # type, data = req.GMMessage.split(':')
            except:
                self.sendGMErr(player,errorMessage['packError'])
                log(u'[try control][error]control failed, nickname[%s] data[%s].'%(player.nickname, req.GMMessage), LOG_LEVEL_RELEASE)
                return
            
            player.game.onGMControl(player, int(type), data)

    def sendGMErr(self, player, errMsg):
        resp = baseProto_pb2.S_C_GMControl()
        resp.result = False
        resp.reason = errMsg
        self.sendOne(player, resp)
        
    def onTalk(self, player, req):
        if not player.game:
            log(u'[try talk][error]nickname[%s] not in game.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        log(u'[try talk]nickname[%s] talk[%s] [%s] [%s].'%(player.nickname, req.emoticons, req.voice, req.duration), LOG_LEVEL_RELEASE)
        emoticons = req.emoticons
        side = player.chair
        voiceNum = req.voice
        voiceLen = req.duration
        player.game.onTalk(emoticons, side, voiceNum, voiceLen)

    def onDebugProto(self, player, req): #单客户端调试
        game = player.game
        side = req.selfSide

        if game.roomId not in self.globalCtrl.num2game:
            log(u'[on debug proto][error]account[%s] not in game.'%(player.account), LOG_LEVEL_RELEASE)
            return

        if side >= game.maxPlayerCount or not game.players[side]:
            log(u'[on debug proto][error]side[%s] not in game[%s], maxPlayerCount[%s].'%(side, game.roomId, game.maxPlayerCount), LOG_LEVEL_RELEASE)
            return

        msgCode = req.msgCode
        protoData = struct.pack('>I', req.msgCode) + req.data
        log(u'[on debug proto]game[%s] side[%s] msgCode[%s].'%(game.roomId, side, msgCode), LOG_LEVEL_RELEASE)

        self.resolveMsg(game.players[side], protoData)

    def onSetGps(self, player, req): #发送gps信息
        if player.game:
            player.game.onSetGps(player, req.gpsValue)

    def onGetOldBalance(self, player, req): #获得上局回放数据
        oldBalanceData = None
        if player.game:
            oldBalanceData = player.game.oldBalanceData
        resp = mahjong_pb2.S_C_OldBalance()
        if oldBalanceData:
            log(u'[on get old balance]get old balance succeed.', LOG_LEVEL_RELEASE)
            resp.balance.CopyFrom(oldBalanceData)
        self.sendOne(player, resp)

    def useRoomCards(self, game): #一局后使用房卡
        ymd = datetime.now().strftime("%Y-%m-%d")
        ownner = game.players[OWNNER_SIDE]
        redis = self.getPublicRedis()
        # 获取俱乐部编号
        room_id = game.roomId
        club_number = redis.hget(ROOM2SERVER % room_id, "club_number")

        pipe = redis.pipeline()

        if not game.ownner:
            ownner.roomCards -= game.needRoomCards
            pipe.incrby(USER4AGENT_CARD%(ownner.parentAg, ownner.uid), -game.needRoomCards)
            useDatas = [-game.needRoomCards, 1, ownner.roomCards, game.roomId]
            useStr = ';'.join(map(str, useDatas))
            uid = ownner.uid
            pipe.lpush(PLAYER_DAY_USE_CARD%(ownner.uid, ymd), useStr)
            pipe.expire(PLAYER_DAY_USE_CARD%(ownner.uid, ymd), SAVE_PLAYER_DAY_USE_CARD_TIME)
            pipe.hincrby(PLAYER_DAY_DATA%(ownner.uid, ymd), 'roomCard', game.needRoomCards)
            pipe.expire(PLAYER_DAY_DATA%(ownner.uid, ymd), PLAYER_DAY_DATA_SAVE_TIME)

        else: #代开
            account2user_table = FORMAT_ACCOUNT2USER_TABLE%(game.ownner)
            table = redis.get(account2user_table)
            uid = table.split(':')[-1]
            pipe.hincrby(PLAYER_DAY_DATA%(uid, ymd), 'roomCard', game.needRoomCards)
            pipe.expire(PLAYER_DAY_DATA%(uid, ymd), PLAYER_DAY_DATA_SAVE_TIME)
            pipe.sadd(FORMAT_LOGIN_DATE_TABLE%(ymd), game.ownner)
            if club_number:
                pipe.incrby(CLUB_ROOM_CARDS_DAY_TOTAL % (club_number, ymd), game.needRoomCards)
                pipe.incrby(CLUB_ROOM_CARDS_ALL_TOTAL % (club_number), game.needRoomCards)

        pipe.incrby(DAY_ALL_PLAY_ROOM_CARD%(ymd), game.needRoomCards)
        pipe.expire(DAY_ALL_PLAY_ROOM_CARD%(ymd), CASH_TABLE_TTL)
        pipe.incrby(DAY_AG_PLAY_ROOM_CARD%(game.parentAg, ymd), game.needRoomCards)
        pipe.expire(DAY_AG_PLAY_ROOM_CARD%(game.parentAg, ymd), CASH_TABLE_TTL)
        pipe.incrby(GAME_ROOMCARDS_DAY_TOTAL%(self.ID, ymd), game.needRoomCards)
        pipe.incrby(GAME_ROOMCARDS_ALL_TOTAL%(self.ID), game.needRoomCards)
        self.dynamic.useRoomCards(game, self, uid, club_number)
        pipe.execute()
        game.isUseRoomCards = True

    def recoverRoomCards(self, game): #代开房间未使用房卡
        redis = self.getPublicRedis()
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(game.ownner)
        table = redis.get(account2user_table)
        uid = table.split(':')[-1]
        parentAg = redis.hget(table, 'parentAg')
        if not parentAg:
            parentAg = game.parentAg
        elif int(parentAg) != int(game.parentAg): #切换了公会
            newTopParentAg = self.getTopAgentId(parentAg)
            oldTopParentAg = self.getTopAgentId(game.parentAg)
            if oldTopParentAg != newTopParentAg: #不同省级
                parentAg = oldTopParentAg
        roomCards = redis.incrby(USER4AGENT_CARD%(parentAg, uid), game.needRoomCards)
        ymd = datetime.now().strftime("%Y-%m-%d")
        useDatas = [game.needRoomCards, 3, roomCards, game.roomId]
        useStr = ';'.join(map(str, useDatas))
        pipe = redis.pipeline()
        pipe.lpush(PLAYER_DAY_USE_CARD%(uid, ymd), useStr)
        pipe.expire(PLAYER_DAY_USE_CARD%(uid, ymd), SAVE_PLAYER_DAY_USE_CARD_TIME)
        pipe.execute()
        self.removeOtherGameData(game)

    def saveReplayData(self, game): #把这局的游戏过程打包成回放数据
        resp = replay4proto_pb2.ReplayData()
        resp.mahjongData.extend(game.replayinitCardsData)
        resp.data.extend(game.replayData)
        resp.privateData = game.replayRefreshData
        replayStr = resp.SerializeToString()
        print [replayStr]
        return replayStr

    def savePlayerBalanceData(self, game, userDatas):
        """
        玩家每小局数据保存入库
        """
        redis = self.getPublicRedis()
        pipe = redis.pipeline()
        roomData = GAME_ROOM_DATA%(game.roomId, game.setStartTime) #GAME_ROOM_DATA：用于存储每一小局的具体数据
        game2room = GAME2ROOM%(game.roomId, game.gameStartTime) #GAME2ROOM：用于存储每一大局包含了哪些小局
        pipe.lpush(game2room, roomData)
        pipe.ltrim(game2room, 0, MAX_PLAY_ROOM_NUM)
        
        replayRedis = self.getPrivateRedis()
        replayPipe = replayRedis.pipeline()
        replayStr = self.saveReplayData(game)
        replayNum = replayRedis.incr(PLAYER_REPLAY_NUM) #PLAYER_REPLAY_NUM：回放编号，无限递增以防重复
        replayPipe.zadd(PLAYER_REPLAY_SET, replayStr, replayNum) #PLAYER_REPLAY_SET：回放集合
        replaySetLen = replayRedis.zcard(PLAYER_REPLAY_SET)
        if replaySetLen >= MAX_REPLAY_LEN:
            replayPipe.zremrangebyrank(PLAYER_REPLAY_SET, 0, (replaySetLen - MAX_REPLAY_LEN))
        replayPipe.execute()

        score = []
        descs = []
        times = []
        cards = []
        for side in xrange(len(game.players)):
            account = game.players[side].account
            userTable = redis.get(FORMAT_ACCOUNT2USER_TABLE%(account))
            pipe.hincrby(userTable, 'playCount', 1)
            
            userData = userDatas[side]
            score.append(str(userData.score))
            descs.append(','.join(userData.descs))
            times.append(','.join(map(str,userData.times)))
            cards.append(','.join(userData.cards))
        scoreStr = ':'.join(score)
        descsStr = '|'.join(descs)
        timesStr = '|'.join(times)
        cardsStr = '|'.join(cards)
        pipe.hmset(roomData,
            {
                'actionData'    :   replayNum,
                'startTime'     :   game.setStartTime,
                'endTime'       :   game.setEndTime,
                'score'         :   scoreStr,
                'descs'         :   descsStr,
                'times'         :   timesStr,
                'tiles'         :   cardsStr,
            }
        )
        pipe.expire(roomData, MAX_GAME_ROOM_DATA_TIME)
        pipe.execute()

    def clubPlyaerSaveReplay(self, game, gamesData, pipe):
        """ 存储俱乐部的录像

        """

        room_id = game.roomId
        club_number = pipe.hget(ROOM2SERVER % room_id, "club_number")
        if not club_number:
            return
        pipe.sadd("club:replay:%s:set" % club_number, gamesData)
        # 按照日期分开存储
        pipe.sadd("club:replay:%s:%s:set" % (club_number, time.strftime("%Y-%m-%d", time.localtime())), gamesData)

    def savePlayerTotalBalanceData(self, game, totalUserData):
        """
        玩家一轮游戏完总数据保存入库
        """
        redis = self.getPublicRedis()
        pipe = redis.pipeline()
        gamesData = PLAY_GAME_DATA%(game.roomId, game.gameStartTime) #PLAY_GAME_DATA：每个大局的具体数据
        players = []
        score = []
        descs = []
        times = []
        cards = []
        roomSettings = []
        for side in xrange(len(game.players)):
            player = game.players[side]
            account = player.account
            playedRoomsData = PLAYER_PLAY_ROOM%(account) #PLAYER_PLAY_ROOM：玩家玩过的房间列表
            pipe.lpush(playedRoomsData, gamesData)
            pipe.ltrim(playedRoomsData, 0, MAX_PLAY_ROOM_NUM)
            
            players.append('%s,%s'%(side, account))
            userData = totalUserData[side]
            score.append(str(userData.score))
            descs.append(','.join(userData.descs))
            times.append(','.join(map(str,userData.times)))
            cards.append(','.join(userData.cards))
            roomSettings.append(userData.roomSetting)
            
            self.removeExitPlayer(pipe, player, game)

        self.clubPlyaerSaveReplay(game, gamesData, redis)
        
        playersStr = ':'.join(players)
        scoreStr = ':'.join(score)
        descsStr = '|'.join(descs)
        timesStr = '|'.join(times)
        cardsStr = '|'.join(cards)
        roomSettingStr = '|'.join(roomSettings)
        if game.otherRoomTable:
            ownner = 100
        else:
            ownner = 0
        pipe.hmset(gamesData,
            {
                'player'          :   playersStr,
                'startTime'       :   game.gameStartTime,
                'endTime'         :   game.gameEndTime,
                'gameid'          :   self.ID,
                'ag'              :   game.parentAg,
                'score'           :   scoreStr,
                'descs'           :   descsStr,
                'times'           :   timesStr,
                'tiles'           :   cardsStr,
                'roomSettings'    :   roomSettingStr,
                'ownner'          :   ownner
            }
        )
        pipe.expire(gamesData, MAX_GAME_ROOM_DATA_TIME)
        if game.otherRoomTable:
            pipe.hmset(game.otherRoomTable,\
                {
                    'gameType':2,
                    'minNum':0,
                    'maxNum':0,
                }
            )
            pipe.expire(game.otherRoomTable, 1 * 24 * 60 * 60)
        #局数统计
        curDateStr = datetime.now().strftime("%Y-%m-%d")
        dayAgPlayCountStr = DAY_ALL_PLAY_COUNT%(curDateStr, game.parentAg)
        pipe.incrby(ALL_PLAY_COUNT%(game.parentAg),game.gamePlayedCount)
        pipe.incrby(dayAgPlayCountStr, game.gamePlayedCount)
        pipe.expire(dayAgPlayCountStr, DAY_ALL_PLAY_COUNT_SAVE_DAY)
        ymd = datetime.now().strftime("%Y-%m-%d")
        for player in game.getPlayers():
            pipe.hincrby(PLAYER_DAY_DATA%(player.uid, ymd), 'playCount', game.gamePlayedCount)
            pipe.expire(PLAYER_DAY_DATA%(player.uid, ymd), PLAYER_DAY_DATA_SAVE_TIME)
        pipe.execute()

    def saveExitPlayer(self, player, game): #退出的玩家
        log(u'[on save exit player] save player[%s].'%(player.account), LOG_LEVEL_RELEASE)
        redis = self.getPublicRedis()
        pipe = redis.pipeline()
        serverExitPlayer = SERVER_EXIT_PLAYER%(self.serviceTag, self.ID)
        exitPlayerData = EXIT_PLAYER%(player.account)
        pipe.hmset(exitPlayerData,
            {
                'ip'            :       self.ip,
                'port'          :       self.port,
                'game'          :       game.roomId,
                'side'          :       player.chair
            }
        )
        pipe.sadd(serverExitPlayer, player.account)
        result = pipe.execute()
        log(u'[on save exit player] save result: %s.'%(result), LOG_LEVEL_RELEASE)
        log(u'[on save exit player] save key[%s] result[%s].'%(exitPlayerData, redis.exists(exitPlayerData)), LOG_LEVEL_RELEASE)

    def savePlayerGameData(self, player, passwd):
        userOnlineTable = FORMAT_CUR_USER_GAME_ONLINE%(player.account)
        redis = self.getPublicRedis()
        redis.hset(userOnlineTable, 'game', passwd)

    def removePlayerGameData(self, player):
        userOnlineTable = FORMAT_CUR_USER_GAME_ONLINE%(player.account)
        redis = self.getPublicRedis()
        redis.hdel(userOnlineTable, 'game')

    def saveSetStartData(self, game):
        if game.otherRoomTable:
            redis = self.getPublicRedis()
            accountList = []
            for player in game.getPlayers():
                accountList.append(player.account)
            accountsStr = ';'.join(accountList)
            redis.hmset(game.otherRoomTable,\
                {
                    'gameType':1,
                    'minNum':game.curGameCount,
                    'maxNum':game.gameTotalCount,
                    'accountList':accountsStr,
                }
            )
            redis.hmset(ROOM2SERVER % (game.roomId),
                        {
                            'curGameCount': game.curGameCount,
                            'maxGameCount': game.gameTotalCount,
                        })

    def saveOtherRoomEndTime(self, game, timestamp):
        if game.otherRoomTable:
            redis = self.getPublicRedis()
            redis.hset(game.otherRoomTable, 'endTime', timestamp)

    def removeExitPlayer(self, pipe, player, game): #退出的玩家
        log(u'[on remove exit player] exit player[%s].'%(player.account), LOG_LEVEL_RELEASE)
        serverExitPlayer = SERVER_EXIT_PLAYER%(self.serviceTag, self.ID)
        exitPlayerData = EXIT_PLAYER%(player.account)
        pipe.delete(exitPlayerData)
        # pipe.expire(exitPlayerData, EXIT_WAITING_TIME)
        pipe.srem(serverExitPlayer, player.account)
        return pipe

    def removeOtherGameData(self, game):
        redis = self.getPublicRedis()
        redis.delete(game.otherRoomTable)

    def tryRmExitPlayerData(self, player, game):
        redis = self.getPublicRedis()
        pipe = redis.pipeline()
        self.removeExitPlayer(pipe, player, game)
        pipe.lrem(ROOM2ACCOUNT_LIST%(game.roomId), player.account)
        pipe.execute()
        self.removePlayerGameData(player)
        #关闭服务器标识
        if self.isEnding:
            player.endType = 'waitEnd'

    def onExit(self, player, req = None):
        if not player.account:
            log(u'[try exit][error]account is null.', LOG_LEVEL_RELEASE)
            return

        #在游戏中
        if player.game:
            self.onExitGame(player, sendMessage = False)

        self.userDBOnLogout(player)

    def onRemoveGame(self, game):

        try:
            if not game.isUseRoomCards and game.ownner:
                self.recoverRoomCards(game)
            redis = self.getPublicRedis()
            club_number, auto_id = redis.hmget(ROOM2SERVER % (game.roomId), 'club_number', "auto_id")

            redis.delete(ROOM2SERVER % (game.roomId))
            if club_number:
                redis.srem(AG2SERVER % ("%s-%s" % (game.parentAg, club_number)), game.roomId)
                redis.srem("otherCreate:Room:%s:%s:%s:set" % (game.parentAg, club_number, auto_id), game.roomId)
            else:
                if redis.exists(AG2SERVER % ("%s-" % game.parentAg)):
                    redis.srem(AG2SERVER % ("%s-" % game.parentAg), game.roomId)
                redis.srem(AG2SERVER % (game.parentAg), game.roomId)

            redis.srem(SERVER2ROOM % (self.serviceTag), game.roomId)
            redis.hincrby(self.table, 'roomCount', -1)
            self.globalCtrl.removeGame(game)
        except Exception as err:
            traceback.print_exc()
            redis.srem(SERVER2ROOM % (self.serviceTag), game.roomId)
            redis.hincrby(self.table, 'roomCount', -1)
            self.globalCtrl.removeGame(game)

    def userDBOnJoinGame(self, player, game):
        redis = redis_instance.getInst(PUBLIC_DB)
        pipe = redis.pipeline()
        pipe.hset(ROOM2SERVER%(game.roomId), 'playerCount', game.playerCount)
        if game.otherRoomTable:
            pipe.hset(game.otherRoomTable, 'minNum', game.playerCount)
        pipe.lpush(ROOM2ACCOUNT_LIST%(game.roomId), player.account)
        pipe.execute()

    def userDBOnExitGame(self, player, game, isDrop):
        redis = redis_instance.getInst(PUBLIC_DB)
        pipe = redis.pipeline()
        pipe.hset(ROOM2SERVER%(game.roomId), 'playerCount', game.playerCount)
        if game.otherRoomTable:
            pipe.hset(game.otherRoomTable, 'minNum', game.playerCount)
        pipe.execute()

        if isDrop:
            # self.onExit(player)
            reactor.callLater(300, self.onDropTimeoutPlayer, player)

    def onDropTimeoutPlayer(self, player):
        if player in self.peerList[:]:
            player.drop('game end timeout', consts.DROP_REASON_INVALID, type = 2)

    def userDBOnLogin(self, player, reg = False):
        curTime = datetime.now()
        dateTimeStr = curTime.strftime("%Y-%m-%d %H:%M:%S")
        #本次登录session初始化
        player.sessionId = player.uid + curTime.strftime("%Y%m%d%H%M%S")
        redis = self.getPublicRedis()
        pipe = redis.pipeline()
        if reg:
            curDateStr = dateTimeStr.split(' ')[0]
            curRegDateTable = FORMAT_REG_DATE_TABLE%(curDateStr)
            pipe.sadd(curRegDateTable, player.account)
        userDBLogin(redis, pipe, player.account, self.ID, player.table, \
            player.descTxt, self.serviceTag, self.table, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), player.parentAg)

    def userDBOnLogout(self, player):
        redis = self.getPublicRedis()
        curTime = datetime.now()
        dateTimeStr = curTime.strftime("%Y-%m-%d %H:%M:%S")
        playerSettingTable = FORMAT_ACCOUNT_SETTING_TABLE%(player.account, self.ID)
        pipe = redis.pipeline()

        self.removePlayerGameData(player)
        userDBLogout(pipe, player.account, self.ID, player.table, player.descTxt, self.table, dateTimeStr)

        key = EXIT_PLAYER%(player.account)
        #退出数据清空，暂时在exitGame处理
        if player.account in self.account2players:
            del self.account2players[player.account]
        log(u'[try logout]nickname[%s] logout succeed.'%(player.nickname), LOG_LEVEL_RELEASE)
        player.account = ""

        log(u'[try logout]logout end, join again key[%s] result[%s].'%(key, redis.exists(key)), LOG_LEVEL_RELEASE)

    def onAddPeer(self, player):
        pass

    def onRemovePeer(self, player):
        if player.account:
            self.onExit(player)

    def closeServer(self):
        self.isEnding = True
        if not self.isClosed:
            #确保在线玩家先入库
            for player in self.account2players.values():
                if not player.game:
                    self.onExit(player)

            #断线通知
            for peer in self.peerList[:]:
                if not peer.game:
                    peer.drop("close game server", consts.DROP_REASON_CLOSE_SERVER, type = 2)

            for game in self.globalCtrl.num2game.values():
                if game.curGameCount == 0:
                    for player in game.players:
                        if player in self.account2players.values():
                            self.onExit(player)
                            player.drop("close game server", consts.DROP_REASON_CLOSE_SERVER, type = 2)
                    game.endGame()

            if not self.isWaitEnd:
                log('on closeServer', LOG_LEVEL_RELEASE)
                reactor.callLater(SERVICE_STOP_SECS, self.endAllGame)
                self.isWaitEnd = True
            if not self.account2players:
                self.isClosed = True
        else:
            if not self.account2players:# and not self.transferQueues:
                reactor.stop()

    def endAllGame(self):
        #确保在线玩家先入库
        for player in self.account2players.values():
            self.onExit(player)

        #断线通知
        for peer in self.peerList[:]:
            peer.drop("close game server", consts.DROP_REASON_CLOSE_SERVER, type = 2)

        for game in self.globalCtrl.num2game.values():
            game.endGame()

        reactor.callLater(WAIT_END_SECS, reactor.stop)

    def stopFactory(self):
        for game in self.globalCtrl.num2game.values():
            game.endGame()

        #清空游戏数据表
        redis = self.getPublicRedis()
        pipe = redis.pipeline()
        pipe.delete(self.table)
        # pipe.lrem(FORMAT_GAME_SERVICE_SET%(self.ID), self.table)

        #清空原服务器下的所有断线重连信息
        serverExitPlayer = SERVER_EXIT_PLAYER%(self.serviceTag, self.ID)
        if redis.exists(serverExitPlayer):
            exitPlayerList = redis.smembers(serverExitPlayer)
            log(u'[on stop factory] exitPlayerList %s.'%(exitPlayerList), LOG_LEVEL_RELEASE)
            for exitPlayer in exitPlayerList:
                if redis.exists(EXIT_PLAYER%(exitPlayer)):
                    pipe.delete(EXIT_PLAYER%(exitPlayer))
        pipe.delete(serverExitPlayer)
        pipe.execute()

        for peer in self.peerList[:]:
            try:
                redis.srem(ONLINE_ACCOUNTS_TABLE, peer.account)
            except:
                pass

    def onCheck(self, timestamp):
        super(BaseServer, self).onCheck(timestamp)
        # if isServiceOutDate():
            # log('on closeServer', LOG_LEVEL_RELEASE)
            # self.closeServer()

    def onRefresh(self, timestamp):
        super(BaseServer, self).onRefresh(timestamp)

        if not self.resovledServiceProtocolsLock and timestamp - self.lastResovledServiceProtocolsTimestamp >= SERVICE_PROTOCOLS_INTERVAL_TICK:
            self.resovledServiceProtocolsLock = True
            reactor.callInThread(self.readServiceProtocol, timestamp)
            self.lastResovledServiceProtocolsTimestamp = timestamp

        #定时同步所有货币流水
#        if not self.globalCtrl.currencyAgentCashRefreshLock and timestamp - self.currencyAgentCashRefreshTimestamp >= AGENT_CASH_REFRESH_TICK:
#            self.globalCtrl.currencyAgentCashRefreshLock = True
#            reactor.callInThread(self.globalCtrl.refreshCurrencyCash, self.currency)
#            self.currencyAgentCashRefreshTimestamp = timestamp

        if self.gameCloseTimestamp:
            if timestamp > self.gameCloseTimestamp:
                # log('on closeServer', LOG_LEVEL_RELEASE)
                self.closeServer()

        games = self.globalCtrl.getTickGames()
        for game in games:
            try:
                game.onTick(timestamp)
            except:
                for tb in traceback.format_exc().splitlines():
                    log(tb, LOG_LEVEL_ERROR)

    def readServiceProtocol(self, timestamp):
        redis = self.getPublicRedis()

        protoName = redis.lpop(self.serviceProtocolTable)

        while protoName:
            log('protoName[%s]'%(protoName), LOG_LEVEL_RELEASE)
            protoArgs = protoName.split('|')
            if protoArgs:
                protoHead = protoArgs[0]
                if protoHead in self.serviceProtoCalls:
                    try:
                        self.serviceProtoCalls[protoHead](timestamp, *protoArgs[1:])
                    except:
                        for tb in traceback.format_exc().splitlines():
                            log(tb, LOG_LEVEL_ERROR)
            protoName = redis.lpop(self.serviceProtocolTable)

        self.resovledServiceProtocolsLock = False

    def onServiceGameClose(self, timestamp):
        #收到关闭服务器协议后就不允许新连接了
        redis = self.getPublicRedis()
        redis.lrem(FORMAT_GAME_SERVICE_SET%(self.ID), self.table)

        self.gameCloseTimestamp = timestamp + DEFAULT_CLOSE_GAME_TICK
        noticeProto = baseProto_pb2.S_C_Notice()
        noticeProto.repeatTimes = 2
        noticeProto.repeatInterval = 0
        noticeProto.id = 100000

        for player in self.account2players.itervalues():
            noticeProto.txt = player.lang.GAME_CLOSE_TIPS
            self.sendOne(player, noticeProto)

    def onServiceMemberRefresh(self, timestamp, memberAccount):
        if memberAccount in self.account2players:
            player = self.account2players[memberAccount]
            player.loadDB(player.table, isInit=False)
            if player.valid != '1':
                player.drop('account[%s] refresh to invalid.'%(player.account), consts.DROP_REASON_FREEZE)
                return
            #同步数据
            walletProto = baseProto_pb2.S_C_WalletMoney()
            walletProto.roomCards = player.roomCards
            self.sendOne(player, walletProto)

    def onServiceAgentBroadcast(self, timestamp, ag, content, repeatTimes, repeatInterval, id):
        noticeProto = baseProto_pb2.S_C_Notice()
        noticeProto.repeatTimes = int(repeatTimes)
        noticeProto.repeatInterval = int(repeatInterval)
        noticeProto.txt = content.decode(LANG_CODE)
        noticeProto.id = int(id)
        parentAg = ag
        redis = self.getPublicRedis()
        if len(ag) == 1:
            self.sendAll(noticeProto)
        else:
            agList = self.getAllChild(parentAg)
            agList.append(parentAg)
            for player in self.account2players.values():
                if player.parentAg in agList and player.game and player.account not in player.game.exitPlayers:
                    self.sendOne(player, noticeProto)
        # self.send([player for player in self.account2players.itervalues() \
            # if isParentAg(redis, player.account, parentAg, player.table)], noticeProto)

    def getAllChild(self, ag):
        agList = []
        redis = self.getPublicRedis()
        childAgList = redis.smembers(AGENT_CHILD_TABLE%(ag))
        agList.extend(childAgList)
        if childAgList:
            for childAg in childAgList:
                agList.extend(self.getAllChild(childAg))
        return agList

    def getTopAgentId(self, agentId):
        """
        获取总公司ID
        """
        redis = self.getPublicRedis()
        agType = redis.hget(AGENT_TABLE%(agentId),'type')
        if agType in ['0','1']:
            return agentId

        while 1:
            agentId = redis.hget(AGENT_TABLE%(agentId),'parent_id')
            agType = redis.hget(AGENT_TABLE%(agentId),'type')
            if int(agType) == 1:
                return agentId

    def onServiceReSession(self, timestamp, account, sid):
        #第三方平台用户session刷新(一般用于同一账号二次登入)
        if account in self.account2players:
            player = self.account2players[account]
            if player.operatorSessionId != sid:
                player.operatorSessionId = sid
                player.drop('Kick for repeated login 3rd party.', consts.DROP_REASON_REPEAT_LOGIN)

    def onServiceKickMember(self, timestamp, memberAccount):
        """
        踢出指定玩家
        """
        if memberAccount in self.account2players:
            self.account2players[memberAccount].drop(\
                    'account[%s] is kicked by manager.'%(memberAccount), consts.DROP_REASON_INVALID)

    def onJoinPartyRoom(self, timestamp, accountList, ag, rule):
        """
        创建娱乐模式游戏房间
        """
        rule = str(self.getGameModule(self, rule, False).getPartyRoomRule())
        log('[onJoinPartyRoom] rule[%s]'%(rule), LOG_LEVEL_RELEASE)
        accountList = list(eval(accountList))
        ownnerAccount = accountList[0]
        player = self.getGameModule(self, rule).getRobot()
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(ownnerAccount)
        redis = self.getPublicRedis()
        table = redis.get(account2user_table)
        player.loadDB(table)
        player.ip = ''
        resp = baseProto_pb2.C_S_DebugConnecting()
        resp.roomSetting.rule = rule
        regResp = baseProto_pb2.S_C_Connected()
        self.onTryRegSucceed(player, '', False, '', resp.roomSetting, -2)
        self.createGame(player, regResp, rule, isSendMsg = False)

        game = player.game
        game.isParty = True
        game.onExitGame(player, sendMessage = False)
        self.onExit(player)
        redis.set(IS_MATCH_FINISHED%(ownnerAccount), '1')
        resp.roomSetting.roomid = game.roomId
        for account in accountList[1:]:
            otherPlayer = game.getRobot()
            account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
            table = redis.get(account2user_table)
            otherPlayer.loadDB(table)
            otherPlayer.ip = ''
            otherPlayer.lang = getLangInst()
            otherPlayer.factory = self
            otherPlayer.hashKey = 'party'
            self.onTryRegSucceed(otherPlayer, '', False, '', resp.roomSetting, -3)

            game.onExitGame(otherPlayer, sendMessage = False)
            self.onExit(otherPlayer)
            redis.set(IS_MATCH_FINISHED%(account), '1')
            log('[onJoinPartyRoom]isOnline[%s]'%(otherPlayer.isOnline), LOG_LEVEL_RELEASE)
        log('[onJoinPartyRoom]accountList[%s]'%(accountList), LOG_LEVEL_RELEASE)

    def onDissolvePlayerRoom(self, timestamp, roomId):
        if roomId not in self.globalCtrl.num2game:
            log('[on dissolve player room][error]not found room[%s]'%(roomId), LOG_LEVEL_RELEASE)
            return

        log('[on dissolve player room]room[%s]'%(roomId), LOG_LEVEL_RELEASE)

        game = self.globalCtrl.num2game[roomId]
        if game.otherRoomTable and game.players.count(None) == game.maxPlayerCount:
            self.removeOtherGameData(game)
        for player in game.getOnlinePlayers():
            player.drop("on dissolve player room", consts.DROP_REASON_INVALID, type = 2)

        game.endGame()

    def onCreateGame4Other(self, timestamp, account, ag, rule, ruleText):
        """ 修改内容，将代理和俱乐部用-来分割，然后进行存储

        """
        tempAg = str(ag).split("-")
        club_number = ''
        if len(tempAg) > 1:
            ag, club_number = tempAg
        else:
            ag = ag

        redis = self.getPublicRedis()
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        table = redis.get(account2user_table)
        ownnerNickname = redis.hget(table, 'nickname')
        uid = table.split(':')[-1]
        params = eval(rule)
        isHidden = int(params[-1])
        del params[-1]
        rule = str(params)
        needRoomCards = int(params[-2])
        times = self.getTimestamp()
        roomCards = redis.incrby(USER4AGENT_CARD%(ag, uid), -needRoomCards)
        if roomCards < 0:
            roomCards = redis.incrby(USER4AGENT_CARD%(ag, uid), needRoomCards)
            log('[on create game for other][error]roomCards[%s] is not enough[%s]'%(roomCards, needRoomCards), LOG_LEVEL_RELEASE)
            return

        _game = self.getGameModule(self, rule)
        addResult = self.globalCtrl.addGame(_game, self.ID)

        if not addResult:
            log(u'[try create game for other][error]no rooms!!!.', LOG_LEVEL_RELEASE)
            return

        ymd = datetime.now().strftime("%Y-%m-%d")
        useDatas = [-needRoomCards, 2, roomCards, _game.roomId]
        useStr = ';'.join(map(str, useDatas))
        pipe = redis.pipeline()
        pipe.lpush(PLAYER_DAY_USE_CARD%(uid, ymd), useStr)
        pipe.expire(PLAYER_DAY_USE_CARD%(uid, ymd), SAVE_PLAYER_DAY_USE_CARD_TIME)

        roomDataKey = OTHER_ROOM_DATA%(account, times, _game.roomId)
        _game.ownner = account
        _game.parentAg = ag
        _game.otherRoomTable = roomDataKey
        if isHidden:
            _game.isHidden = True
        # pipe = redis.pipeline()
        room_server_data = {
                'ip'         :       self.ip,
                'port'       :       self.port,
                'ag'         :       ag,
                'gameid'     :       self.ID,
                'hidden'     :       isHidden,
                'dealer'     :       ownnerNickname,
                'playerCount':       0,
                'maxPlayer'  :       _game.maxPlayerCount,
                'gameName'   :       _game.roomName,
                'baseScore'  :       eval(rule)[-1],
                'ruleText'   :       _game.ruleDescs,
            }
        if club_number:
            room_server_data["club_number"] = club_number
            room_server_data["auto_id"] = -1

        pipe.hmset(ROOM2SERVER%(_game.roomId),
            room_server_data
        )
        # pipe.sadd(AG2SERVER%("%s-%s" % (ag, club_number)), _game.roomId)
        if not club_number:
            pipe.sadd(AG2SERVER % ("%s" % (ag)), _game.roomId)
        else:
            pipe.sadd(AG2SERVER%("%s-%s" % (ag, club_number)), _game.roomId)
        pipe.sadd(SERVER2ROOM%(self.serviceTag), _game.roomId)
        pipe.hincrby(self.table, 'roomCount', 1)
        pipe.hmset(roomDataKey,
            {
                'roomId'        :     _game.roomId,
                'name'          :     _game.roomName,
                'gameType'      :     0,
                'minNum'        :     0,
                'maxNum'        :     _game.maxPlayerCount,
                'time'          :     times,
                'rule'          :     _game.ruleDescs,
                'roomType'      :     isHidden,
                'gameid'        :     self.ID,
                "club_number"   :     club_number
            }
        )
        # pipe.expire(roomDataKey, 1 * 24 * 60 * 60)
        pipe.lpush(MY_OTHER_ROOMS%(account), roomDataKey)
        pipe.execute()
        log(u'[try create game for other]create game succeed, account[%s] room[%s].'%(account, _game.roomId), LOG_LEVEL_RELEASE)

    def getPublicRedis(self):
        return redis_instance.getInst(PUBLIC_DB)

    def getPrivateRedis(self):
        try:
            publicRedis = self.getPublicRedis()
            redisIp, redisPort, redisNum, passwd = publicRedis.hmget(GAME2REDIS%(self.ID), ('ip', 'port', 'num', 'passwd'))
            import redis
            redisdb = redis.ConnectionPool(host=redisIp, port=int(redisPort), db=int(redisNum), password=passwd)
            return redis.Redis(connection_pool=redisdb)
        except Exception as e:
            log('[get private redis][error]message[%s]'%(e), LOG_LEVEL_RELEASE)
            return self.getPublicRedis()

    def getMysqlRedis(self):
        try:
            publicRedis = self.getPublicRedis()
            redisIp, redisPort, redisNum, passwd = publicRedis.hmget('gameRedisDatas2Mysql:hesh', ('ip', 'port', 'num', 'passwd'))
            import redis
            redisdb = redis.ConnectionPool(host=redisIp, port=int(redisPort), db=int(redisNum), password=passwd)
            return redis.Redis(connection_pool=redisdb)
        except Exception as e:
            log('[getMysqlRedis][error]message[%s]' % (e), LOG_LEVEL_RELEASE)
            return

    def sendOne(self, peer, protocol_obj):
        #test
        # print 'test sendOne:%s'%(protocol_obj.DESCRIPTOR.name), protocol_obj
        name = protocol_obj.__class__.__name__
        if peer.isControlByOne and protocol_obj.DESCRIPTOR.name != 'S_C_Disconnected':
            self.sendDebugProto(peer, protocol_obj)
            return
        if isinstance(peer.controlPlayer, Peer):
            super(BaseServer, self).sendOne(peer.controlPlayer, protocol_obj)
        elif isinstance(peer, Peer):
            super(BaseServer, self).sendOne(peer, protocol_obj)
        else:
            print 'File error, send'

    def send(self, peers, protocol_obj, excludes=()):
        #test
        # print 'test send:%s'%(protocol_obj.DESCRIPTOR.name), protocol_obj
        for peer in peers:
            if peer in excludes:
                continue
            if peer.isControlByOne:
                self.sendDebugProto(peer, protocol_obj)
            else:
                if isinstance(peer.controlPlayer, Peer):
                    self.sendData(peer.controlPlayer, self.senderMgr.pack(protocol_obj))
                elif isinstance(peer, Peer):
                    self.sendData(peer, self.senderMgr.pack(protocol_obj))
                else:
                    print 'File error, send'

    def sendDebugProto(self, player, protocol_obj):
        """
        发送调试模式协议
        """
        name = protocol_obj.__class__.__name__
        code = self.senderMgr._cmds[name].msg_code
        protoData = protocol_obj.SerializeToString()

        side = player.chair
        if player.chair < 0:
            side = 0

        controlPlayer = player.controlPlayer

        resp = baseProto_pb2.S_C_DebugProto()
        resp.selfSide = side
        resp.msgCode = code
        resp.data = protoData

        log(u'[send debug proto]controlPlayer[%s] side[%s] proto[%s].'%(controlPlayer.nickname, side, name), LOG_LEVEL_RELEASE)
        if controlPlayer.descTxt:
            self.sendData(controlPlayer, self.senderMgr.pack(resp))
        else:
            self.sendData(player, self.senderMgr.pack(resp))

    def saveGameTotalData(self, id, values):
        """
        记录游戏统计数据,id为需要记录的字段号，values为增加值 
        """
        redis = self.getPublicRedis()
        key = GAME_TOTAL_DATA%(self.ID)
        redis.hincrby(key, id, values)

    def ifMoreThanOneHour(self,strtime2):
        #???????????
        strtime1=time.strftime("%Y-%m-%d %H:%M:%S")
        localtime1=time.strptime(strtime1,'%Y-%m-%d %H:%M:%S')
        localtime2=time.strptime(strtime2,'%Y-%m-%d %H:%M:%S')

        #?????????????
        time1= time.mktime(localtime1)
        time2= time.mktime(localtime2)
        if (time1 - time2) > 300:
                return True
        else:
                return False