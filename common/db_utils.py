#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    数据表实用操作
"""

from common.common_db_define import *
import time
from datetime import datetime, timedelta

MAX_TTL_GAME_LOG = 7 * 24 * 3600

def readLangTxtsFromRequest(request, lang):
    langTxts = {}
    for langCode, _ in lang.LANGUAGE_NAMES:
        field = 'txt%s'%(langCode)
        langTxts[field] = request.forms.get(field, '').strip()
    return langTxts

def readGamesFromRequest(request):
    agGames = []
    for idx, gameId in enumerate(GAME_IDS):
        agGame = {}
        agGame['enable'] = 'on' #request.forms.get('game%sEnable'%(idx+1), '').strip()
        agGame['rateShare'] = request.forms.get('game%sRateShare'%(idx+1), '').strip()
        agGame['oddsOfPumping'] = '3' #request.forms.get('game%sOddsOfPumping'%(idx+1), '').strip()
        agGames.append(agGame)
    return agGames

def getRealAgAccount(redis, account):
    type, parentAg = redis.hmget(FORMAT_ADMIN_ACCOUNT_TABLE%(account), ('type', 'parentAg'))
    if ADMIN_TYPE_SUB_ACCOUNT == type:
        return parentAg
    else:
        return account

def getRateShare(redis, account):
    agGameTable = FORMAT_ADMIN_GAME_TABLE%(account, FISHGAME_GAMEID)
    return redis.hget(agGameTable, 'rateShare')

def getGameOnline(redis, account):
    """
    根据账号返回用户在线游戏数据
    @param p1:
    @type p1:
    @return:
    @rtype:
    """
    onlineInfo = {}
    for gameId in GAME_IDS:
        onlineTable = FORMAT_CUR_USER_GAME_ONLINE%(account)
        info = redis.hgetall(onlineTable)
        if info:
            onlineInfo[gameId] = info
    return onlineInfo

def getAgGames(redis, lang, account):
    agGames = []
    for gameId in GAME_IDS:
        agGameTable = FORMAT_ADMIN_GAME_TABLE%(account, gameId)
        agGame = redis.hgetall(agGameTable)
        agGame['name'] = lang.GAMES_NAME[gameId]
        agGames.append(agGame)
    return agGames

def saveAgGames(redis, account, games):
    for gameId, game in zip(GAME_IDS, games):
        agGameTable = FORMAT_ADMIN_GAME_TABLE%(account, gameId)
        redis.hmset(agGameTable, game)

def getDirectAgChildren(redis, account):
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)
    return [child for child in children]

def getSubAccount(redis, account):
    subAccountTable = FORMAT_ADMIN_ACCOUNT_SUB_ACCOUNT_TABLE%(account)
    subAccounts = redis.smembers(subAccountTable)
    return [subAccount for subAccount in subAccounts]

def getDirectMemberChildren(redis, account):
    memberTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account)

    membersIds = redis.smembers(memberTable)
    return [memberId for memberId in membersIds]

def getAgDownLineCount(redis, account):
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    count = 0
    memberTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account)
    count += redis.scard(memberTable)

    for child in children:
        count += int(redis.hget(FORMAT_ADMIN_ACCOUNT_TABLE%(child), 'agCount'))

    return count

def getAgChildrenCount(redis, account):
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    count = 0
    memberTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account)
    count += redis.scard(memberTable)
    for child in children:
        count += getAgChildrenCount(redis, child)

    return count

def getAgOnlyAgChildrenSet(redis, account):
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    res = [child for child in children]
    for child in children:
        res.extend(getAgOnlyAgChildrenSet(redis, child))

    return res

def getAgOnlyMemberChildrenIdSet(redis, account):
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    res = []
    memberTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account)

    membersIds = redis.smembers(memberTable)
    memberAccounts = [memberId for memberId in membersIds]
    res.extend(memberAccounts)
    for child in children:
        res.extend(getAgOnlyMemberChildrenIdSet(redis, child))

    return res

def getAgOnlyMemberChildrenSet(redis, account):
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    res = []
    memberTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account)

    membersIds = redis.smembers(memberTable)
    memberAccounts = [redis.hget(FORMAT_USER_TABLE%(memberId), 'account') for memberId in membersIds]
    res.extend(memberAccounts)
    for child in children:
        res.extend(getAgOnlyMemberChildrenSet(redis, child))

    return res

def getAgChildrenSet(redis, account):
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    res = [child for child in children]
    memberTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account)

    membersIds = redis.smembers(memberTable)
    memberAccounts = [redis.hget(FORMAT_USER_TABLE%(memberId), 'account') for memberId in membersIds]
    res.extend(memberAccounts)
    for child in children:
        res.extend(getAgChildrenSet(redis, child))

    return res

def getParentAg(redis, account, table = None):
    parentAgs = []
    if not table:
        table = FORMAT_ADMIN_ACCOUNT_TABLE%(account)
    parentAg = redis.hget(table, 'parentAg')
    if not parentAg:
        return []
    else:
        parentAgs.append(parentAg)
        parentAgs.extend(getParentAg(redis, parentAg))
        return parentAgs

def isParentAg(redis, account, parentAccount, table = None):
    #先判断账号是否有效
    if redis.hget(FORMAT_ADMIN_ACCOUNT_TABLE%(parentAccount), 'valid') != '1':
        return False
    parentAgs = getParentAg(redis, account, table)
    return parentAccount in parentAgs

def serviceNoticeMemberRefresh(redis, account, excludeServiceTag = None):
    for gameId in GAME_IDS:
        onlineTable = FORMAT_CUR_USER_GAME_ONLINE%(account)
        onlineInfo = redis.hgetall(onlineTable)
        if onlineInfo:
            if excludeServiceTag and excludeServiceTag == onlineInfo['serviceTag']:
                continue
            redis.rpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, onlineInfo['serviceTag']), HEAD_SERVICE_PROTOCOL_MEMBER_REFRESH%(account))

def serviceNoticeKickMember(redis, account):
    for gameId in GAME_IDS:
        onlineTable = FORMAT_CUR_USER_GAME_ONLINE%(account)
        onlineInfo = redis.hgetall(onlineTable)
        if onlineInfo:
            redis.rpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, onlineInfo['serviceTag']), HEAD_SERVICE_PROTOCOL_KICK_MEMBER%(account))

def freezeAg(redis, account):
    agTable = (FORMAT_ADMIN_ACCOUNT_TABLE)%account
    redis.hset(agTable, 'valid', 0)
    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    memberIDs = redis.smembers(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account))
    for memberID in memberIDs:
        memberTable = FORMAT_USER_TABLE%(memberID)
        memberAccount = redis.hget(memberTable, 'account')
        redis.hset(memberTable, 'valid', 0)
        serviceNoticeMemberRefresh(redis, memberAccount)

    for child in children: 
        freezeAg(redis, child)

def getCreditByCurrency(redis, credit, fromCurrency, toCurrency):
    if fromCurrency == toCurrency:
        return float(credit)
    #货币兑率转换
    fromCent, fromCoinRate = redis.hmget((FORMAT_ADMIN_CURRENCY_DICT_TABLE)%fromCurrency, ('name', 'coinRate'))
    toCent, toCoinRate = redis.hmget((FORMAT_ADMIN_CURRENCY_DICT_TABLE)%toCurrency, ('name', 'coinRate'))
    credit = float(credit)
    fromCoinRate = float(fromCoinRate)/float(fromCent)
    toCoinRate = float(toCoinRate)/float(toCent)

    return (credit*fromCoinRate)/toCoinRate

def modifyAgCurrency(redis, account, toCurrency, excludeMember=False):
    agTable = FORMAT_ADMIN_ACCOUNT_TABLE%(account)
    fromCurrency, credit = redis.hmget(agTable, ('currency', 'credit'))
    #无更新
    if fromCurrency == toCurrency:
        return

    toCredit = getCreditByCurrency(redis, credit, fromCurrency, toCurrency)
    redis.hmset(agTable, {
        'currency'          :   toCurrency,
        'credit'            :   toCredit
    })

    curDateTime = datetime.now()
    deltaTime = timedelta(-1)
    #前90天内的数据纠正
    endDateTime = curDateTime + timedelta(-90)
    while endDateTime < curDateTime:
        curDate = curDateTime.strftime('%Y-%m-%d')
        for gameId in GAME_IDS:
            betCash = redis.get(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(account, gameId, curDate))
            profitCash = redis.get(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(account, gameId, curDate))
            if betCash:
                betCash = getCreditByCurrency(redis, betCash, fromCurrency, toCurrency)
                profitCash = getCreditByCurrency(redis, profitCash, fromCurrency, toCurrency)
                redis.set(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(account, gameId, curDate), betCash)
                redis.set(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(account, gameId, curDate), profitCash)
        curDateTime += deltaTime

    if not excludeMember:
        membersTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(account)
        memberIds = redis.smembers(membersTable)
        for memberId in memberIds:
            memberTable = FORMAT_USER_TABLE%(memberId)
            memberAccount, fromCurrency, credit = redis.hmget(memberTable, ('account', 'currency', 'money'))
            #无更新
            if fromCurrency == toCurrency:
                continue
            toCredit = getCreditByCurrency(redis, credit, fromCurrency, toCurrency)
            redis.hmset(memberTable, {
                'currency'      :   toCurrency,
                'money'         :   toCredit
            })
            curDateTime = datetime.now()
            #前90天内的数据纠正
            endDateTime = curDateTime + timedelta(-90)
            while endDateTime < curDateTime:
                curDate = curDateTime.strftime('%Y-%m-%d')
                for gameId in GAME_IDS:
                    betCash = redis.get(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(memberAccount, gameId, curDate))
                    profitCash = redis.get(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(memberAccount, gameId, curDate))
                    if betCash:
                        betCash = getCreditByCurrency(redis, betCash, fromCurrency, toCurrency)
                        profitCash = getCreditByCurrency(redis, profitCash, fromCurrency, toCurrency)
                        redis.set(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(memberAccount, gameId, curDate), betCash)
                        redis.set(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(memberAccount, gameId, curDate), profitCash)

                curDateTime += deltaTime
            serviceNoticeMemberRefresh(redis, memberAccount)

    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    for child in children:
        modifyAgCurrency(redis, child, toCurrency)

def isServiceOutDate():
    outDate = datetime.strptime('2020-07-28 00:00:00', '%Y-%m-%d %H:%M:%S')
    if datetime.now() > outDate:
        return True
    return False

def getCurrencyHTML(redis):
    currencyTables = redis.smembers(FORMAT_ADMIN_CURRENCY_DICT_TABLE_SET)
    fields = ('code', 'name', 'coinRate')
    currency = []
    for currencyTable in currencyTables:
        info = {}
        code, cent, coinRate = redis.hmget(currencyTable, fields)
        info['code'] = code
        info['text'] = '%s (%s:%s)'%(code, cent, coinRate)
        currency.append(info)
    return currency

def isGameServiceRunning(redis, gameId):
    assert gameId in GAME_IDS
    return bool(redis.lrange(FORMAT_GAME_SERVICE_SET%(gameId), 0, -1))

def sendProtocol2OneGameService(redis, gameId, protocolStr):
    """
    发协议给某个服务器
    """
    # assert gameId in GAME_IDS
    serverList = redis.lrange(FORMAT_GAME_SERVICE_SET%(gameId), 0, -1)
    print 'sendProtocol2OneGameService11111', gameId,serverList
    if not serverList:
        return
    serverTable = serverList[0]
    _, _, _, currency, ip, port = serverTable.split(':')
    redis.rpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, '%s:%s:%s'%(currency, ip, port)), protocolStr)
    # for serverTable in serverList:
        # if serviceFind and serverTable.find(serviceFind) == -1:
            # continue
        # _, _, _, currency, ip, port = serverTable.split(':')
        # redis.rpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, '%s:%s:%s'%(currency, ip, port)), protocolStr)

def sendProtocol2GameService(redis, gameId, protocolStr, serviceFind = None):
    # assert gameId in GAME_IDS
    serverList = redis.lrange(FORMAT_GAME_SERVICE_SET%(gameId), 0, -1)
    for serverTable in serverList:
        if serviceFind and serverTable.find(serviceFind) == -1:
            continue
        _, _, _, currency, ip, port = serverTable.split(':')
        redis.rpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, '%s:%s:%s'%(currency, ip, port)), protocolStr)

def sendProtocol2AllGameService(redis, protocolStr):
    for gameId in GAME_IDS:
        sendProtocol2GameService(redis, gameId, protocolStr)

def getAgTotalCash(redis, gameId, account, startDate, endDate, onlySelf=False):
    """
    获取代理某个时间段的总账，通过递归统计该时间段，所有代理投注及输赢数据
    @param redis: Redis连接实例
    @type redis: Redis连接实例
    @param gameId: 游戏ID
    @type gameId: string
    @param account: 账户名
    @type account: string
    @param startDate: 开始时间
    @type startDate: string YYYY-mm-dd HH:MM:SS
    @param endDate: 结束时间
    @type endDate: string YYYY-mm-dd HH:MM:SS
    @return: totalBet, totalProfit
    @rtype: float, float
    """
    deltaTime = timedelta(1)

    toCurrency = redis.hget(FORMAT_ADMIN_ACCOUNT_TABLE%(account), 'currency')

    if onlySelf:
        children = []
    else:
        childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
        children = redis.smembers(childrenTable)

    totalBet = 0
    totalProfit = 0
    totalShare = 0

    for child in children:
        fromCurrency = redis.hget(FORMAT_ADMIN_ACCOUNT_TABLE%(child), 'currency')

        bet, profit = getAgTotalCash(redis, gameId, child, startDate, endDate)
        totalBet += getCreditByCurrency(redis, bet, fromCurrency, toCurrency)
        totalProfit += getCreditByCurrency(redis, profit, fromCurrency, toCurrency)

    startDateTime = datetime.strptime(startDate, '%Y-%m-%d')
    endDateTime = datetime.strptime(endDate, '%Y-%m-%d')

    creditProfit = 0
    while startDateTime <= endDateTime:
        curDate = startDateTime.strftime('%Y-%m-%d')
        bet = redis.get(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(account, gameId, curDate))
        if bet:
            totalBet += float(bet)
        profit = redis.get(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(account, gameId, curDate))
        if profit:
            totalProfit += float(profit)

        startDateTime += deltaTime

    return totalBet, totalProfit

def calcAgTotalCashT(redis, gameId, account, curDate):
    """
    计算生成代理当天的总账，通过递归统计所有代理投注及输赢数据，转存到当天缓存记录中，建议1分钟一次
    @param redis: Redis连接实例
    @type redis: Redis连接实例
    @param gameId: 游戏ID
    @type gameId: string
    @param account: 账户名
    @type account: string
    @param curDate: 日期GMT+8
    @type curDate: string YYYY-mm-dd
    @return: totalBet, totalProfit
    @rtype: float, float
    """

    toCurrency = redis.hget(FORMAT_ADMIN_ACCOUNT_TABLE%(account), 'currency')

    childrenTable = FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE%(account)
    children = redis.smembers(childrenTable)

    totalBet = 0
    totalProfit = 0
    totalShare = 0

    for child in children:
        fromCurrency = redis.hget(FORMAT_ADMIN_ACCOUNT_TABLE%(child), 'currency')

        bet, profit = calcAgTotalCashT(redis, gameId, child, curDate)
        totalBet += getCreditByCurrency(redis, bet, fromCurrency, toCurrency)
        totalProfit += getCreditByCurrency(redis, profit, fromCurrency, toCurrency)

    bet = redis.get(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(account, gameId, curDate))
    if bet:
        totalBet += float(bet)
    profit = redis.get(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(account, gameId, curDate))
    if profit:
        totalProfit += float(profit)

    redis.set(FORMAT_ACCOUNT_BET_CASH_DATE_T_TABLE%(account, gameId, curDate), totalBet)
    redis.set(FORMAT_ACCOUNT_PROFIT_CASH_DATE_T_TABLE%(account, gameId, curDate), totalProfit)

    return totalBet, totalProfit

def getAgTotalCashT(redis, gameId, account, startDate, endDate):
    """
    获取代理某个时间段的总账，临时缓存优化版
    @param redis: Redis连接实例
    @type redis: Redis连接实例
    @param gameId: 游戏ID
    @type gameId: string
    @param account: 账户名
    @type account: string
    @param startDate: 开始时间
    @type startDate: string YYYY-mm-dd HH:MM:SS
    @param endDate: 结束时间
    @type endDate: string YYYY-mm-dd HH:MM:SS
    @return: totalBet, totalProfit
    @rtype: float, float
    """
    deltaTime = timedelta(1)

    totalBet = 0
    totalProfit = 0
    totalShare = 0

    startDateTime = datetime.strptime(startDate, '%Y-%m-%d')
    endDateTime = datetime.strptime(endDate, '%Y-%m-%d')

    while startDateTime <= endDateTime:
        curDate = startDateTime.strftime('%Y-%m-%d')
        bet = redis.get(FORMAT_ACCOUNT_BET_CASH_DATE_T_TABLE%(account, gameId, curDate))
        if bet:
            totalBet += float(bet)
        profit = redis.get(FORMAT_ACCOUNT_PROFIT_CASH_DATE_T_TABLE%(account, gameId, curDate))
        if profit:
            totalProfit += float(profit)

        startDateTime += deltaTime

    return totalBet, totalProfit

def inputUserLog(pipe, account, gameId, curDateTime, logData):
    """
    @param pipe: Redis提交管道
    @type pipe: Redis pipeline
    @param gmaeId: 玩家账号
    @type pipe: string
    @param gmaeId: 游戏标识
    @type pipe: redis pipeline
    @param curDateTime: 当前时间字符串，精确到分
    @type curDateTime: string, format(YYYY-mm-dd MM:HH:SS)
    @param logData: 日志字典
    @type logData: dict, format({'type' : LOGIN,'ip' : 'XXX.XXX.XXX.XXX', 'serviceTag' : '$服务器标识'})
    @return:
    @rtype:
    """
    logListTable = FORMAT_ACCOUNT_LOG_LIST_TABLE%(account)
    logTable = FORMAT_ACCOUNT_LOG_TABLE%(gameId, account, curDateTime)
    pipe.lpush(logListTable, logTable)
    pipe.ltrim(logListTable, 0, MAX_LOG_LIST_COUNT)
    pipe.hmset(logTable, logData)
    pipe.expire(logTable, LOG_TABLE_TTL)

def userDBLogin(redis, pipe, account, gameId, userTable, ip, serviceTag, serviceTable, dateTimeStr, parentAg):
    _ymd, _hms = dateTimeStr.split(' ')
    curDateStr = _ymd
    curLoginDateTable = FORMAT_LOGIN_DATE_TABLE%(curDateStr)
    curOnlineTable = FORMAT_ONLINE_TABLE%(gameId)
    userOnlineTable = FORMAT_CUR_USER_GAME_ONLINE%(account)
    try:
        oldDateStr = redis.hget(userTable, 'last_login_date').split(' ')[0]
    except:
        oldDateStr = ''
    if oldDateStr != curDateStr:
        try:
            redis.incrby(DAY_ALL_LOGIN_COUNT%(curDateStr), 1)
            redis.expire(DAY_ALL_LOGIN_COUNT%(curDateStr), CASH_TABLE_TTL)
        except Exception as e:
            print 'File', e
            redis.delete(DAY_ALL_LOGIN_COUNT%(curDateStr))
            redis.incrby(DAY_ALL_LOGIN_COUNT%(curDateStr), 1)
            redis.expire(DAY_ALL_LOGIN_COUNT%(curDateStr), CASH_TABLE_TTL)
        try:
            redis.incrby(DAY_AG_LOGIN_COUNT%(parentAg, curDateStr), 1)
            redis.expire(DAY_AG_LOGIN_COUNT%(parentAg, curDateStr), CASH_TABLE_TTL)
        except Exception as e:
            print 'File', e
            redis.delete(DAY_AG_LOGIN_COUNT%(parentAg, curDateStr),)
            redis.incrby(DAY_AG_LOGIN_COUNT%(parentAg, curDateStr), 1)
            redis.expire(DAY_AG_LOGIN_COUNT%(parentAg, curDateStr), CASH_TABLE_TTL)

    pipe.hmset(userOnlineTable, 
            {
                'serviceTag'        :   serviceTag,
                'ip'                :   ip,
                'date'              :   dateTimeStr,
            }
    )
    pipe.hmset(userTable, 
        {
            'last_login_ip'     :   ip,
            'last_login_date'   :   dateTimeStr
        }
    )
    pipe.sadd(curLoginDateTable, account)
    inputUserLog(pipe, account, gameId, dateTimeStr, 
            {
                'type'          :   GAMELOG_TYPE_LOGIN,
                'ip'            :   ip,
                'serviceTag'    :   serviceTag,
            }
    )
    pipe.hincrby(serviceTable, 'playerCount', 1)
    pipe.sadd(ONLINE_ACCOUNTS_TABLE, account)
    pipe.sadd(ONLINE_GAME_ACCOUNTS_TABLE%(gameId), account)
    pipe.incrby(curOnlineTable, 1)
    res = pipe.execute()
    tmpDateStr = _ymd + '-' + _hms.split(':')[0]
    maxOnlineTable = FORMAT_MAX_ONLINE_COUNT_TABLE%(gameId, tmpDateStr)
    if int(res[-1]) > redis.incrby(maxOnlineTable, 0):
        redis.set(maxOnlineTable, res[-1])

def userDBLogout(pipe, account, gameId, userTable, ip, serviceTable, dateTimeStr):
    curOnlineTable = FORMAT_ONLINE_TABLE%(gameId)
    userOnlineTable = FORMAT_CUR_USER_GAME_ONLINE%(account)
    pipe.delete(userOnlineTable)
    pipe.hmset(userTable, 
        {
            'last_logout_ip'    :   ip,
            'last_logout_date'  :   dateTimeStr
        }
    )
    inputUserLog(pipe, account, gameId, dateTimeStr, 
            {
                'type'          :   GAMELOG_TYPE_LOGOUT,
                'ip'            :   ip,
                'date'          :   dateTimeStr
            }
    )
    pipe.hincrby(serviceTable, 'playerCount', -1)
    pipe.srem(ONLINE_ACCOUNTS_TABLE, account)
    pipe.srem(ONLINE_GAME_ACCOUNTS_TABLE%(gameId), account)
    pipe.incrby(curOnlineTable, -1)
    pipe.execute()

def userDBBetNProfit(pipe, account, parentAg, currency, bet, profit, gameId, money2coinRate, parentMoeny2coinRate):
    """
    curDateTime: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    """
    #试玩无须入账
    if currency == 'GUEST':
        return

    curTime = time.time()
    curDate = time.strftime("%Y-%m-%d", time.localtime(curTime))

    betMoney = round(float(bet)/money2coinRate, 2)
    profit = profit - bet
    profitMoney = round(float(profit)/money2coinRate, 2)
    parentBetMoney = round(float(bet)/parentMoeny2coinRate, 2)
    parentProfitMoney = round(float(profit)/parentMoeny2coinRate, 2)

    if bet:
        pipe.incrbyfloat(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(parentAg, gameId, curDate), parentBetMoney)
        pipe.incrbyfloat(FORMAT_ACCOUNT_BET_CASH_DATE_TABLE%(account, gameId, curDate), betMoney)
        #pipe.incrbyfloat(FORMAT_CURRENCY_BET_CASH_DATE_TABLE%(currency, gameId, curDate), betMoney)
    if profit:
        pipe.incrbyfloat(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(parentAg, gameId, curDate), parentProfitMoney)
        pipe.incrbyfloat(FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE%(account, gameId, curDate), profitMoney)
        #pipe.incrbyfloat(FORMAT_CURRENCY_PROFIT_CASH_DATE_TABLE%(currency, gameId, curDate), profitMoney)

    if bet or profit:
        cashListTable = FORMAT_ACCOUNT_GAME_CASH_LIST_TABLE%(account)
        pipe.lpush(cashListTable, FORMAT_ACCOUNT_GAME_CASH%(curTime, gameId, betMoney, profitMoney))
        pipe.ltrim(cashListTable, 0, MAX_CASH_LIST_COUNT)
