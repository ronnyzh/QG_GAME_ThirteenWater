#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: $Author$
@Date: $Date$
@version: $Revision$

Description: Describe module function
"""

from common.gameobject import GameObject
from common import consts
from common.consts import ERR_MSG
from common.log import log, LOG_LEVEL_RELEASE
from common_player import CommonPlayer
from common.deal_manage import *

from common.protocols.poker_consts import *
from common_db_define import *
from card_define import *

import baseProto_pb2
import poker_pb2
import replay4proto_pb2
from pb_utils import *
import random
import time
from datetime import datetime
import copy
import redis_instance
import re
#import statics

CUR_LAG_MS = 2*1000
WAIT_BACK_TIME = 3000 #15*1000 + CUR_LAG_MS
WAIT_DISSOLVE_TIME = 3 * 60 * 1000 #等待解散时间
GAME_NOT_START_END_TIME = 6 * 60 * 60 * 1000
PUBLIC_ROOM_GAME_NOT_START_END_TIME = 5 * 60 * 1000
OTHER_TYPE_GAME_NOT_START_END_TIME = 6 * 60 * 60 * 1000

SAVE_SEND_ALL_PROTO_LIST = ['S_C_TurnAction', 'S_C_DoActionResult', 'S_C_SetStart']
SAVE_SEND_ONE_PROTO_LIST = []
SAVE_SEND_PROC_PROTO_LIST = ['S_C_DealCards']
SAVE_SEND_END_PROTO = 'S_C_Balance'

PING_INTERVAL_TICK = 25*1000


class CommonGame(GameObject):
    """
    """
    def __init__(self, server, ruleParams, needInit = True, roomId = 0):
        """
        """
        self.server = server
        self.roomId = roomId
        self.roomName = ''
        self.parentAg = None

        # 是否允许相同IP玩家进入房间
        self.allowSameIpNotInto = False
        self.curTimeGenerate = int(time.time())

        self.ruleParams = ruleParams
        self.playerCount = 0
        self.maxPlayerCount = self.getMaxPlayerCount()
        self.curGameCount = 0
        self.gameTotalCount = self.getGameTotalCount()
        self.gamePlayedCount = 0
        self.players = [None]*self.maxPlayerCount
        self.side2gps = {}
        self.controlPlayerSide = -1 #调试模式时可能指定由一个人控制四个人
        # self.specialCard = None
        self.isDebug = False
        self.isParty = False
        self.ownner = ''
        self.otherRoomTable = ''
        self.isUseRoomCards = False
        self.needRoomCards = 1
        self.baseScore = 1 #基本分
        self.isSendReadyHand = False
        self.isHidden = False
        #倒计时回调及毫秒
        self.__resetCounter()
        self.stage = WAIT_START #游戏状态
        self.exitPlayers = [] #掉线玩家的位置列表
        self.countPlayerSides = []
        self.ready2NextGameSides = []

        #倒计时毫秒数
        self.discardCounterMs = self.getDiscardCounterMs()
        self.actionCounterMs = self.getActionCounterMs()
        self.balanceCounterMs = self.getBalanceCounterMs()
        self.dissovedCounterMs = 0
        self.dissoved4GameNotStartMs = 0

        #解散
        self.dissolvePlayerSide = -1
        self.dissolve = [None] * self.maxPlayerCount
        self.isSaveGameData = False
        self.isEnding = False
        self.isDissolveEnd = False

        #回放
        self.replayRefreshData = None
        self.saveSendAllProtoList = copy.deepcopy(SAVE_SEND_ALL_PROTO_LIST)
        self.saveSendAllProtoList.extend(self.getSaveSendAllProtoList())
        self.saveSendOneProtoList = copy.deepcopy(SAVE_SEND_ONE_PROTO_LIST)
        self.saveSendOneProtoList.extend(self.getSaveSendOneProtoList())
        self.oldBalanceData = None

        self.dealerSide = -1
        self.dealerCount = 0
        self.lastWinSide = -1 #记录上次赢牌的side
        self.actionNum = 0
        self.extendStr = ''

        #时间记录
        self.gameStartTime = 0
        self.gameEndTime = 0

        self.ruleDescs = []
        if needInit:
            self.initByRuleParams(ruleParams)
        
        #发牌器
        self.dealMgr = self.getDealManager()
        self.setGMType2ValidCmdJudge()

        self.resetSetData()

    def resetSetData(self):
        '''
        每局数据初始化
        '''
        self.setStartTime = 0
        self.setEndTime = 0
        for player in self.getPlayers():
            player.resetPerGame()

        #回放
        self.replayData = []
        self.replayinitCardsData = []
        self.resetReplayData = []

        self.lastDiscard = []
        self.lastDiscardSide = -1
        self.curPlayerSide = 0
        self.lastOperateSide = -1

        self.isGameEnd = False
        self.resetCurAction()

        self.dealMgr.resetCards()

    def resetCurAction(self):
        """
        curActioningSide = side
        """
        # self.curActions = []
        self.curAction2Datas = {}
        self.curActioningSide = -1
        self.curActionedData = []
        # self.curHighestAction = 0
        # self.grabKongCard = ''
        self.side2ActionNum = {}

#++++++++++++++++++++ 响应消息回调 ++++++++++++++++++++


    def onGameStart(self, player):
        """
        开始游戏（房主点击或自动开始）
        """
        self.doBeforeGameStart()
        if player.chair != OWNNER_SIDE:
            log(u'[on game start][error]error chair[%s].'%(player.chair), LOG_LEVEL_RELEASE)
            return

        if self.getEmptyChair() != consts.SIDE_UNKNOWN: #满人
            log(u'[on game start][error]room is not full, empty chair[%s].'%(self.getEmptyChair()), LOG_LEVEL_RELEASE)
            resp = poker_pb2.S_C_GameStartResult()
            resp.result = False
            errMsg = '房间未满，无法开始'.decode('utf-8')
            resp.reason = errMsg
            self.sendOne(player, resp)
            return

        if self.stage != WAIT_START and not self.isEnding:
            log(u'[on game start][error]can not start, stage[%s], isEnding[%s].'%(self.stage, self.isEnding), LOG_LEVEL_RELEASE)
            return

        self.dealGameStartData(player)
        resp = poker_pb2.S_C_GameStartResult()
        resp.result = True
        self.sendOne(player, resp)
        self.doAfterGameStart()

    def dealGameStartData(self, player):
        if not self.setStartTime:
            self.setStartTime = self.server.getTimestamp()
        if not self.gameStartTime:
            self.gameStartTime = self.server.getTimestamp()
            # 数据统计
            #statics.dig_game_start(self)

        self.dissoved4GameNotStartMs = 0
        self.ready2NextGameSides = []
        self.isEnding = False
        self.stage = GAME_READY

    def doAfterGameStart(self):
        """
        """
        self.onSetStart(self.players[OWNNER_SIDE])
        # self.setCounter([OWNNER_SIDE], self.balanceCounterMs, self.onSetStart, [self.players[OWNNER_SIDE]])

    def dealSetStartData(self, player):
        self.stage = GAMING
        self.curGameCount += 1
        self.startLock = True
        oldDealerSide = self.dealerSide
        self.dealerSide = self.getDealer()
        if self.hasDealerCount() and self.dealerSide != -1:
            if oldDealerSide != self.dealerSide:
                self.dealerCount = 0
            self.dealerCount += 1

    def onSetStart(self, player):
        """
        开始游戏（每小局开始）
        """
        if not self.checkStage(GAME_READY):
            return

        # if player.chair != OWNNER_SIDE:
            # log(u'[on set start][error]error chair[%s].'%(player.chair), LOG_LEVEL_RELEASE)
            # return

        self.doBeforeSetStart()
        self.dealSetStartData(player)

        resp = poker_pb2.S_C_SetStart()
        resp.timestamp = self.server.getTimestamp()
        if self.dealerSide != -1:
            resp.dealerSide = self.dealerSide
        if self.dealerCount:
            resp.dealerCount = self.dealerCount

        self.sendAll(resp)

        log(u'[on set start]room[%s] dealer[%s] dealerCount[%s].'\
            %(self.roomId, self.dealerSide, self.dealerCount), LOG_LEVEL_RELEASE)

        self.doAfterSetStart()

    def doAfterSetStart(self):
        """
        """
        # self.countPlayerSides = [self.dealerSide]
        self.server.saveSetStartData(self)
        self.deal()

    def deal(self, isReDeal = False):
        """
        发牌处理
        """
        self.dealMgr.deal()
        eachCards = self.dealMgr.getEachHands()

        resp = poker_pb2.S_C_DealCards()
        resp.timestamp = self.server.getTimestamp()
        resp.isReDeal = isReDeal
        for player, handleCards in zip(self.getPlayers(), eachCards):
            log(u'[deal]room[%s] nickname[%s] handleCards%s.'\
                %(self.roomId, player.nickname, handleCards), LOG_LEVEL_RELEASE)
            player.setHandleCards(handleCards)
            #客户端的牌值为逗号分隔的字串
            playerResp = copy.deepcopy(resp)
            handleCardsStr = ','.join(handleCards)
            playerResp.cards = handleCardsStr
            self.sendOne(player, playerResp)

        self.doAfterDeal()

    def doAfterDeal(self):
        """
        """
        self.doSendAllowActions(self.players[OWNNER_SIDE])

    def dealAllowActionData(self, curPlayer):
        """
        """
        if self.lastDiscardSide == curPlayer.chair:
            self.lastDiscard = []
        self.setCounter([curPlayer.chair], self.actionCounterMs, self.onDoActionTimeout)

        self.resetCurAction()
        self.actionNum += 1
        self.curActioningSide = curPlayer.chair
        self.curPlayerSide = curPlayer.chair

    def doSendAllowActions(self, curPlayer):
        """
        """
        self.dealAllowActionData(curPlayer)

        resp = poker_pb2.S_C_TurnAction()
        resp.side = self.curActioningSide
        self.sendExclude((curPlayer,),resp)
        resp.num = self.actionNum
        if self.curAction2Datas:
            for key, value in self.curAction2Datas.items():
                actions = resp.action.add()
                actions.action = key
                actions.datas.extend(value)
        log(u'[fillAllowAction] resp[%s]'%(resp),LOG_LEVEL_RELEASE)
        # self.fillAllowAction(resp)
        self.sendOne(curPlayer, resp)
        log(u'[doSendAllowActions] curPlayer[%s]'%(curPlayer.chair),LOG_LEVEL_RELEASE)

    def fillAllowAction(self, resp):
        """
        """
        resp.side = self.curActioningSide
        resp.num = self.actionNum
        if self.curAction2Datas:
            for key, value in self.curAction2Datas.items():
                actions = resp.action.add()
                actions.action = key
                actions.datas.extend(value)
        log(u'[fillAllowAction] resp[%s]'%(resp),LOG_LEVEL_RELEASE)
        return resp

    def packDoActionResult(self):
        """
        """
        resp = poker_pb2.S_C_DoActionResult()
        resp.side = self.curActioningSide
        resp.action = self.curActionedData[0]
        resp.datas.extend(self.curActionedData[1])
        log(u'[packDoActionResult] resp[%s]'%(resp),LOG_LEVEL_RELEASE)
        return resp

    def onDoAction(self, player, action, actionCards, num):
        """
        玩家操作
        """
        if not self.checkStage(GAMING):
            return

        # if not self.checkCounter(player):
            # return

        side = player.chair
        if side != self.curActioningSide:
            log(u'[onDoAction][error]side[%s] is not curActioningSide[%s].'%(side, self.curActioningSide), LOG_LEVEL_RELEASE)
            return

        if num != self.actionNum:
            log(u'[onDoAction][error]error num[%s] for side[%s] player[%s], actionNum[%s].'\
                    %(num, side, player.nickname, self.actionNum), LOG_LEVEL_RELEASE)
            return

        self.doCurAction(player, action, actionCards)

    def doCurAction(self, player, action, actionCards):
        """
        """
        log(u'[doCurAction] player[%s] action[%s] actionCards[%s].'\
            %(player.nickname, action, actionCards), LOG_LEVEL_RELEASE)

        cardlist = player.doAction(action, actionCards)
        if action == DISCARD and not cardlist:
            log(u'[doCurAction][error] invalid discard.', LOG_LEVEL_RELEASE)
            return

        self.curActionedData = [action, actionCards]
        player.isActioned = True

        resp = self.packDoActionResult()
        self.sendAll(resp)

        self.doAfterDoCurAction(player, action, actionCards)

    def doAfterDoCurAction(self, player, action, actionCards):
        log(u'[doAfterDoCurAction] room[%s] player[%s].'%(self.roomId, player.chair), LOG_LEVEL_RELEASE)

        self.nextProc(player)

    def nextProc(self, curPlayer):
        """
        下一个流程
        """
        log(u'[nextProc] curPlayer[%s].'%(curPlayer.nickname), LOG_LEVEL_RELEASE)

        if self.isCanEndGame(curPlayer):
            self.isGameEnd = True
            self.lastWinSide = self.getWinSide(curPlayer)
            self.balance()
            return
        print '11111111'
        nexter = self.getNexter(curPlayer)
        print '22222222', nexter
        if not nexter:
            self.balance()
            return
        if nexter.leaveGameStage == 1:
            self.doWinPlayerDatas(nexter)
            return
        self.doSendAllowActions(nexter)

    def doWinPlayerDatas(self, player):
        if self.lastDiscardSide == player.chair:
            self.lastDiscard = []
        player.leaveGameStage = 2
        self.nextProc(player)

    def getWinSide(self, player):
        return player.chair

    def getNexter(self, curPlayer):
        """
        返回curPlayer的下一家
        """
        print '3333333'
        nexter = None
        side = curPlayer.chair
        while True:
            print '444444444'
            side = self.getNextSide(side)
            print 'getNexter,side', side
            nexter = self.players[side]

            print 'getNexter1', nexter
            if nexter is curPlayer:
                return None

            print 'getNexter2', nexter.leaveGameStage
            if nexter.leaveGameStage in [0,1]:
                log(u'[getNexter] nexter[%s] side[%s].'\
                    %(nexter, side), LOG_LEVEL_RELEASE)
                break

        return nexter

    def getNextSide(self, curSide):
        return (curSide+1)%self.maxPlayerCount

    def getLeftPlayers(self, excludePlayers=()):
        return [player for player in self.players if (player and player not in excludePlayers and player.leaveGameStage == 0)]

    def isCanEndGame(self, curPlayer):
        """
        是否结束游戏，上层根据具体条件重写
        """
        return False

    def balance(self, isEndGame = False, isSave = True):
        """
        结算并结束游戏
        """
        log(u'[on balance]room[%s] curGameCount[%s] gameTotalCount[%s] isEndGame[%s] isSave[%s].'\
                %(self.roomId, self.curGameCount, self.gameTotalCount, isEndGame, isSave), LOG_LEVEL_RELEASE)
        self.doBeforeBalance()
        if not self.setEndTime:
            self.setEndTime = self.server.getTimestamp()
        if not self.gameEndTime:
            self.gameEndTime = self.server.getTimestamp()

        if not self.isUseRoomCards and self.curGameCount == 1 and not self.isDebug and not self.isParty and isSave:
            self.server.useRoomCards(self)

        #检测局数是否直接结束全部
        if self.curGameCount + 1 > self.gameTotalCount:
            log(u'[on balance]room[%s] curGameCount[%s] > gameTotalCount[%s].'\
                %(self.roomId, self.curGameCount, self.gameTotalCount), LOG_LEVEL_RELEASE)
            isEndGame = True

        #打包小局数据
        resp = poker_pb2.S_C_Balance()
        resp.isNormalEndGame = self.isGameEnd
        if isSave:
            for player in self.getPlayers():
                self.calcBalance(player)

        if self.stage != GAME_READY:
            self.fillCommonData(resp)
        for player in self.getPlayers():
            if self.stage != GAME_READY: #局间不显示单局结算数据
                userData = resp.setUserDatas.add()
                pbBalanceData(player, userData)
                self.fillBalanceData(player, userData)
                player.upTotalUserData()
            if isEndGame:
                totalUserData = resp.gameUserDatas.add()
                pbBalanceData(player, totalUserData)
                self.fillTotalBalanceData(player, totalUserData)
                totalUserData.roomSetting = self.ruleDescs
        self.oldBalanceData = copy.deepcopy(resp)
        log(u'[on balance] resp[%s]'%(resp), LOG_LEVEL_RELEASE)
        self.sendAll(resp)

        #每局数据存盘
        if isSave:
            self.server.savePlayerBalanceData(self, resp.setUserDatas)
            saveResp = poker_pb2.S_C_RefreshData()
            saveResp.result = True
            self.server.tryRefresh(self, player, saveResp)
            self.replayRefreshData = saveResp.SerializeToString()
            self.isSaveGameData = True
            self.gamePlayedCount += 1
        if isEndGame:
            if self.isSaveGameData:
                #总数据存盘
                log(u'[on balance]room[%s] save all data.'%(self.roomId), LOG_LEVEL_RELEASE)
                self.server.savePlayerTotalBalanceData(self, resp.gameUserDatas)
            self.removeRoom()
        else:
            #切换下一局
            self.resetSetData()
            self.isEnding = True
            self.stage = GAME_READY
            # self.onSetStart(self.players[OWNNER_SIDE])
            self.setCounter([self.dealerSide], self.balanceCounterMs, self.onGameStartTimeout)


    def onDissolveRoom(self, player):
        """
        玩家发起解散
        """
        if self.dissolvePlayerSide >= 0:
            log(u'[try dissolve game][error]side[%s] is dissolveing.'%(self.dissolvePlayerSide), LOG_LEVEL_RELEASE)
            return

        #非房主不能解散
        # if player.chair != OWNNER_SIDE:
            # log(u'[try dissolve game][error]nickname[%s] is not game master.'%(player.nickname), LOG_LEVEL_RELEASE)
            # return

        if self.stage == WAIT_START:
            log(u'[try dissolve game][error]error stage.', LOG_LEVEL_RELEASE)
            return

        self.dissolvePlayerSide = player.chair
        self.dissolve[player.chair] = True
        self.dissovedCounterMs = self.server.getTimestamp() + self.getDissolvedCounterMs()
        log(u'[try dissolve game]nickname[%s] room[%s].'%(player.nickname, self.roomId), LOG_LEVEL_RELEASE)
        # if self.maxPlayerCount <= 2:
            # self.dissovedCounterMs = 0
            # resp = baseProto_pb2.S_C_DissolveVoteResult()
            # resp.result = True
            # self.sendAll(resp)
            # self.dissolve = [None] * self.maxPlayerCount
            # self.dissolvePlayerSide = -1
            # log(u'[try dissolve vote]room[%s] dissolve succed for player count[%s].'%(self.roomId, self.maxPlayerCount), LOG_LEVEL_RELEASE)
            # self.endGame()
        # else:
        self.sendDissolveResult(player)

    def onDissolveVote(self, player, result):
        """
        解散投票
        """

        if self.dissolvePlayerSide < 0:
            log(u'[try dissolve vote][error]no one want to dissolve game.', LOG_LEVEL_RELEASE)
            return

        side = player.chair
        if self.dissolve[side] != None:
            log(u'[try dissolve vote][error]nickname[%s] is voted.'%(player.nickname), LOG_LEVEL_RELEASE)
            return

        self.dissolve[side] = result
        if self.dissolve.count(True) >= self.getDissolveSuccedNeedPlayerCount() or\
                self.dissolve.count(False) > self.getDissolveFailNeedPlayerCount():
            self.dissovedCounterMs = 0
            resp = baseProto_pb2.S_C_DissolveVoteResult()
            resp.result = result
            self.sendAll(resp)
            self.dissolve = [None] * self.maxPlayerCount
            self.dissolvePlayerSide = -1
            if result:
                log(u'[try dissolve vote]room[%s] dissolve succed.'%(self.roomId), LOG_LEVEL_RELEASE)
                self.isDissolveEnd = True
                self.endGame()
            else:
                log(u'[try dissolve vote]room[%s] dissolve failed.'%(self.roomId), LOG_LEVEL_RELEASE)
            return
        #依旧解散中，告知投票结果
        self.sendDissolveResult(player)

    def onReady2NextGame(self, player):
        """
        快速关闭结算页面，所有玩家都做了此操作后，马上开始下一小局
        """
        if not self.isEnding:
            log(u'[ready next]room[%s] game is not end.'%(self.roomId), LOG_LEVEL_RELEASE)
            return

        side = player.chair
        if side not in self.ready2NextGameSides:
            self.ready2NextGameSides.append(side)
        if len(self.ready2NextGameSides) >= self.maxPlayerCount:
            log(u'[ready next]room[%s] all ready.'%(self.roomId), LOG_LEVEL_RELEASE)
            self.ready2NextGameSides = []
            #马上开始下一局
            self.__resetCounter()
            self.onGameStart(self.players[OWNNER_SIDE])

    def doNextGame(self, player):
        self.ready2NextGameSides = []
        #马上开始下一局
        self.__resetCounter()
        self.onGameStart(self.players[OWNNER_SIDE])

    def onSetGps(self, player, gpsValue):
        """
        设置gps
        """
        self.side2gps[player.chair]=gpsValue

        resp = baseProto_pb2.S_C_Gps()
        for side, gps in self.side2gps.items():
            gpsData = resp.gpsDatas.add()
            gpsData.chair = side
            gpsData.gpsValue = gps
        self.sendAll(resp)

    def onJoinGame(self, player, resp, isSendMsg = True):
        """
        加入游戏
        """
        chair = self.getEmptyChair()
        assert chair != consts.SIDE_UNKNOWN
        player.chair = chair
        player.game = self

        self.server.savePlayerGameData(player, self.roomId)
        if not self.parentAg: #房间绑定代理商
            self.parentAg = player.parentAg
        self.playerCount += 1
        self.players[chair] = player

        joinResponse = baseProto_pb2.S_C_JoinRoom()
        joinResponse.info.headImgUrl = player.headImgUrl
        joinResponse.isFull = False
        pbPlayerInfo(joinResponse.info, self, player.chair)

        pbRoomInfo(resp.myInfo.roomInfo, self.server, self)
        pbPlayerInfo(resp.myInfo.selfInfo, self, player.chair, isNeedMyData = True)
        for p in self.players:
            if not p:
                continue
            _playerInfo = resp.myInfo.roomInfo.playerList.add()
            pbPlayerInfo(_playerInfo, self, p.chair)

        if self.getEmptyChair() == consts.SIDE_UNKNOWN: #满人
            joinResponse.isFull = True

            #打包全员初始数据保存回放
            saveResp = poker_pb2.S_C_RefreshData()
            saveResp.result = True
            self.server.tryRefresh(self, player, saveResp)
            self.replayRefreshData = saveResp.SerializeToString()
            self.doAfterRoomFull()

        if isSendMsg:
            self.sendOne(player, resp)
            self.sendExclude((player,), joinResponse)
            self.server.sendOthersOnlineState(player)

        self.server.userDBOnJoinGame(player, self)

    def onExitGame(self, player, sendMessage = True, byPlayer = False, isEndGame = False):
        """
        退出游戏
        """
        if not player or not player.game or player.game != self:
            return

        isOwnnerEnd = False #房主提前退出导致的游戏结束
        isDrop = False #是否断开玩家，只有离开当前game时才为true
        side = player.chair

        if (byPlayer and self.stage == WAIT_START) or isEndGame: #未开始前客户端主动退出，或者游戏结束
            isDrop = True
            log(u'[on exit]nickname[%s] is exit room[%s] in wait time.'%(player.nickname, self.roomId), LOG_LEVEL_RELEASE)
            if sendMessage:
                exitResp = baseProto_pb2.S_C_ExitRoom()
                exitResp.info.side = side
                exitResp.info.nickname = player.nickname
                self.sendExclude((player,), exitResp)
            self.players[side] = None
            self.playerCount -= 1
            #该情况下不记录重连信息，无法重连
            self.server.tryRmExitPlayerData(player, self)
            if not isEndGame and side == OWNNER_SIDE and not self.ownner: #开始前庄家退出T出全员解散
                log(u'[try dissolve game]game is not start and master[%s] is exit.'%(player.nickname), LOG_LEVEL_RELEASE)
                isOwnnerEnd = True
        else: #游戏中退出，需要记录重连信息
            log(u'[on exit]nickname[%s] is exit room[%s] in game time.'%(player.nickname, self.roomId), LOG_LEVEL_RELEASE)
            self.exitPlayers.append(side)
            robot = self.getRobot()
            self.setPlayerCopy(robot, player)
            self.server.saveExitPlayer(player, self)

            #发送离线状态
            # self.onLeaveGame(robot.chair)
            robot.isOnline = False
            _resp = baseProto_pb2.S_C_OnlineState()
            _resp.changeSide = player.chair
            _resp.isOnline = player.isOnline
            self.sendExclude((player,), _resp)

        player.chair = consts.SIDE_UNKNOWN
        player.game = None

        self.server.userDBOnExitGame(player, self, isDrop)

        if side == self.controlPlayerSide:
            for otherPlayer in self.getPlayers((robot,)):
                self.onExitGame(otherPlayer, sendMessage = False)
        if byPlayer and self.stage == WAIT_START:
            resp = baseProto_pb2.S_C_ExitRoomResult()
            resp.result = True
            self.sendOne(player, resp)
        if isOwnnerEnd:
            self.endGame(isNotStart = True)

    def setGMType2ValidCmdJudge(self):
        """
         GM类型到相应判断命令是否有效的方法的映射
        """
        self.validGMCommand = {
            GET_CARDS        :  self.validGetCards,
        }

    def sendGMError(self, player, errMsg):
        """
        """
        resp = baseProto_pb2.S_C_GMControl()
        resp.result = False
        resp.reason = errMsg
        self.sendOne(player, resp)

    def validGetCards(self, player, data):
        """
        检验GM命令是否有效
        """
        data = reCards.findall(data)
        if len(data) > self.dealMgr.setting['HAND_CARDS_COUNT']:
            self.sendGMError(player, ERR_MSG['lenErr'])
            return False
        for card in data:
            # if card not in self.dealMgr.poolCards:
            if data.count(card) > self.dealMgr.poolCards.count(card):
                log(u'valid data[%s] card[%s] poolCards[%s]'\
                    %(data, card, self.dealMgr.poolCards),LOG_LEVEL_RELEASE)
                self.sendGMError(player, ERR_MSG['cardErr'])
                return False
        return True

    # def validGetDealer(self, player, data):
        # """
        # 检验GM命令是否有效
        # """
        # data = int(data)
        # if data >= len(self.players) or data < 0:
            # self.sendGMError(player, ERR_MSG['sideErr'])
            # return False
        # return True

    def onGMControl(self, player, type, data):
        """
        """
        if not self.dealMgr.ctrlTypes.has_key(type):
            self.sendGMError(player, ERR_MSG['typeErr'])
            log(u'[try control]control failed, nickname[%s] type[%s] data[%s].'\
                %(player.nickname, type, data), LOG_LEVEL_RELEASE)
            return
            
        validCommand = self.validGMCommand[type](player, data)
        if not validCommand:
            log(u'[try control]control failed, nickname[%s] type[%s] data[%s].'\
                %(player.nickname, type, data), LOG_LEVEL_RELEASE)
            return

        self.dealMgr.ctrlTypes[type](player.chair, data)

        resp = baseProto_pb2.S_C_GMControl()
        resp.result = True
        resp.reason = ''
        self.sendOne(player, resp)
        log(u'[try control]control succeed, nickname[%s] type[%s] data[%s].'\
            %(player.nickname, type, data), LOG_LEVEL_RELEASE)

    def onTalk(self, emoticons, side, voiceNum, duration): #发表情和语音
        log(u'[player talk]room[%s] side[%s] talk[%s] [%s] [%s].'\
            %(self.roomId, side, emoticons, voiceNum, duration), LOG_LEVEL_RELEASE)
        resp = baseProto_pb2.S_C_Talk()
        resp.talkSide = side
        if emoticons:
            resp.emoticons = emoticons
        if voiceNum:
            resp.voice = voiceNum
        if duration:
            resp.duration = duration
        # self.sendExclude((self.players[side],), resp)
        self.sendAll(resp)

