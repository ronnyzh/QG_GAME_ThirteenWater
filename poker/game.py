# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: game logic
"""

from common.common_game import CommonGame
from common import poker_pb2
from common import replay4proto_pb2
import thirteenWater_poker_pb2
from common.card_define import *
from common.log import *
from common.protocols.poker_consts import *

from player import Player
from deal import *
# from tw_arith import *
from lj_tw_arith import *
from consts import *

import copy
import random
from common.pb_utils import *

import private_mahjong_pb2


#最多几人
MaxPlayer = 4

class Game(CommonGame):
    def __init__(self, server, ruleParams, needInit = True, roomId = 0):
        self.initRuleDict()
        super(Game, self).__init__(server, ruleParams, needInit = needInit, roomId = 0)
        self.arrangeCounterMs = self.getArrangeCounterMs()
        self.setType2SpecialScore()
        self.gameStage = NO_START
        self.okList = [0]*self.maxPlayerCount

    def resetSetData(self):
        '''
        每局数据初始化
        '''
        super(Game,self).resetSetData()
        # self.winList = []
        # self.isExistBigger = False
        # self.disCount = 0
        # self.wrapSide = -1
        # self.left1Sides = []
        # self.wildCardList = []
        self.hasMultipleSides = []
        self.hasArrangedSides = [0]*self.maxPlayerCount
        self.ranksDict = {0:[], 1:[], 2:[], 3:[]}
        self.shootDict = {}
        self.speSideNTypes = []
        self.comSideNIns = {HEAD_PIER:[], MIDDLE_PIER:[], TAIL_PIER:[]}
        self.comSides = []
        self.compareResp = None
        self.startTime = 0
        self.isNoDeal = True
        

    def initRuleDict(self):
        """
        规则字段映射
        """
        self.canChoose = {
            HAS_JOKER       :    self.setHasJoker,
            HAS_HORSE       :    self.setHasHorse,
            SHOOT_ADD_1     :    self.setShootAdd1,
            FU_QING         :    self.setFuQing,
            HAS_DO_DEALER   :    self.setHasDoDealer,
        }

    def setPlayerCount(self, switch):
        self.pCountNo = switch
        self.maxPlayerCount = MaxPlayer - switch
        self.ruleDescs.append("%s人"%(self.maxPlayerCount))
        self.players = [None]*self.maxPlayerCount
        self.dissolve = [None] * self.maxPlayerCount

    def setPlayWay(self, switch):
        """
        设置玩法
        """
        self.playWay = switch
        if switch == NORMAL:
            self.ruleDescs.append('普通玩法')
        else:
            self.ruleDescs.append('多一色')

    def setHorseCard(self, switch):
        if self.isNoHorse():
            return
        self.horseCard = switch
        if switch == DIAMOND_A_NO:
            self.ruleDescs.append('方块A')
        elif switch == DIAMOND_5_NO:
            self.ruleDescs.append('方块5')
        elif switch == DIAMOND_10_NO:
            self.ruleDescs.append('方块10')

    def setMultiple(self, switch):
        """
        设置倍数
        """
        if self.isNoDoDealer():
            return

        if switch == 0:
            self.ruleDescs.append('1倍')
            self.multipleNo = MULTIPLE_1
        elif switch == 1:
            self.ruleDescs.append('2倍')
            self.multipleNo = MULTIPLE_2
        elif switch == 2:
            self.ruleDescs.append('3倍')
            self.multipleNo = MULTIPLE_3

    def isNoHorse(self):
        return self.hasHorse == False

    def isNoDoDealer(self):
        return self.hasDoODealer == False

    def setHasJoker(self):
        self.hasJoker = True
        self.ruleDescs.append('带鬼')
        # pass

    def setHasHorse(self):
        self.hasHorse = True
        self.ruleDescs.append('带马')

    def setShootAdd1(self):
        self.shootAdd1 = True
        self.ruleDescs.append('打枪+1')

    def setFuQing(self):
        self.Fuqing = True
        self.ruleDescs.append('福清玩法')

    def setHasDoDealer(self):
        self.hasDoODealer = True
        self.ruleDescs.append('房主坐庄')

    def dealMultiselect(self, paramList):
        log(u'[dealMultiselect] room[%s] paramList[%s]'%(self.roomId, paramList),LOG_LEVEL_RELEASE)
        curList = paramList[:]
        if HAS_DO_DEALER in paramList and SHOOT_ADD_1 not in paramList:
            curList.append(SHOOT_ADD_1)
            curList.sort()
        log(u'[dealMultiselect] curList[%s]'%(curList),LOG_LEVEL_RELEASE)
        return curList

    # def initByRuleParams(self,ruleParams):
    #     """
    #     初始化游戏设置参数
    #     """
    #     self.pCountNo = 0
    #     self.playWay = NORMAL #普通玩法
    #     self.hasJoker = False #是否有鬼
    #     self.hasHorse = False #是否有马
    #     self.shootAdd1 = False #打枪+1
    #     self.Fuqing = False #福清玩法
    #     self.hasDoODealer = False #房主坐庄
    #     self.multipleNo = MULTIPLE_1 #倍数序号
    #     # self.multiple = 1
    #     self.horseCard = -1 #马数
    #
    #     params = eval(ruleParams)
    #     log(u'[initByRuleParams] room[%s] params[%s] ruleParams[%s]'%(self.roomId, params, ruleParams),LOG_LEVEL_RELEASE)
    #     self.ruleDescs = []
    #
    #     self.setPlayerCount(params[0])
    #     self.setPlayWay(params[1])
    #
        # multiselectList = self.dealMultiselect(params[2])
        # for num in multiselectList:
        #     self.canChoose[num]()
    #
    #     self.setHorseCard(params[3])
    #     self.setMultiple(params[4])
    #
    #     self.extendStr = '%s,%s,%s,%s,%s,%s,%s,%s,%s'%(self.pCountNo, self.playWay, self.hasJoker, 
    #         self.hasHorse, self.shootAdd1, self.Fuqing, self.hasDoODealer, self.horseCard, self.multipleNo)
    #
    #     super(Game, self).initByRuleParams(ruleParams, False)

    def initByRuleParams(self, ruleParams):
        """
        初始化游戏设置参数
        """
        self.pCountNo = 0
        self.playWay = NORMAL #普通玩法
        self.hasJoker = False #是否有鬼
        self.hasHorse = False #是否有马
        self.shootAdd1 = False #打枪+1
        self.shootAdd = False #是否开启打枪玩法
        self.isCanAllShoot = False #全垒打
        self.Fuqing = False #福清玩法
        self.hasDoODealer = False #房主坐庄
        self.multipleNo = MULTIPLE_1 #倍数序号
        self.specialCards_x2 = False  # 特殊牌型翻倍
        self.sixPairs_x2 = False  # 六对半牌型带四条翻倍
        # self.multiple = 1
        self.horseCard = -1 #马数
        params = eval(ruleParams)
        log(u'[initByRuleParams] room[%s] params[%s] ruleParams[%s]' % (self.roomId, params, ruleParams), LOG_LEVEL_RELEASE)
        self.ruleDescs = []

        self.banInteraction = False


        playerCount = params[0]
        self.pCountNo = playerCount
        self.maxPlayerCount = MaxPlayer - playerCount
        self.ruleDescs.append("%s人"%(self.maxPlayerCount))
        self.players = [None]*self.maxPlayerCount
        self.dissolve = [None] * self.maxPlayerCount

        if params[1] == 0:
            self.baseScore = 2
        elif params[1] == 1:
            self.baseScore = 3
        elif params[1] == 2:
            self.baseScore = 5
        elif params[1] == 3:
            self.baseScore = 10
        self.ruleDescs.append("%s分" % (self.baseScore))

        if 0 in params[2]:
            self.shootAdd = True
            self.ruleDescs.append('打枪')
        if 1 in params[2]:
            self.isCanAllShoot = True
            self.ruleDescs.append('全垒打')
        if 2 in params[2]:
            self.banInteraction=True
            self.ruleDescs.append("禁用互动功能")

        if 3 in params[2]:
            self.specialCards_x2 = True
            self.ruleDescs.append('报到牌型*2')

        if 4 in params[2]:
            self.sixPairs_x2 = True
            self.ruleDescs.append('六对半牌型带四条*2')

        self.extendStr = '%s,%s,%s,%s,%s,%s,%s,%s,%s'%(self.pCountNo, self.playWay, self.hasJoker,
            self.hasHorse, self.shootAdd1, self.Fuqing, self.hasDoODealer, self.horseCard, self.multipleNo)

        totalCount = int(params[-3])
        if totalCount:
            self.gameTotalCount = totalCount
            self.ruleDescs.append("%s局"%(self.gameTotalCount))

        self.needRoomCards = int(params[-2])
        # self.baseScore = max(int(params[-1]), 1)
        self.ruleDescs.append("底分%s"%(self.baseScore))

        self.ruleDescs = "-".join(self.ruleDescs).decode('utf-8')

        log(u'[get gameRules]room[%s] ruleParams[%s] ruleTxt[%s]'%(self.roomId, params, self.ruleDescs),LOG_LEVEL_RELEASE)


    def calcBalance(self, player):
        """
        每小局结算算分接口
        """
        return

    def fillBalanceData(self, player, balanceData):
        """
        客户端显示规则根据发送的balanceData.descs组装每条play的结算信息字串
        如：海南麻将
        player.getBalanceDescs()返回类似：
        ['缺门','掐张']这样的结算描述给客户端组装显示
        将输赢分数/玩家手牌信息 填充到score/cards字段
        ['#chow1#a1,a2,a3']
        """

        type = player.getSpecialType()
        if type > FIVE_HEADS:
            scoreDatas = [str(player.tmpGameScore)]
        else:
            pierTotalScore = player.pierTotalScore
            scoreDatas = [str(sum(pierTotalScore[pierNo])) for pierNo in PIER_LIST]
        balanceData.descs.extend(player.getBalanceDescs())
        balanceData.score = player.curGameScore
        balanceData.cards.extend(player.perCards)
        balanceData.times.extend(player.perPierType)
        balanceData.extend.extend(scoreDatas)
        # balanceData.isWin = player.isWin

    def fillTotalBalanceData(self, player, balanceData):
        """
        客户端显示规则根据发送的balanceData.descs组装每条play的结算信息字串
        如：海南麻将
        player.getBalanceDescs()返回类似：
        ['无噶','点炮','庄闲','1连庄']这样的结算描述给客户端组装显示
        将输赢分数/玩家手牌信息 填充到score/cards字段
        ['#chow1#a1,a2,a3']
        """
        balanceData.score = player.totalGameScore
        balanceData.descs.extend(player.packTotalBalanceDatas())

    def fillCommonData(self,resp):
        commonData = resp.gameCommonDatas.add()
        commonData.datas.extend(self.getCommonData())
        commonData.extendData.extend(self.getCommonExtendData())

    def getCommonExtendData(self):
        return []

    def getCommonData(self):
        return []

    def getDealManager(self):
        """
        返回发牌器
        """
        return DealMange(self)

    def getRobot(self):
        """
        获得使用的玩家类，用于设置掉线后放置玩家的拷贝
        """
        return Player()

    def getBalanceCounterMs(self):
        """
        结算倒计时(毫秒)，需要则重写
        """
        return 30000

    def getSaveSendAllProtoList(self):
        """
        获得需要保存回放的sendAll的协议列表
        """
        return ['S_C_Compare', 'S_C_MultipleResult']

    def setGMType2ValidCmdJudge(self):
        # GM类型到相应判断命令是否有效的方法的映射
        super(Game, self).setGMType2ValidCmdJudge()

    def doBeforeBalance(self):
        """
        结算前重写逻辑
        """
        pass

    def getDealer(self):
        """
        返回庄家座位号
        """
        # if self.lastWinSide != -1:
            # return self.lastWinSide
        if self.hasDoODealer:
            return OWNNER_SIDE
        return -1

    def doAfterSetStart(self):
        self.gameStage = CHOOSE_MULTIPLE_S
        if self.hasDoODealer:
            dealer = self.players[self.dealerSide]
            dealer.isDealer = True
            resp = thirteenWater_poker_pb2.S_C_SetMultiple()
            resp.canChoose.extend(self.getCanChooseMultiple())
            self.sendAll(resp)
            return

        super(Game, self).doAfterSetStart()

    def getCanChooseMultiple(self):
        return xrange(1, 4-self.multipleNo)

    def onSetMultiple(self, player, multiple):
        if player.multiple == 0 and not player.isDealer:
            player.multiple = multiple
            self.hasMultipleSides.append(player.chair)
            resp = thirteenWater_poker_pb2.S_C_MultipleResult()
            self.fillMultipleResult(player, resp)
            self.sendAll(resp)

        if self.isAllSelectedMultiple() and self.isNoDeal:
            self.isNoDeal = False
            super(Game, self).doAfterSetStart()

    def isAllSelectedMultiple(self):
        return len(self.hasMultipleSides) == self.maxPlayerCount-1

    def fillMultipleResult(self, player, resp):
        resp.side = player.chair
        resp.multiple = player.multiple
        log(u'[fillMultipleResult] room[%s] resp[%s].'%(self.roomId, resp), LOG_LEVEL_RELEASE)

    def getSixPairsScore(self, handleCards):
        """
        获取 6 对半的分数
        :param handleCards:
        :return:
        """
        kindDict = dict()
        fourKind = 0
        log('六对半 %s' % handleCards, LOG_LEVEL_RELEASE)
        for kind in handleCards:
            if kind[0] not in kindDict:
                kindDict[kind[0]] = 1
            else:
                kindDict[kind[0]] += 1
                if kindDict[kind[0]] >= 4:
                    fourKind += 1

        log('四条出现的情况 %s' % kindDict, LOG_LEVEL_RELEASE)
        if fourKind == 1:
            typeScore = self.getSpecialScore(SIX_PAIRS, -1) * 2
        elif fourKind == 2:
            typeScore = self.getSpecialScore(SIX_PAIRS, -1) * 2 * 2
        elif fourKind == 3:
            typeScore = self.getSpecialScore(SIX_PAIRS, -1) * 2 * 2 * 2
        else:
            typeScore = self.getSpecialScore(SIX_PAIRS, -1)

        return typeScore

    def deal(self, isReDeal = False):
        """
        发牌处理
        """
        self.dealMgr.deal()
        eachCards = self.dealMgr.getEachHands()

        resp = thirteenWater_poker_pb2.S_C_NewDealCards()
        self.startTime = self.server.getTimestamp()
        resp.timestamp = self.startTime
        for player, handleCards in zip(self.getPlayers(), eachCards):
            log(u'[deal]room[%s] nickname[%s] handleCards%s.'\
                %(self.roomId, player.nickname, handleCards), LOG_LEVEL_RELEASE)
            player.setHandleCards(handleCards)
            #客户端的牌值为逗号分隔的字串
            playerResp = copy.deepcopy(resp)
            playerResp.cards = ','.join(player.handleMgr.cards)
            playerResp.defultCards = ','.join(player.defaultCards)
            type = player.getSpecialType()
            playerResp.specialType = type
            playerResp.typeScore = self.getSpecialScore(type, -1)
            if type == SIX_PAIRS and self.sixPairs_x2:
                playerResp.typeScore = self.getSixPairsScore(handleCards)
            # playerResp.typeScore = self.getSpecialScore(type, -1)
            log(u'[deal]room[%s] playerResp[%s].'%(self.roomId, playerResp), LOG_LEVEL_RELEASE)
            self.sendOne(player, playerResp)

        self.doAfterDeal()

    def doAfterDeal(self):
        """
        发牌后操作
        """
        self.gameStage = DEALING_E
        self.setCounter([0], self.arrangeCounterMs, self.onArrangeTimeout)
        # self.dealDefaultType()
        return

    def onArrangedCards(self, player, cards, cardTypes):
        if player.arranged:
            log(u'[onArrangedCards] error: already arranged.', LOG_LEVEL_RELEASE)
            return
        player.arranged = True
        isValid = player.handleMgr.checkCardsType(cards, cardTypes)
        log(u'[onArrangedCards] room[%s] isValid[%s].'%(self.roomId, isValid), LOG_LEVEL_RELEASE)
        _side = player.chair
        self.hasArrangedSides[_side] = 1
        if not isValid:
            player.handleMgr.checkCardsType(player.defaultCards, player.defaultType)
        resp = thirteenWater_poker_pb2.S_C_ArrangedCards()
        resp.side = _side
        resp.SpecialType = 1 if player.handleMgr.specialType else 0
        self.sendAll(resp)
        log(u'[onArrangedCards] hasArrangedSides[%s].'%(self.hasArrangedSides), LOG_LEVEL_RELEASE)
        if 0 not in self.hasArrangedSides:
            self.doCompare()

    def onGetArrangedCards(self, player):
        if player.arranged and self.gameStage < COMPARE_S:
            resp = thirteenWater_poker_pb2.S_C_MyArrangedCards()
            resp.side = player.chair
            curPerCards = player.perCards
            if len(curPerCards) == 1:
                print '1111----'
                cardStr = curPerCards[0]
                curPerCards = [cardStr[0:8], cardStr[9:23], cardStr[24:38]]
            log(u'[onGetArrangedCards] room[%s] curPerCards[%s].'%(self.roomId, curPerCards), LOG_LEVEL_RELEASE)
            resp.cards.extend(curPerCards)
            resp.cardTypes.extend(player.perPierType)
            log(u'[onGetArrangedCards] room[%s] resp[%s].'%(self.roomId, resp), LOG_LEVEL_RELEASE)
            self.sendOne(player, resp)
        else:
            log(u'[onGetArrangedCards] room[%s],error: arranged[%s] gameStage[%s].' 
                %(self.roomId, player.arranged, self.gameStage), LOG_LEVEL_RELEASE)

    def setType2SpecialScore(self):
        deltaScore = 0
        if self.Fuqing:
            deltaScore = 1
        #至尊青龙分数修改+108分(原104)；
        #一条龙分数修改为+13分(原52)；
        #六对半分数修改为+6分；
        self.type2Score = {
            THREE_FLUSH            :        6-deltaScore,  # 三同花
            THREE_STRAIGHT         :        6-deltaScore,  # 三顺子
            SIX_PAIRS              :        12-deltaScore,  # 六对半
            FIVE_PAIRS_A_TRIPLET   :        6,   # 五对三条
            FOUR_TRIPLET           :        6,   # 四套三条
            ONE_COLOR              :        6,   # 凑一色
            ALL_SMALL              :        6,   # 全小
            ALL_BIG                :        6,   # 全大
            SIX_HEADS              :        20,  # 六同
            THREE_POINTS           :        26,  # 三分天下
            THREE_STRAIGHT_FLUSH   :        26,  # 三同花顺
            TWELVE_ROYALTY         :        26,  # 十二皇族
            SEVEN_HEADS            :        30,  # 七同
            DRAGON                 :        26,  # 一条龙
            SUPREME_QINGLONG       :        108,  # 至尊青龙
        }

    def getSpecialScore(self, type, pierNo=0):
        log(u'[getSpecialScore] room[%s] type[%s].'%(self.roomId, type), LOG_LEVEL_RELEASE)
        if type > FIVE_HEADS:
            # 如果选择了特殊牌型 x 2
            return self.type2Score[type] * 2 if self.specialCards_x2 else self.type2Score[type]
        if type == FIVE_HEADS:
            return 19-10*(pierNo-1)
        if type == STRAIGHT_FLUSH:
            #中墩同花顺：大于对手+9分改为10分；尾墩同花顺：大于对手+4分改为+5分；
            return 9-5*(pierNo-1)
            # return 10 - 5 * (pierNo - 1)
        if type == IRON_BRANCH:
            #中墩铁支：大于对手+7分改为+8分；尾墩铁支：大于对手+3分改为+4分；
            return 7-4*(pierNo-1)
            # return 8-4*(pierNo-1)
        if type == GOURD:
            # 中墩葫芦：大于对手+1分改为+2分；
            return 1-1*(pierNo-1)
            # return 2*(2-pierNo)
        if pierNo == 0:
            if type == DOUBLE_GHOST:
                return 20
            if type == TRIPLET:
                return 2
        return 0

    def doCompare(self):
        log(u'[doCompare] room[%s].'%(self.roomId), LOG_LEVEL_RELEASE)
        self.dealSpecialDatas()
        self.dealCommonDatas()
        self.sendComparePro()

    def dealSpecialDatas(self):
        log(u'[dealSpecialDatas] room[%s].'%(self.roomId), LOG_LEVEL_RELEASE)
        specialPlayers = self.speSideNTypes
        if not specialPlayers:
            return
        rankSides_s, side2ltSides = getRankFromSideNcards(specialPlayers)
        self.ranksDict[SPECIAL] = rankSides_s
        isDoDealer = self.hasDoODealer
        dealerSide = self.dealerSide
        for side, ltSides in side2ltSides.items():
            inPlayer = self.players[side]
            perSideScore = []
            isHorse = inPlayer.hasHorse
            _ltSides = ltSides + self.comSides
            log(u'Special cards -------------> %s' % inPlayer.perCards, LOG_LEVEL_RELEASE)
            log(u'[dealSpecialDatas] side[%s] _ltSides[%s].'%(side, _ltSides), LOG_LEVEL_RELEASE)
            if isDoDealer:
                if dealerSide != side and dealerSide not in _ltSides:
                    continue
                if dealerSide in _ltSides:
                    _ltSides = [dealerSide]
            specialType = inPlayer.getSpecialType()
            deltaScore = self.getSpecialScore(inPlayer.getSpecialType())
            if specialType == SIX_PAIRS and self.sixPairs_x2:
                deltaScore = self.getSixPairsScore(inPlayer.perCards[0].split(','))
            for side in _ltSides:
                outPlayer = self.players[side]
                curDeltaScore = deltaScore
                if isHorse or outPlayer.hasHorse:
                    curDeltaScore *= 2
                perSideScore.append('%s,%s'%(side, curDeltaScore))
                self.upGameScore(inPlayer, outPlayer, curDeltaScore, False, True, True)
                log(u'[dealSpecialDatas] inPlayer[%s] outPlayer[%s] curDeltaScore[%s].' 
                        %(inPlayer, outPlayer, deltaScore), LOG_LEVEL_RELEASE)

                if isDoDealer:
                    dealerMultiple = self.dealMultiple(inPlayer, outPlayer)
                    _curDeltaScore = curDeltaScore * (dealerMultiple - 1)
                    self.upGameScore(inPlayer, outPlayer, _curDeltaScore, False, False, True)
            if perSideScore:
                inPlayer.speScoreStr = ';'.join(perSideScore)

    def dealDoDealer(self, side2ltSides):
        dealerSide = self.dealerSide

    def dealMultiple(self, inPlayer, outPlayer):
        if self.hasDoODealer:
            if inPlayer.isDealer:
                return outPlayer.multiple
            else:
                return inPlayer.multiple
        return 1

    def dealCommonDatas(self):
        log(u'[dealCommonDatas] room[%s].'%(self.roomId), LOG_LEVEL_RELEASE)
        commonPlayers = self.comSides
        if not commonPlayers:
            return
        sideNinsDict = self.comSideNIns
        pierNo2sideNltSides = {}
        isDoDealer = self.hasDoODealer
        dealerSide = self.dealerSide
        for pierNo, sideNins in sideNinsDict.items():
            log(u'[dealCommonDatas] pierNo[%s] sideNins[%s].'%(pierNo, sideNins), LOG_LEVEL_RELEASE)
            rankSides_c, side2ltSides_c = getRankFromSideNcards(sideNins)
            self.ranksDict[pierNo] = rankSides_c
            pierNo2sideNltSides[pierNo] = side2ltSides_c
        for _side in commonPlayers:
            inPlayer = self.players[_side]
            ltSides_h = pierNo2sideNltSides[HEAD_PIER][_side]
            ltSides_m = pierNo2sideNltSides[MIDDLE_PIER][_side]
            ltSides_t = pierNo2sideNltSides[TAIL_PIER][_side]
            shootSet = set(ltSides_h) & set(ltSides_m) & set(ltSides_t)
            shootList = []
            # horseMultiple = 1
            isDealer = (dealerSide == _side)
            if shootSet and self.shootAdd:
                shootList = list(shootSet)
                if isDoDealer:
                    if isDealer:
                        self.shootDict[_side] = shootList
                    elif dealerSide in shootList:
                        self.shootDict[_side] = [dealerSide]
                else:
                    self.shootDict[_side] = shootList
            isHasHorse = inPlayer.hasHorse
            # if inPlayer.hasHorse:
                # horseMultiple = 2
            horseMultiple = 2 if isHasHorse else 1
            # log(u'[dealCommonScore] side[%s] inPlayer[%s].'%(_side, inPlayer), LOG_LEVEL_RELEASE)

            for pierNo, ltSides in enumerate([ltSides_h, ltSides_m, ltSides_t]):
                log(u'[dealCommonScore] pierNo[%s] ltSides[%s].'%(pierNo, ltSides), LOG_LEVEL_RELEASE)
                if isDoDealer:
                    if (not isDealer) and (dealerSide not in ltSides):
                        continue
                    if dealerSide in ltSides:
                        ltSides = [dealerSide]
                speScore = inPlayer.specialScore[pierNo]
                baseScore = 1
                inPlayer.basePierTotalScore += (speScore + baseScore )* self.baseScore
                for side in ltSides:
                    outPlayer = self.players[side]
                    _horseMultiple = horseMultiple
                    if outPlayer.hasHorse:
                        _horseMultiple = 2
                    _speScore = speScore * _horseMultiple
                    _baseScore = baseScore * _horseMultiple
                    deltaScore = _speScore + _baseScore

                    log(u'[dealCommonScore] inPlayer[%s] outPlayer[%s] deltaScore[%s].' 
                        %(inPlayer, outPlayer, deltaScore), LOG_LEVEL_RELEASE)
                    outPlayer.updateScore(pierNo, -deltaScore, -_speScore, -_baseScore)
                    inPlayer.updateScore(pierNo, deltaScore, _speScore, _baseScore)
                    self.upGameScore(inPlayer, outPlayer, deltaScore, False, True, True)

                    if isDoDealer:
                        dealerMultiple = self.dealMultiple(inPlayer, outPlayer)
                        curDeltaScore = deltaScore * (dealerMultiple - 1)
                        self.upGameScore(inPlayer, outPlayer, curDeltaScore, False, False, True)

    def isAllShoot(self, shootCount):
        return shootCount == self.maxPlayerCount-1 >= 2 and not self.hasDoODealer and self.isCanAllShoot

    def sendComparePro(self):
        log(u'[sendComparePro] room[%s].'%(self.roomId), LOG_LEVEL_RELEASE)
        normalDatas = [','.join(str(i) for i in self.ranksDict[pierNo]) for pierNo in PIER_LIST if self.ranksDict[pierNo]]
        specialDatas = self.ranksDict[SPECIAL]
        shootDatas = []
        allShootDatas = []
        for shootSide, beShootSides in self.shootDict.items():
            baseShootScore = 1
            shootPlayer = self.players[shootSide]
            if not self.shootAdd1:
                baseShootScore = shootPlayer.basePierTotalScore/self.baseScore

            # 全垒打
            shootCount = len(beShootSides)
            if self.isAllShoot(shootCount):
                allShootScore = shootPlayer.basePierTotalScore/self.baseScore
                for beShootSide in beShootSides:
                    outPlayer, curShootScore, multiple = self.dealShootData(shootPlayer, beShootSide, baseShootScore)
                    curScore = allShootScore*multiple + curShootScore*2
                    self.upGameScore(shootPlayer, outPlayer, curScore, True, True, True)
                    allShootDatas.append(','.join([str(shootSide), str(beShootSide), str(baseShootScore)]))
                allShootDatas.append(','.join([str(shootSide), '100', str(allShootScore)]))
            else:
                for beShootSide in beShootSides:
                    outPlayer, curShootScore, multiple = self.dealShootData(shootPlayer, beShootSide, baseShootScore)
                    self.upGameScore(shootPlayer, outPlayer, curShootScore, True, True, True)
                    shootDatas.append(','.join([str(shootSide), str(beShootSide), str(baseShootScore)]))
                    if self.hasDoODealer:
                        dealerMultiple = self.dealMultiple(shootPlayer, outPlayer)
                        curDeltaScore = curShootScore * (dealerMultiple - 1)
                        self.upGameScore(shootPlayer, outPlayer, curDeltaScore, False, False, True)

        shootDatas.extend(allShootDatas)
        resp = thirteenWater_poker_pb2.S_C_Compare()
        resp.normalDatas.extend(normalDatas)
        resp.specialDatas.extend(specialDatas)
        resp.shootDatas.extend(shootDatas)
        for _player in self.getPlayers():
            cardData = resp.cardDatas.add()
            _side = _player.chair
            cardData.side = _side
            cardData.cards.extend(_player.perCards)
            cardData.cardTypes.extend(_player.perPierType)
            type = _player.getSpecialType()
            if type > FIVE_HEADS:
                cardData.speScore = self.getSpecialScore(type)
                scoreDatas = [_player.speScoreStr]
            else:
                pierTotalScore = _player.pierTotalScore
                # scoreDatas = [','.join(str(i) for i in pierTotalScore[pierNo]) for pierNo in PIER_LIST]
                scoreDatas = [','.join(str(i) for i in pierTotalScore[pierNo]) for pierNo in PIER_LIST]
                scoreDatas.append(str(_player.curScore))
            cardData.scoreDatas.extend(scoreDatas)
            if _player.hasHorse:
                resp.horseSide = _side
        self.compareResp = copy.deepcopy(resp)
        self.sendAll(resp)
        log(u'[sendComparePro] resp[%s].'%(resp), LOG_LEVEL_RELEASE)
        self.gameStage = COMPARE_S

        for _player in self.getPlayers():
            for pierNo in PIER_LIST:
                _player.pierTotalScore[pierNo] *= self.baseScore

        self.balance()

    def dealShootData(self, inPlayer, outSide, baseShootScore):
        outPlayer = self.players[outSide]
        multiple = 2 if (inPlayer.hasHorse or outPlayer.hasHorse) else 1
        shootScore = baseShootScore * multiple
        return outPlayer, shootScore, multiple

    def upGameScore(self, inPlayer, outPlayer, deltaScore, isShoot, isTmp, isGS):
        if deltaScore == 0:
            return
        if isShoot:
            inPlayer.shootScore += deltaScore * self.baseScore
            outPlayer.shootScore -= deltaScore * self.baseScore
        if isTmp:
            inPlayer.tmpGameScore += deltaScore * self.baseScore
            outPlayer.tmpGameScore -= deltaScore * self.baseScore
        if isGS:
            inPlayer.curGameScore += deltaScore * self.baseScore
            outPlayer.curGameScore -= deltaScore * self.baseScore

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

        isDissolveEnd = self.isDissolveEnd
        #打包小局数据
        resp = poker_pb2.S_C_Balance()
        resp.isNormalEndGame = self.isGameEnd

        if isSave:
            for player in self.getPlayers():
                self.calcBalance(player)

        if self.stage != GAME_READY:
            self.fillCommonData(resp)
            
        for player in self.getPlayers():
            if self.stage != GAME_READY and not isDissolveEnd: #局间不显示单局结算数据
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
            # self.setCounter([self.dealerSide], self.balanceCounterMs, self.onGameStartTimeout)

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
            self.okList[side] = 1
            resp = thirteenWater_poker_pb2.S_C_SendOkData()
            resp.side = side
            self.sendAll(resp)
            log(u'[ready next] resp[%s].'%(resp), LOG_LEVEL_RELEASE)
        if len(self.ready2NextGameSides) >= self.maxPlayerCount:
            log(u'[ready next]room[%s] all ready.'%(self.roomId), LOG_LEVEL_RELEASE)
            self.okList = [0]*self.maxPlayerCount
            self.doNextGame(player)

    def fillArrangedCards(self, player, resp):
        resp.side = player.chair
        resp.cards.extend(player.perCards)
        resp.cardTypes.extend(player.perPierType)
        log(u'[fillArrangedCards] room[%s] resp[%s].'%(self.roomId, resp), LOG_LEVEL_RELEASE)

    def dealDefaultType(self):
        """
        处理玩家操作超时的默认牌型
        """
        for player in self.getPlayers():
            player.handleMgr.dealDefaultType()

    def getArrangeCounterMs(self):
        """
        """
        # return 103*1000
        return 301*1000

    def onArrangeTimeout(self):
        """
        """
        # return
        for player in self.getPlayers():
            log(u'[onArrangeTimeout] room[%s] player[%s].'%(self.roomId, player), LOG_LEVEL_RELEASE)
            if not player.perPierType and not player.perCards:
                rslt = player.handleMgr.checkCardsType(player.defaultCards, player.defaultType)
                log(u'[onArrangeTimeout] room[%s] rslt[%s].'%(self.roomId, rslt), LOG_LEVEL_RELEASE)
                if not rslt:
                    return
        log(u'[onArrangeTimeout] room[%s] start doCompare.'%(self.roomId), LOG_LEVEL_RELEASE)
        self.doCompare()
        return

    def setPlayerCopy(self, robot, player):
        """
        设置拷贝了玩家数据的机器人
        """
        super(Game, self).setPlayerCopy(robot, player)

        robot.totalShootCount = player.totalShootCount
        robot.totalAllShootCount = player.totalAllShootCount
        robot.totalSpeCount = player.totalSpeCount

        robot.perPierType = player.perPierType
        robot.defaultType = player.defaultType
        robot.perCards = player.perCards
        robot.defaultCards = player.defaultCards
        robot.hasHorse = player.hasHorse
        robot.multiple = player.multiple
        robot.specialScore = player.specialScore
        robot.pierTotalScore = player.pierTotalScore
        robot.arranged = player.arranged
        robot.curScore = player.curScore
        robot.basePierTotalScore = player.basePierTotalScore
        robot.shootScore = player.shootScore
        robot.tmpGameScore = player.tmpGameScore
        robot.isDealer = player.isDealer
        robot.speScoreStr = player.speScoreStr
        robot.isSureCards = player.isSureCards


    def onJoinGame(self, player, resp, isSendMsg=True):
        """
        加入游戏
        """
        super(Game, self).onJoinGame(player, resp, isSendMsg=True)

        #通知禁用互动功能
        if self.banInteraction:
            resp = private_mahjong_pb2.S_C_BanInteraction()
            resp.result = True
            self.sendOne(player, resp)