#++++++++++++++++++++ 响应消息回调 end ++++++++++++++++++++

#++++++++++++++++++++ 麻将工具函数 ++++++++++++++++++++

    def removeRoom(self):
        # statics.dig_game_end(self)
        for player in self.getPlayers():
            self.onExitGame(player, isEndGame = True, sendMessage = False)
        if self.playerCount <= 0: #房间无人则移除房间
            log(u'[try end game] nobody in room[%s].'%(self.roomId), LOG_LEVEL_RELEASE)
            self.server.onRemoveGame(self)
        else:
            log(u'[try end game][error]player in room[%s], players[%s], playerCount[%s]'%(self.roomId, self.getPlayers(), self.playerCount), LOG_LEVEL_RELEASE)

    def endGame(self, isNotStart = False):
        """
        结束游戏（主动解散房间）
        """
        #发送报表
        self.server.dynamic.endGame(self, self.server)
        if isNotStart:
            for player in self.getOnlinePlayers((self.players[OWNNER_SIDE],)):
                try:
                    messsageStr = '房主退出，游戏解散'.decode('utf-8')
                    player.drop(messsageStr, type = 2)
                except Exception as e:
                    print 'drop error e:%s'%(e)
                    print 'drop nickname%s'%(player.nickname)
            self.removeRoom()
        else:
            self.balance(isEndGame = True, isSave = False)


    def sendDissolveResult(self, player):
        """
        发送解散投票结果
        """
        resp = baseProto_pb2.S_C_DissolveVote()
        for otherPlayer in self.getPlayers():
            voteData = resp.vote.add()
            side = otherPlayer.chair
            if self.dissolve[side] != None:
                voteData.result = self.dissolve[side]
            voteData.nickname = otherPlayer.nickname
        resp.nickname =  self.players[self.dissolvePlayerSide].nickname
        resp.dissolveSide = self.dissolvePlayerSide
        resp.waitTime = max(int((self.dissovedCounterMs - self.server.getTimestamp()) / 1000), 0)
        self.sendAll(resp)

    def setPlayerCopy(self, robot, player):
        """
        设置拷贝了玩家数据的机器人
        """
        robot.game = self
        robot.handleMgr = player.handleMgr
        robot.handleMgr.player = robot
        robot.account = player.account
        robot.nickname = player.nickname
        robot.chair = player.chair
        robot.ip = player.ip
        robot.region = player.region
        robot.sex = player.sex
        robot.headImgUrl = player.headImgUrl
        robot.uid = player.uid
        robot.lastOnlineState = player.lastOnlineState
        robot.isOnline = player.isOnline

        robot.totalGameScore = player.totalGameScore
        robot.totalWinCount = player.totalWinCount

        robot.curGameScore = player.curGameScore
        robot.leaveGameStage = player.leaveGameStage
        robot.lastDiscard = player.lastDiscard
        robot.isActioned = player.isActioned
        robot.isUpdated = player.isUpdated
        if player.controlPlayer != player:
            robot.controlPlayer = player.controlPlayer
        self.players[player.chair] = robot

#++++++++++++++++++++ 通用麻将工具函数 end ++++++++++++++++++++

#++++++++++++++++++++ 通用房间服务工具 ++++++++++++++++++++
    def sendOne(self, player, protocol_obj):
        if player.chair not in self.exitPlayers:
            log(u'[try send]account[%s]'%(player.nickname), LOG_LEVEL_RELEASE)
            self.server.sendOne(player, protocol_obj)
        self.saveSendData(protocol_obj, peer = player)

    def sendExclude(self, excludePlayers, protocol_obj):
        log(u'[try send]game[%s] exit player %s'%(self.roomId, self.exitPlayers), LOG_LEVEL_RELEASE)
        self.server.send(self.getOnlinePlayers(excludePlayers), protocol_obj)
        # self.server.send([p for p in self.__getPlayers() if p not in excludePlayers], protocol_obj)

    def sendAll(self, protocol_obj):
        log(u'[try send]game[%s] exit player %s'%(self.roomId, self.exitPlayers), LOG_LEVEL_RELEASE)
        self.server.send(self.getOnlinePlayers(), protocol_obj)
        self.saveSendData(protocol_obj)

    def saveSendData(self, protocol_obj, peer = None): #保存发包
        name = protocol_obj.__class__.__name__
        code = self.server.senderMgr._cmds[name].msg_code
        data = protocol_obj.SerializeToString()
        print 'saveSendData,name,code', name, code

        saveResp = replay4proto_pb2.ActionData()
        saveResp.msgCode = code
        saveResp.replayMessage = data
        saveResp.timestamp = self.server.getTimestamp()

        if name in self.saveSendAllProtoList:
            self.replayData.append(saveResp)
        elif name == SAVE_SEND_END_PROTO:
            protoCopy = copy.deepcopy(protocol_obj)
            protoLen = len(protoCopy.gameUserDatas)
            for index in xrange(protoLen):
                protoCopy.gameUserDatas.remove(protoCopy.gameUserDatas[protoLen - 1 - index])
            saveResp.replayMessage = protoCopy.SerializeToString()
            self.replayData.append(saveResp)
        elif peer and name in SAVE_SEND_PROC_PROTO_LIST:
            if not self.replayinitCardsData: #标记发牌时间
                self.replayData.append(saveResp)
            resp = replay4proto_pb2.TilesData()
            resp.side = peer.chair
            resp.tiles = data
            self.replayinitCardsData.append(resp)
        elif peer and name in self.saveSendOneProtoList and (peer.chair in self.countPlayerSides):
            self.replayData.append(saveResp)

        #print 'replayData', self.replayData
        if name in self.getResetProtoList():
            self.resetReplayData.append(saveResp)
            print 'resetReplayData', self.resetReplayData

    def getResetProtoList(self):
        return []

    def doResetReplayData(self):
        """
        重置回放数据
        """
        log(u'[doResetReplayData] replayinitCardsData[%s]' \
            %(self.replayinitCardsData), LOG_LEVEL_RELEASE)
        self.replayinitCardsData = []
        log(u'[doResetReplayData] resetReplayData[%s] replayData[%s]' \
            %(self.resetReplayData, self.replayData), LOG_LEVEL_RELEASE)
        for data in self.resetReplayData:
            if data in self.replayData:
                self.replayData.remove(data)
        self.resetReplayData = []

    def getEmptyChair(self):
        """
        return an empty side range[0:maxPlayerCount-1]
        return -1 for full
        """
        for chair, player in enumerate(self.players):
            if not player:
                return chair

        return consts.SIDE_UNKNOWN

    def getOnlinePlayers(self, excludePlayers=()):
        return [player for player in self.players if (player and player not in excludePlayers and player.chair not in self.exitPlayers)]

    def getPlayers(self, excludePlayers=()):
        return [player for player in self.players if (player and player not in excludePlayers)]

    def getPlayers2sides(self, players = ()):
        sides = []
        for player in players:
            sides.append(player.chair)
        return sides

    def setCounter(self, countPlayers, timeMs, timeoutCallback, params = ()):
        """
        设置当前计时器及超时回调
        """
        log(u'[set counter]countPlayers[%s] timeMs[%s] timeoutCallback[%s] params[%s].'\
                    %(countPlayers, timeMs, timeoutCallback.__name__, params), LOG_LEVEL_RELEASE)
        self.countPlayerSides = countPlayers
        self.countStartTime = self.server.getTimestamp()
        self.counterMs = timeMs
        self.counterCallback = timeoutCallback
        self.counterParams = params

    def doCounter(self, timestamp):
        """
        倒计时处理
        """
        if self.counterCallback and timestamp - self.countStartTime > self.counterMs:
            countStartTime = self.countStartTime
            log(u'[do counter]room[%s] counterCallback[%s] counterParams[%s].'\
                    %(self.roomId, self.counterCallback.__name__, self.counterParams), LOG_LEVEL_RELEASE)
            self.counterCallback(*self.counterParams)
            #倒计时变更则增加了新计时器，不重置
            if countStartTime == self.countStartTime:
                self.__resetCounter()

    def __resetCounter(self):
        """
        重置倒计时
        """
        self.counterCallback = None
        self.countStartTime = 0
        self.counterMs = None
        self.counterParams = None
        # self.dealer = None

    def checkCounter(self, player):
        """
        """
        if player.chair not in self.countPlayerSides:
            log(u'[check counter][error]error counter[%s] need counter[%s].'%(player.chair, self.countPlayerSides), LOG_LEVEL_RELEASE)
            return False
        return True

    def checkStage(self, stage):
        """
        """
        if self.stage != stage:
            log(u'[check stage][error]error stage[%s] need stage[%s].'%(self.stage, stage), LOG_LEVEL_RELEASE)
            return False
        return True

    def onTick(self, timestamp):
        """
        房间服务心跳
        """
        #倒计时及回调触发
        self.doCounter(timestamp)
        self.dealPing(timestamp)

        if self.dissovedCounterMs and timestamp > self.dissovedCounterMs:
            self.onDissolveVoteTimeout()
            self.dissovedCounterMs = 0

        if self.stage == WAIT_START and not self.ownner:
            if self.players[OWNNER_SIDE] and self.players[OWNNER_SIDE].isOnline == False:
                if not self.dissoved4GameNotStartMs:
                    self.dissoved4GameNotStartMs = self.server.getTimestamp()
                waitingTime = PUBLIC_ROOM_GAME_NOT_START_END_TIME
                if self.isHidden:
                    waitingTime = GAME_NOT_START_END_TIME
                if self.server.getTimestamp() - self.dissoved4GameNotStartMs > waitingTime:
                    if OWNNER_SIDE not in self.exitPlayers:
                        messsageStr = '长时间未开始游戏，房间已自动解散'.decode('utf-8')
                        self.players[OWNNER_SIDE].drop(messsageStr, type = 2)
                    log(u'[on tick]room[%s] ownner leave game too long.'%(self.roomId), LOG_LEVEL_RELEASE)
                    self.endGame(isNotStart = True)
            else:
                self.dissoved4GameNotStartMs = 0
        elif self.ownner:
            if self.playerCount == 0:
                waitingTime = PUBLIC_ROOM_GAME_NOT_START_END_TIME
                if self.isHidden:
                    waitingTime = OTHER_TYPE_GAME_NOT_START_END_TIME
                if not self.dissoved4GameNotStartMs:
                    self.dissoved4GameNotStartMs = self.server.getTimestamp()
                    self.server.saveOtherRoomEndTime(self, self.dissoved4GameNotStartMs + waitingTime)
                if self.server.getTimestamp() - self.dissoved4GameNotStartMs > waitingTime:
                    log(u'[on tick]room[%s] nobody too long.'%(self.roomId), LOG_LEVEL_RELEASE)
                    self.server.removeOtherGameData(self)
                    self.endGame(isNotStart = True)
            else:
                self.dissoved4GameNotStartMs = 0

    def dealPing(self, timestamp):
        """
        """
        for player in self.players:
            if not player:
                continue
            #log(u'[dealPing start] account[%s] isOnline[%s] lastOnlineState[%s]'%(player.nickname, player.isOnline,player.lastOnlineState), LOG_LEVEL_RELEASE)
            if timestamp - player.lastPingTimestamp > PING_INTERVAL_TICK:
                player.isOnline = False
            if player.isOnline != player.lastOnlineState:
                resp = baseProto_pb2.S_C_OnlineState()
                resp.changeSide = player.chair
                resp.isOnline = player.isOnline
                self.sendExclude((player,), resp)
                player.lastOnlineState = player.isOnline
                #log(u'[dealPing] side[%s] isOnline[%s]'%(resp.changeSide, resp.isOnline), LOG_LEVEL_RELEASE)

#++++++++++++++++++++ 通用房间服务工具 end ++++++++++++++++++++

#++++++++++++++++++++ 房间服务可重写接口 ++++++++++++++++++++

    def getDiscardCounterMs(self):
        """
        出牌倒计时(毫秒)，需要则重写
        """
        return WAIT_BACK_TIME

    def getActionCounterMs(self):
        """
        吃碰杠胡倒计时(毫秒)，需要则重写
        """
        return WAIT_BACK_TIME

    def getBalanceCounterMs(self):
        """
        结算倒计时(毫秒)，需要则重写
        """
        return WAIT_BACK_TIME

    def getDissolvedCounterMs(self):
        """
        解散倒计时(毫秒)，需要则重写
        """
        return 5 * 60 * 1000

    def getMaxPlayerCount(self):
        """
        返回房间最大玩家数，上层可重写
        """
        return 5

    def getGameTotalCount(self):
        """
        返回默认最大小局数
        """
        return 8

    def getDissolveSuccedNeedPlayerCount(self):
        """
        同意人数满足，解散成功
        """
        return self.maxPlayerCount - self.getDissolveFailNeedPlayerCount()

    def getDissolveFailNeedPlayerCount(self):
        """
        不同意人数满足，解散失败
        默认值为房间人数减去解散成功需要的人数
        """
        return max(self.maxPlayerCount / 2 + self.maxPlayerCount % 2 - 1, 1)

    def initByRuleParams(self, ruleParams, haveBaseScore=True):
        """
        Abstract interface for parse rule parameters
        """
        params = eval(ruleParams)

        totalCount = int(params[-3])
        if totalCount:
            self.gameTotalCount = totalCount
            self.ruleDescs.append("%s局"%(self.gameTotalCount))

        self.needRoomCards = int(params[-2])
        self.baseScore = max(int(params[-1]), 1)
        if haveBaseScore:
            self.ruleDescs.append("底分%s"%(self.baseScore))

        self.ruleDescs = "-".join(self.ruleDescs).decode('utf-8')

        log(u'[get gameRules]room[%s] ruleParams[%s] ruleTxt[%s]'%(self.roomId, params, self.ruleDescs),LOG_LEVEL_RELEASE)

    def getDealer(self):
        """
        返回庄家座位号
        """
        return -1

    def getDealManager(self):
        """
        返回发牌器
        """
        return DealMgr(self)

    def getRobot(self):
        """
        获得使用的玩家类，用于设置掉线后放置玩家的拷贝
        """
        return CommonPlayer()

    def getSaveSendAllProtoList(self):
        """
        获得需要保存回放的sendAll的协议列表
        """
        return []

    def getSaveSendOneProtoList(self):
        """
        获得需要保存回放的sendOne的协议列表
        只保存当前行动玩家的，比如S_C_DrawCards只会保存发给摸牌的那个人的那条，不会保存发给别人的那条
        """
        return []

    def getActionedCards(self, resp, side, curPlayerSide):
        """
        返回玩家已有操作的数据抽象，用于重连刷新
        """

        _player = self.players[side]
        if _player.leaveGameStage != 0:
            resp.extend([]) #手牌列表
        else:
            cards = _player.handleMgr.getCards()
            if side != curPlayerSide:
                cards = [''] * len(cards)
            cardsStr = ','.join(cards)
            resp.extend([cardsStr]) #手牌列表

        return resp

    def doAfterRoomFull(self):
        """
        人满后操作
        """
        pass

    def doBeforeGameStart(self):
        """
        """
        pass

    def doBeforeSetStart(self):
        """
        """
        pass

    def onDoActionTimeout(self):
        """
        """
        return

    def onDiscardTimeout(self, player):
        """
        """
        return
        self.onDiscard(player, player.handleMgr.getLastCard())

    def onDissolveVoteTimeout(self):
        """
        """
        for player in self.getPlayers():
            self.onDissolveVote(player, True)

    def onGameStartTimeout(self):
        """
        """
        self.onGameStart(self.players[OWNNER_SIDE])

    def getPartyRoomRule(self):
        """
        娱乐模式规则
        """
        return []

    def hasDealerCount(self):
        """
        是否存在连庄
        """
        return False

    def _dealCardsData(self, side, cardList, player, action):
        cards = player.handleMgr.packActionCards(action, cardList)
        cardData = ','.join(cards)
        cardsData = '%s;%s'%(side, cardData)
        return cardsData

    def fillCommonData(self,resp):
        # commonData = resp.gameCommonDatas.add()
        # commonData.datas.extend([])
        pass

    def fillBalanceData(self, player, balanceData):
        """
        填充玩家小局结算数据，详见mahjong.proto中BalanceData中的
        desc
        score
        times
        cards
        """
        balanceData.descs.extend([])
        balanceData.score = 0
        balanceData.cards.extend([])
        balanceData.isHu = False

    def fillTotalBalanceData(self, player, balanceData):
        """
        填充玩家总结算数据，详见mahjong.proto中BalanceData中的
        score
        times
        """
        balanceData.score = 0
        balanceData.descs.extend([])

    def calcBalance(self, player):
        """
        每小局结算算分接口
        """
        pass

    def doBeforeBalance(self):
        """
        结算前重写逻辑
        """
        pass

#++++++++++++++++++++ 房间服务可重写接口 end ++++++++++++++++++++

