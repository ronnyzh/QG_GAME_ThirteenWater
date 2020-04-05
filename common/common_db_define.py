# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: 数据表定义
"""

#版本号
VERSION = "1.0.1334"

"""
IP -> 地区码 映射
"""
FORMAT_IP2CONTRYCODE = "global:ip:%s:countryCode"
FORMAT_IP2REGIONCODE = "global:ip:%s:regionCode"

"""
UID到玩家表名的映射：users:account:$账号名
users:uid:test      ->      账号test所在的数据表
"""
FORMAT_ACCOUNT2USER_TABLE = "users:account:%s"
"""
玩家数据表：users:$id(从1开始递增）

"""
FORMAT_USER_TABLE = "users:%s"
FORMAT_USER_COUNT_TABLE = "users:count"
FORMAT_NICKNAME2USER_TABLE = "users:nickname:%s"
"""
金币排行榜表
表项：
[($uid, coin),...]
"""
FORMAT_USER_COIN_TABLE = "users:game:%s:coin"
FORMAT_USER_COINDELTA_TABLE = "users:game:%s:coinDelta"
FROMAT_USER_FISHCOUNT_TABLE = "users:game:%s:fishCount"
FISH_LEVEL_SHIFT_MASK = 0xFF000000
FISH_COUNT_SHIFT_MASK = 0x00FFFFFF
RANK_COUNT = 30

"""
玩家游戏数据：黄金时刻任务个数
"""
FORMAT_USER_GAME_DATA_GOLD_TIME_COUNT = "goldTimeCount:user:%s:gameId:%s:key"

def GET_FISH_LEVEL(data):
    return ((data & FISH_LEVEL_SHIFT_MASK) >> 24)

def GET_FISH_COUNT(data):
    return data & FISH_COUNT_SHIFT_MASK

def FISH_LEVEL_COUNT(level, count):
    return ((level & 0xff) << 24) | (count & FISH_COUNT_SHIFT_MASK)

"""
各小时在线人数记录
等就test有
"""
FORMAT_ONLINE_TABLE = "online:game:%s:count"
FORMAT_MAX_ONLINE_COUNT_TABLE = "online:game:%s:%s:maxCount"
#总在线账号
ONLINE_ACCOUNTS_TABLE = "online:accounts"
ONLINE_GAME_ACCOUNTS_TABLE = "online4game:accounts:game:%s"

"""
玩家的在线情况
user:$account:online:$gameId
{
    'serviceTag'        :   serviceTag,
    'clientKind'        :   clientKind,
    'ip'                :   ip,
    'date'              :   dateTimeStr,
    'game'              :   gameNum
}
"""
FORMAT_CUR_USER_GAME_ONLINE = "user:%s:online"

"""
DAU日活跃用户统计
redis set,记录每日登陆玩家账号，不重复，如：
login:date:account:2015-01-01
记录2015-01-01的不重复登录玩家账号
"""
FORMAT_LOGIN_DATE_TABLE = "login:date:account:%s"

"""
日注册玩家
redis set,记录每日注册玩家账号
login:date:account:2015-01-01
记录2015-01-01的不重复注册玩家账号
"""
FORMAT_REG_DATE_TABLE = "reg:date:account:%s"

"""
玩家游戏日志
{
    'type'              :   #日志类型
    'ip'                :   #操作产生ip
    'date'              :   #操作产生时间
    'coinDelta'         :   #操作产生金币流水
    'gainRate'          :   #获取倍率（仅捕获操作有效）
    'pickFishCount'     :   #捕获鱼数量（仅捕获操作有效）
}
"""
#user:$account:logList
FORMAT_ACCOUNT_LOG_LIST_TABLE = "user:%s:logList"
#userlog:$gameId:$account:$YYYY-mm-dd MM:HH:SS
FORMAT_ACCOUNT_LOG_TABLE = "userlog:%s:%s:%s"
MAX_LOG_LIST_COUNT = 2999
LOG_TABLE_TTL = 60 * 60 * 24 * 8
FROMAT_ACCOUNT_GAME_LOG_COUNT_TABLE = "gamelog:%s:account:%s"
FORMAT_ACCOUNT_GAME_LOG_TABLE = "gamelog:%s:account:%s:%d"

#gamecash:account:$account
FORMAT_ACCOUNT_GAME_CASH_LIST_TABLE = "gamecash:account:%s"
#gamecash:$gameId:account:$account:$dateTime
FORMAT_ACCOUNT_GAME_CASH_TABLE = "gamecash:%s:account:%s:%s"
#$time.time()|$gameId|$bet|$profit
FORMAT_ACCOUNT_GAME_CASH = "%s|%s|%s|%s"
#最大玩家投注订单
MAX_CASH_LIST_COUNT = 2999
#最长保存30天
CASH_TABLE_TTL = 60 * 60 * 24 * 91

#betDetail:account:$account
FORMAT_ACCOUNT_GAME_BET_DETAIL_LIST_TABLE = "betDetail:account:%s"
#$time.time()|$gameId|$bet|$profit|$fishs[]
FORMAT_ACCOUNT_GAME_BET_DETAIL = "%s|%s|%s|%s|%s"
#投注细明最多存最近30000条
MAX_BET_DETAIL_LIST_COUNT = 29999

#failedOrders:$account
FORMAT_TORDER_FAIL_LIST_TABLE = "failedOrders:%s"
#torders:$account
FORMAT_TORDER_LIST_TABLE = "torders:%s"
#torder:$account:$datetime
FORMAT_TORDER_TABLE = "torder:%s:%s"
MAX_TORDER_COUNT = 999


"""
游戏服务配置表
{
    'playerCount'       :   #玩家个数
    'roomCount'         :   #房间个数
}
"""
#gameid:currency:ip:port
FORMAT_GAME_SERVICE_TABLE = "service:game:%s:%s"
FORMAT_GAME_SERVICE_SET = "services:game:%s"

"""
运营接口KEY
"""
"""
运营商tag类型：
'gc'        =   黄金世纪
'tbs'       =   A1
'default'   =   默认
"""
OPERATOR_TAGS = ('gc', 'tbs', 'default')

"""
运营商数据表
{
    "outDesKey"         :       "",
    "outMD5Key"         :       "",
    "inDesKey"          :       "",
    "inMd5Key"          :       "",
    "billNo"            :       0,
    "cAgent"            :       "",
    "apiUrl"            :       "",
    "apiRetryTimes"     :       3,
    "cacheExistSec"     :       300
}
"""
FORMAT_OPERATOR_TABLE = "operators:%s"
FORMAT_OPERATOR_TABLE_SET = "operators:set"

"""
运营商子游戏API
{
    "apiUrl"            :   "",
}
#gameId
"""
FORMAT_OPERATOR_GAMEAPI_TABLE = "operator:%s:gameapi:%s"

FORMAT_SELF2GOLDEN_DES_KEY_TABLE = "self2golden:des:key"
FORMAT_SELF2GOLDEN_MD5_KEY_TABLE = "self2golden:md5:key"
FORMAT_GOLDEN2SELF_DES_KEY_TABLE = "golden2self:des:key"
FORMAT_GOLDEN2SELF_MD5_KEY_TABLE = "golden2self:md5:key"

FORMAT_GOLDEN_BILL_NO = "operator:golden:billno"
FORMAT_GOLDEN_CAGENT = "operator:golden:cagent"

OPERATOR_GOLDEN_URL = "http://202.131.80.61/api/doExternalReading.do?%s"
OPERATOR_URL_TRY_COUNT = 3
OPERATOR_GET_BALANCE_PARAMS = "ag=%s/\\\\/cagent=%s/\\\\/sid=%s/\\\\/method=gb/\\\\/cur=%s"
OPERATOR_TRANSFER_PARAMS = "ip=%s/\\\\/gameId=%s/\\\\/sectionId=%s/\\\\/closeFlag=%d/\\\\/ag=%s/\\\\/cagent=%s/\\\\/method=tq/\\\\/sid=%s/\\\\/billno=%s/\\\\/type=%s/\\\\/credit=%s/\\\\/cur=%s"
#cache映射一个account，时间默认是5分钟
"""
{
    'sessionId'         :   #账号sessionId
}
"""
FORMAT_LOGIN_CAHCE_TABLE = "login:cache:%s"
#loginR:$account:$timestamp
FORMAT_LOGIN_REPEATED_TABLE = "loginR:%s:%s"
LOGIN_REPEATED_TIMEOUT_SEC = 60 * 60 * 24 * 30
GOLDEN_LOGIN_CACHE_SEC = 60 * 30
OPERATOR_TAG_GOLDEN = "golden666"

"""
玩家日志类型
"""
GAMELOG_TYPE_FIRE = 0
GAMELOG_TYPE_PICKFISH = 1
GAMELOG_TYPE_CREDITIN = 2
GAMELOG_TYPE_CREDITOUT = 3
GAMELOG_TYPE_LOGIN = 10
GAMELOG_TYPE_LOGOUT = 11
GAMELOG_TYPE_JOINGAME = 12
GAMELOG_TYPE_EXITGAME = 13

"""
账目流水日志类型
"""
GAMELOG_TYPE_REAL_CREDIT = (GAMELOG_TYPE_FIRE, GAMELOG_TYPE_PICKFISH)
GAMELOG_TYPE_CREDIT = (GAMELOG_TYPE_FIRE, GAMELOG_TYPE_PICKFISH, GAMELOG_TYPE_CREDITIN, GAMELOG_TYPE_CREDITOUT)

"""
玩家设置表
{
    "musicVolume"           :   #音乐音量大小
    "soundVolume"           :   #音效音量大小
    "coinTransferPerTime"   :   #每次转账金币额
}
"""
FORMAT_ACCOUNT_SETTING_TABLE = "account:%s:settting:game:%s"
DEFAULT_SETTING_TRANSFER_COIN = 1000
DEFUALT_SETTING_MUSIC_VOLUME = 0.5
DEFAULT_SETTING_SOUND_VOLUME = 0.5

"""
货币与金币兑率关系表
"""
FORMAT_MONEY2COIN_RATE_TABLE = "money:coin:rate:%s"

#新注玩家默认赠送金币
NEWCOMER_MONEY = 100

#默认抽水(97%)
DEFAULT_ODDS_PUMPING = 3
#默认升水变化时间差，每个玩家隔段时间升水
DEFAULT_ODDS_UP_SWITCH_SEC = 60
#默认升水增加赔率
DEFAULT_ODDS_UP_DELTA = 10
#默认每次升水人数百分比
DEFAULT_ODDS_UP_COUNT = 10
#默认币种
DEFAULT_MONEY_CODE = "RMB"
#默认兑率
DEFAULT_MONEY2COIN_RATE = 1000
#默认最低赔率缩放因子(0.65)
DEFAULT_ODDS_MIN = 65

MIN_ODDS_UP_DELTA_MIN = 0
MAX_ODDS_UP_DELTA_MAX = 20

MIN_ODDS_MIN = 30
MAX_ODDS_MIN = 80
MIN_ODDS_PUMPING = 1
MAX_ODDS_PUMPING = 20
MIN_RATE_RETURN = 0
MAX_RATE_RETURN = 0.5
DEFAULT_INFINIT_AGCOUNT = 99999999
DEFAULT_INFINIT_CREDIT = 999999999999

DEFAULT_TRIAL_ACCOUNT_COUNT = 1000

"""
管理后台数据库
"""

"""
{
    'enable'            :   1,
    'rateShare'         :   60,
    'oddsOfPumping'     :   #赔率抽水
}
"""
FORMAT_ADMIN_GAME_TABLE = "admins:account:%s:game:%s"

"""
管理员数据表
{
    'passwd'            :   "",
    'credit'            :   1.00,
    'agCount'           :   100,
    'currency'          :   "RMB",
    'type'              :   "",
    'parentAg'          :   "",
    'agLevel'           :   1,
    'valid'             :   1,
    'name'              :   "",
    'phone'             :   "",
    'email'             :   "",
    'regIp'             :   "",
    'regDate'           :   "",
    'lastLoginIp'       :   "",
    'lastLoginDate'     :   "",
}
"""
FORMAT_ADMIN_ACCOUNT_TABLE = "admins:account:%s"
FORMAT_ADMIN_ACCOUNT_TABLE_SET = "admins:accounts:set"

ADMIN_TYPE_SADMIN = "sadmin"
ADMIN_TYPE_ADMIN = "admin"
ADMIN_TYPE_AGENT = "agent"
ADMIN_TYPE_OPERATOR = "operator"
ADMIN_TYPE_SUB_ACCOUNT = "subAccount"
ADMIN_TYPE_TRIAL = "trial"

DEFAULT_SYS_ACCOUNT = 'sysadmin'
DEFAULT_SADMIN_ACCOUNT = 'sadmin'
DEFAULT_TRIAL_ACCOUNT = 'Guest'

"""
管理员子代理账号集合
"""
FORMAT_ADMIN_ACCOUNT_CHIDREN_TABLE = "admins:account:%s:children"
FORMAT_ADMIN_ACCOUNT_SUB_ACCOUNT_TABLE = "admins:account:%s:sub"

"""
管理员子会员id集合
"""
FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE = "admins:account:%s:member:children"

"""
管理员账号权限集合
"""
FORMAT_ADMIN_ACCOUNT_ACCESS_TABLE = "admins:account:%s:access"

"""
管理员操作日志
{
    'account'           :   "",
    'toAccount'         :   "",
    'description'       :   "",
    'datetime'          :   "",
    'ip'                :   ""
}
"""
#日志流水号
FORMAT_ADMIN_OP_LOG_COUNT_TABLE = "admins:op:log:count"
FORMAT_ADMIN_OP_LOG_TABLE = "admins:op:log:%s"
FORMAT_ADMIN_OP_LOG_DATESET_TABLE = "admins:op:log:dateset:%s"

FORMAT_ADMIN_LOG_DESCRIPTION = {
    "/admin/self/modifyPasswd"      :   "(%s) modify self passwd.",
    "/admin/login"                  :   "(%s) login.",
    "/admin/logout"                 :   "(%s) logout.",
    "/admin/ag/create"              :   "(%s) create downline agent(%s) credit(%s %s).",
    "/admin/ag/modify"              :   "(%s) modify downline agent(%s).",
    "/admin/ag/modifyPasswd"        :   "(%s) modify agent(%s)'s password.",
    "/admin/ag/depositMoney"        :   "(%s) deposit (%s %s) to agent(%s).",
    "/admin/ag/drawMoney"           :   "(%s) withdraw (%s %s) from agent(%s).",
    "/admin/ag/freeze"              :   "(%s) make agent(%s) valid(%s).",
    "/admin/ag/member/create"       :   "(%s) create account(%s) credit(%s %s).",
    "/admin/ag/member/modify"       :   "(%s) modify account(%s).",
    "/admin/ag/member/modifyPasswd" :   "(%s) modify account(%s)'s password.",
    "/admin/ag/member/depositMoney" :   "(%s) deposit (%s %s) to account(%s).",
    "/admin/ag/member/drawMoney"    :   "(%s) withdraw (%s %s) from account(%s).",
    "/admin/ag/member/freeze"       :   "(%s) make account(%s) valid(%s).",
    "/admin/currencyDict/create"    :   "(%s) create currency (%s) rate(%s).",
    "/admin/currencyDict/modify"    :   "(%s) modify currency (%s) rate(%s).",
    "/admin/currencyDict/del"       :   "(%s) del currency (%s).",
    "/admin/announce/create"        :   "(%s) create announce (%s).",
    "/admin/announce/del"           :   "(%s) del announce (%s).",
    "/admin/operatorSetting/operatorGolden"     :   "(%s) modify operator (%s) information.",
    "/admin/subAccount/create"      :   "(%s) create sub account(%s).",
    "/admin/subAccount/modify"      :   "(%s) modify sub account(%s).",
    "/admin/subAccount/modifyPasswd":   "(%s) modify sub account(%s)'s password.",
    "/admin/subAccount/freeze"      :   "(%s) make sub account(%s) valid(%s).",
}

"""
存取款记录日志
{
    'account'           :   "",
    'toAccount'         :   "",
    'remark'            :   "",
    'description'       :   "",
    'datetime'          :   "",
    'fromCurrency'      :   "",
    'toCurrency'        :   "",
    'depositCredit'     :   0.0,
    'withDrawCredit'    :   0.0,
    'endCredit'         :   0.0,
    'ip'                :   ""
}
"""
#转账日志流水号
FORMAT_ADMIN_CASH_LOG_COUNT_TABLE = "admins:cash:log:count"
FORMAT_ADMIN_CASH_LOG_TABLE = "admins:cash:log:%s"
FORMAT_ADMIN_CASH_LOG_DATESET_TABLE = "admins:cash:log:dateset:%s"

"""
货币兑率字典
{
    'code'          :   "RMB",
    'name'          :   "RMB",
    'coinRate'      :   1000,
    'lastModifer'   :   '',
    'lastModifyDate':   ''
}
"""
FORMAT_ADMIN_CURRENCY_DICT_TABLE = "currency:dict:%s"
FORMAT_ADMIN_CURRENCY_DICT_TABLE_SET = "currency:dicts:set"

"""
    公告条数
"""
NOTIC_NUMS = 5

"""
服务协议表队列表
"""
#service:protocols:game:$gameId:$channelId:$IP:$PORT
FORMAT_SERVICE_PROTOCOL_TABLE = "service:protocols:game:%s:%s"

HEAD_SERVICE_PROTOCOL_GAME_CLOSE = "close"
HEAD_SERVICE_PROTOCOL_GAME_CONFIG_REFRESH = "configRefresh"
#operatorRefresh|$account
HEAD_SERVICE_PROTOCOL_OPERATOR_REFRESH = "operatorRefresh|%s"
HEAD_SERVICE_PROTOCOL_AGENT_REFRESH = "agRefresh|%s"
#currencyRefresh|$cur
HEAD_SERVICE_PROTOCOL_CURRENCY_REFRESH = "currencyRefresh|"
#memberRefresh|$account
HEAD_SERVICE_PROTOCOL_MEMBER_REFRESH = "memberRefresh|%s"
#noticeRefresh|$noticCount
HEAD_SERVICE_PROTOCOL_GAMEHALL_NOTICE = "noticeRefresh|%s"
#broadcast|$ag|$content|$repeatTimes|$repeatInterval|$id
HEAD_SERVICE_PROTOCOL_AGENT_BROADCAST = "broadcast|%s|%s|%s|%s|%s"
#reSession|$memberAccount|$sessionId
HEAD_SERVICE_PROTOCOL_OPERATOR_RESESSION = "reSession|%s|%s"
#kickMember|$memberAccount
HEAD_SERVICE_PROTOCOL_KICK_MEMBER = "kickMember|%s"
#inCoin|$accountHeader|$coin
HEAD_SERVICE_PROTOCOL_IN_COIN = "inCoin|%s|%s"
#sysStat
HEAD_SERVICE_PROTOCOL_SYS_STATUS = "sysStat"
#joinPartyRoom|$memberAccount|$ag|$rule
HEAD_SERVICE_PROTOCOL_JOIN_PARTY_ROOM = "joinPartyRoom|%s|%s|%s"
#cancelJoinPartyRoom|$memberAccount|$ag|$rule
HEAD_SERVICE_PROTOCOL_CANCEL_JOIN_PARTY_ROOM = "cancelJoinPartyRoom|%s|%s|%s"
#cancelJoinPartyRoom|$memberAccount|$ag|$rule
HEAD_SERVICE_PROTOCOL_DISSOLVE_ROOM = "dissolveRoom|%s"
#createRoom4Other|$memberAccount|$ag|$rule|$ruleText
HEAD_SERVICE_PROTOCOL_CREATE_OTHER_ROOM = "createRoom4Other|%s|%s|%s|%s"
#kickMember4repeat|$memberAccount|$sid
HEAD_SERVICE_PROTOCOL_KICK_MEMBER4REPEAT = "kickMember4repeat|%s|%s"

"""
等待加入娱乐模式列表
'testWaitJoinPartyRoomPlayers:ag:gameID:rule:list'
"""
WAIT_JOIN_PARTY_ROOM_PLAYERS = 'testWaitJoinPartyRoomPlayers:%s:%s:%s:list'

"""
取消加入娱乐模式列表
'testCancelJoinPartyRoomPlayers:list'
"""
CANCEL_JOIN_PARTY_ROOM_PLAYERS = 'testCancelJoinPartyRoomPlayers:list'

"""
账号到所在等待加入娱乐模式列表表名的映射
'testAccount2waitJoinPartyTable:account:str'
"""
ACCOUNT2WAIT_JOIN_PARTY_TABLE = 'testAccount2waitJoinPartyTable:%s:str'

"""
判断娱乐模式匹配是否完成
'testIsMatchFinished:account:str'
"""
IS_MATCH_FINISHED = 'testIsMatchFinished:%s:str'

"""
娱乐模式account到玩家个数的映射
'testPartyAccount2PlayerCount:account:str'
"""
PARTY_ACCOUNT2PLAYER_COUNT = 'testPartyAccount2PlayerCount:%s:str'


"""
广播表
{
    'agent'         :   #代理商名
    'content'       :   #广播内容
    'repeatTimes'   :   #重播次数
    'repeatInterval':   #重播间隔秒数
}
"""
FORMAT_SERVICE_PROTOCOL_CACHE = 'cache%s'
BROADCAST_CONTENT_LEN = 100

DEFAULT_CLOSE_GAME_TICK = 10000

"""
现金账目日统计
"""
FORMAT_ACCOUNT_BET_CASH_DATE_TABLE = "accounts:%s:game:%s:bet:cash:date:%s"
FORMAT_ACCOUNT_PROFIT_CASH_DATE_TABLE = "accounts:%s:game:%s:profit:cash:date:%s"

#非实时临时缓存帐，用户优化报表查询
FORMAT_ACCOUNT_BET_CASH_DATE_T_TABLE = "accounts:%s:game:%s:bet:cash:dateT:%s"
FORMAT_ACCOUNT_PROFIT_CASH_DATE_T_TABLE = "accounts:%s:game:%s:profit:cash:dateT:%s"

FORMAT_CURRENCY_BET_CASH_DATE_TABLE = "currency:%s:game:%s:bet:cash:date:%s"
FORMAT_CURRENCY_PROFIT_CASH_DATE_TABLE = "currency:%s:game:%s:profit:cash:date:%s"

"""
跑马灯通告
{
    'txt'           :   #文本内容，限制512个字
    'date'          :   #发布时间
}
"""
FORMAT_ADMIN_MARQUEE_COUNT = "admins:%s:marquee:count"
FORMAT_ADMIN_MARQUEE = "admins:%s:marquee:%s"

MAX_LEN_TXT_OF_MARQUEE = 4096

# FISHGAME_GAMEID = '1'
# FRUITCASH_GAMEID = '2'
# SOLOKING_GAMEID = '3'
# GOLDSHARK_GAMEID = '4'
MAHJONG_GAMEID = '6'
GAME_IDS = (MAHJONG_GAMEID)

"""
第三方游戏数据
"""
#time -> userTable
FORMAT_USER_EXTERNAL_GAME_SESSION = 'externalGames:session:%s'
#$gameId:$account:$orderId
FORMAT_USER_EXTERNAL_GAME_ORDER = 'externalGames:%s:%s:order:%s'
#$gameId:$orderId
FORMAT_USER_EXTERNAL_GAME_ORDER_SET = 'externalGames:%s:%s:orderIds'
FORMAT_USER_EXTERNAL_GAME_ORDERID = 'externalGames:%s:%s:orderId'

EXTERNAL_PUB_DES_KEY = '12345678'
EXTERNAL_PUB_MD5_KEY = '123123'

FRUITCASH_GAME_DES_KEY = '12345678'
FRUITCASH_GAME_MD5_KEY = '123123'
FRUITCASH_GAME_SETTING_URL = 'http://120.24.61.189:36660/setparams/fruit'

"""
游戏配置表
{
    'id'                :   #
    'oddsOfPumping'     :   #赔率抽水比例
    'outDesKey'         :   #第三方游戏DesKey
    'outMd5Key'         :   #第三方游戏Md5Key
    'lastModifer'       :   '',
    'lastModifyDate'    :   ''
}
"""
FORMAT_GAME_CONFIG_TABLE = "gameconfig:%s"
FORMAT_GAMES_SET = "global:gameset"

"""
网站用户登录Session
{
    'account'       :   #账户名
    'lang'          :   #语言标识
}
"""
FORMAT_WEB_SESSION = "web:session:%s"

"""
玩家玩过的房间列表
player:account1:player2game:list
"""
PLAYER_PLAY_ROOM = 'player:%s:player2game:list'
MAX_PLAY_ROOM_NUM = 200 #房间列表长度

"""
一轮中包含的每局
game:gameNum1:startTime:time1:game2room:list
"""
GAME2ROOM = 'game:%s:startTime:%s:game2room:list'

"""
房间信息（一整轮）
game:gameNum1:startTime:time1:playGame:hash
{
    'player'                    :   side1,account1:side2,account2:side3,account3...
    'startTime'                 :   time1,
    'endTime'                   :   time2,
    'score'                     :   score0 :score1 :score2 :score3...
    'descs'                     :   a,b,c,d:a,b,c,d:a,b,c,d:a,b,c,d...
    'times'                     :   1,2,3,4:1,2,3,4:1,2,3,4:1,2,3,4...
    'tiles'                     :   a,b,c,d:a,b,c,d:a,b,c,d:a,b,c,d...
}
"""
PLAY_GAME_DATA = 'game:%s:startTime:%s:playGame:hash'

"""
某个房间（一局）的游戏信息
game:gameNum1:time:time1:playRoom:hash
{
    'startTime'                 :   time1,
    'endTime'                   :   time2,
    'actionData'                :   回放,
    'score'                     :   score0 :score1 :score2 :score3
    'descs'                     :   a,b,c,d:a,b,c,d:a,b,c,d:a,b,c,d
    'times'                     :   1,2,3,4:1,2,3,4:1,2,3,4:1,2,3,4
    'tiles'                     :   a,b,c,d:a,b,c,d:a,b,c,d:a,b,c,d
}
"""
GAME_ROOM_DATA = 'game:%s:time:%s:playRoom:hash'
MAX_GAME_ROOM_DATA_TIME = 7 * 24 * 60 *60 #房间信息保存时间

"""
玩家输赢情况
player:account:win:gameID1:list
win1:win2:win3
"""
# PLAYER_WIN = 'player:%s:win:%s:list'
# MAX_PLAYER_WIN_NUM = 200 #最大长度

"""
退出的玩家记录
player:account:exitPlayer:hash
{
    'ip'            :       ip,
    'port'          :       port1,
    'game'          :       gameNum1,
    'side'          :       side1
}
"""
EXIT_PLAYER = 'player:%s:exitPlayer:hash'
EXIT_WAITING_TIME = 60 * 60

"""
退出的玩家集合，用于异常退出清除数据
server:server1:waitJoinPlayer:gameID1:set
"""
SERVER_EXIT_PLAYER = 'server:%s:waitJoinPlayer:%s:set'

"""
微信标示ID到账号的映射
unionid2account:weixin:ID1:key
"""
WEIXIN2ACCOUNT = 'unionid2account:weixin:%s:key'

"""
微信账号集合
account4weixin:set
"""
ACCOUNT4WEIXIN_SET = 'account4weixin:set'

"""
游戏可配置的设置
gameConfig:ID1:hash
{
    'gameCount'     :       count1 #一个房卡可打的局数
}
"""
GAME_CONFIG = 'gameConfig:%s:hash'

"""
游戏房间集合
roomNnm:set
"""
GAME_ROOM_SET = 'gameNnm:set'

"""
游戏房间个数
roomMaxNnm:ID1:key
"""
# MAX_ROOM_NUM = 'roomMaxNnm:key'
MAX_COUNT = 999999 + 1 #限制

"""
房间号到服务器的映射
room2server:room1:hesh
{
    'ip'           :       房间所在ip,
    'port'         :       房间所在port,
    'ag'           :       房间所属ag,
    'gameid'       :       房间所属游戏,
    'type'         :       房间类型,
    'gameName'     :       房间名,
    'dealer'       :       房主, 
    'playerCount'  :       玩家数, 
    'maxPlayer'    :       最大玩家数,
}
"""
ROOM2SERVER = 'room2server:%s:hesh'

"""
代理房间列表
ag2room:ag:agID:set
"""
AG2SERVER = 'ag2room:ag:%s:set'

"""
服务器下房间列表
server2room:server:server1:set
"""
SERVER2ROOM = 'server2room:server:%s:set'

"""
GM账号
GMAccount:set
"""
GM_SET = 'GMAccount:set'

PUBLIC_DB = 1

"""
游戏大厅公告列表
notice:day1:ID:list
"""
FORMAT_GAMEHALL_NOTIC_LIST_TABLE = "notice:%s:list"
FORMAT_GAMEHALL_NOTIC_COUNT_TABLE = "notice:%s:count"
"""
公告内容表
{
    'content'       :       公告内容
    'date'          :       公告时间
    'status'        :       公告类型
}
"""
FORMAT_GAMEHALL_NOTIC_TABLE = "notice:%s:%s"

"""
每日玩家数据
playerData4day:$uid:$day:hesh
{
    'playCount'       :       #局数
    'roomCard'        :       #房卡数
}
"""
PLAYER_DAY_DATA = 'playerData4day:%s:%s:hesh'
PLAYER_DAY_DATA_SAVE_TIME = 60 * 24 * 60 * 60

"""
每日总房卡数
allRoomCard4day:day1:key
"""
DAY_ALL_PLAY_ROOM_CARD = 'allRoomCard4day:%s:key'

"""
每日代理总房卡数
allRoomCard4ag4day:ag1:day1:key
"""
DAY_AG_PLAY_ROOM_CARD = 'allRoomCard4ag4day:%s:%s:key'

"""
每日总活跃数
allLogin4day:day1:key
"""
DAY_ALL_LOGIN_COUNT = 'allLogin4day:%s:key'

"""
代理下每日总活跃数
allLogin4ag4day:day1:key
"""
DAY_AG_LOGIN_COUNT = 'allLogin4ag4day:%s:%s:key'

"""
总房卡数
allRoomCard:gameID:key
"""
# ALL_PLAY_ROOM_CARD = 'allRoomCard:%s:key'

"""
回放集合
playerReplaySet:zset
"""
PLAYER_REPLAY_SET = 'playerReplaySet:zset'

PLAYER_REPLAY_NUM = 'playerReplayNum:key'
# MAX_REPLAY_LEN = 2
MAX_REPLAY_LEN = 50 * 10000


"""
服务器状态标识
"""
SERVER_STATUS_KEY = 'game:server:%s:status:key'

"""
休闲模式房间列表
matchGameList:gameID:list
"""
MATCHLIST = 'matchGameList:%s:list'

#玩家正在游戏服务器信息缓存
#有效期5分钟
#格式：memberId
MEMBER_IN_GAME_CACHE = 'memberGameCache:%s'

"""
房间规则
rules:gameID:list
"""
GAME2RULE = 'rules:%s:list'

"""
房间规则详细
ruleDatas:gameID:ruleNum:hesh
{
    title   :   规则名
    type    :   单选1复选0
    rule    :   选项
}
"""
GAME2RULE_DATA = 'ruleDatas:%s:%s:hesh'

"""
消耗房卡数设置
useRoomCardsRule:gameID:list
['描述:消耗房卡数', '1局:1']
"""
USE_ROOM_CARDS_RULE = 'useRoomCardsRule:%s:list'

"""
user4AgentCard
agent:ID:user:ID:cards
"""
USER4AGENT_CARD = 'agent:%s:user:%s:card'

"""
大厅游戏登录session
"""
#time -> userTable
FORMAT_USER_HALL_SESSION = 'hall:session:%s'

"""
Game 游戏表
{
       id        :     游戏ID
       name      :     游戏名称
       version   :     游戏版本号
       web_tag   :     web启动地址
       ipa_tag   :     ios启动标志
       apk_tag   :     android启动标志
       minVersion  :   android版本号
       iosVersion  :   ios版本号
       pack_name   :   游戏包名称
       downloadUrl :   游戏包下载地址
       IPAURL      :   
       apk_size    :   apk大小
       apk_md5     :   apkmd5验证
       game_rule   :   游戏规则(创建房间时使用)
       module_id   :   游戏模块ID

}
"""
GAME_COUNT      =       'games:id:count'
GAME_LIST       =       'games:list'
GAMEID_SET      =       'games:id:set'
GAME_TABLE      =       'games:id:%s'

"""
gameid到redis库映射关系
{
       ip        :     redis的ip
       port      :     redis的port
       num       :     redis的数据库编号
       passwd    :     redis数据库密码，没有则为空字符串
}
"""
GAME2REDIS = 'gameRedisDatas:%s:hesh'

"""
gameid到redis库映射关系，此库为读取用的分库
{
       ip        :     redis的ip
       port      :     redis的port
       num       :     redis的数据库编号
       passwd    :     redis数据库密码，没有则为空字符串
}
"""
GAME2REDIS4READ = 'gameRedisDatas4Read:%s:hesh'

AGENT_CHILD_TABLE   =     'agents:id:%s:child'

"""
开给别人的房间
myRoom4Other:account:$account:list
"""
MY_OTHER_ROOMS = 'myRoom4Other:account:%s:list'

"""
开给别人的房间数据
{
       roomId        :     房间号,
       name          :     房间名称,
       gameType      :     游戏是否开始结束,
       minNum        :     分子,
       maxNum        :     分母,
       time          :     时间戳,
       rule          :     规则字符串,
       accountList   :     玩家账号列表，用;隔开,
}
otherRoomData:account:$account:time:$time:roomId:$roomId:hesh
"""
OTHER_ROOM_DATA = 'otherRoomData:account:%s:time:%s:roomId:%s:hesh'

"""
房间下玩家账号列表
room2accountList:roomId:$roomId:list
"""
ROOM2ACCOUNT_LIST = 'room2accountList:roomId:%s:list'

"""
代理每日总局数
allPlayCount4day:$day:$agId:key
"""
DAY_ALL_PLAY_COUNT = 'allPlayCount4day:%s:%s:key'
DAY_ALL_PLAY_COUNT_SAVE_DAY = 30 * 24 * 60 *60

"""
代理总局数
allPlayCount:$agId:key
"""
ALL_PLAY_COUNT = 'allPlayCount:%s:key'

"""
游戏数据
gameTotalData:$gameId:hesh
{
    $id1     :   $values1,
    $id2     :   $values2,
}
"""
GAME_TOTAL_DATA = 'gameTotalData:%s:hesh'

"""
房卡消耗
playerUseCardData:player:$uid:day:$day:list
&useRoomCard;&type;&playerRoomCard;&roomId;$;others1$;others2
使用房卡数;类型;总房卡数;房间号;其他
type:1普通开房，2代开房间，3解散代开房间，4addRoomCard2Member，5onAppleStorePay，6buyCard
"""
PLAYER_DAY_USE_CARD = 'playerUseCardData:player:%s:day:%s:list'
SAVE_PLAYER_DAY_USE_CARD_TIME = 91 * 24 * 60 * 60

"""
捕鱼ID集合
fish:room:id:set
"""
FISH_ROOM_ID_SETS = 'fish:room:id:set'

"""
捕鱼房间列表
"""
FISH_ROOM_LIST = 'fish:room:lists'

"""
捕鱼频道表
{
    room_id     :   房间ID
    room_name   :   房间名
    min_coin    :   最小携带金币
    max_coin    :   最大携带金币
    base_coin   :   最小底分
    max_base_coin : 最大底分
    step_base_coin : 步长底分
    isTrail     :   是否试玩
    max_player_count : 房间最大人数
    status      :   房间状态
    ip_mask     :   IP掩码做同IP判断用
}
fish:channel:$id:info
"""
FISH_ROOM_TABLE = "fish:channel:%s:info"

"""
捕鱼玩家总投注收益情况
playerFishBetAllData:player:$uid:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
PLAYER_FISH_BET_DATA4ALL = 'playerFishBetAllData:player:%s:hesh'

"""
捕鱼玩家日投注收益情况
playerFishBetDayData:player:$uid:day:$day:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
PLAYER_FISH_BET_DATA4DAY = 'playerFishBetDayData:player:%s:day:%s:hesh'
PLAYER_FISH_BET_DATA4DAY_SAVE_TIME = 91 * 24 * 60 * 60

"""
捕鱼玩家收益明细
playerFishBetDataDetail:player:$uid:list
每次登陆的bet和profit，内为json串
"""
PLAYER_FISH_BET_DATA_DETAIL = 'playerFishBetDataDetail:player:%s:list'
PLAYER_FISH_BET_DATA_DETAILL_MAX_LEN = 100

"""
捕鱼玩家日收益明细
playerFishBetDataDetail:player:$uid:day:$day:list
内为json串
"""
PLAYER_FISH_BET_DATA_DETAIL4DAY = 'playerFishBetDataDetail:player:%s:day:%s:list'
PLAYER_FISH_BET_DATA_DETAIL4DAY_SAVE_TIME = 91 * 24 * 60 * 60
PLAYER_FISH_BET_DATA_DETAIL4DAY_MAX_LEN = 100

"""
捕鱼代理总投注收益情况
agentFishBetAllData:agent:$agentUid:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
AGENT_FISH_BET_DATA4ALL = 'agentFishBetAllData:agent:%s:hesh'

"""
捕鱼代理日投注收益情况
agentFishBetDayData:agent:$agentUid:day:$day:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
AGENT_FISH_BET_DATA4DAY = 'agentFishBetDayData:agent:%s:day:%s:hesh'
AGENT_FISH_BET_DATA4DAY_SAVE_TIME = 91 * 24 * 60 * 60

"""
捕鱼代理收益明细
agentFishBetDataDetail:agent:$agentUid:day:$day:list
每次登陆的bet和profit，内为json串
"""
AGENT_FISH_BET_DATA_DETAIL = 'agentFishBetDataDetail:agent:%s:day:%s:list'
AGENT_FISH_BET_DATA_DETAIL_SAVE_TIME = 91 * 24 * 60 * 60
AGENT_FISH_BET_DATA_DETAILL_MAX_LEN = 100

"""
捕鱼总投注收益情况
allFishBetAllData:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
ALL_FISH_BET_DATA4ALL = 'allFishBetAllData:hesh'

"""
捕鱼日投注收益情况
allFishBetDayData:day:$day:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
ALL_FISH_BET_DATA4DAY = 'allFishBetDayData:day:%s:hesh'
ALL_FISH_BET_DATA4DAY_SAVE_TIME = 91 * 24 * 60 * 60

"""
捕鱼收益明细
allFishBetDataDetail:day:$day:list
每次登陆的bet和profit，内为json串
"""
ALL_FISH_BET_DATA_DETAIL = 'allFishBetDataDetail:day:%s:list'
ALL_FISH_BET_DATA_DETAILL_MAX_LEN = 100
ALL_FISH_BET_DATA_DETAILL_SAVE_TIME = 91 * 24 * 60 * 60

"""
捕鱼房间投注收益情况
fishBetAllData4Room:room:$roomId:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
FISH_BET_DATA4ROOM = 'fishBetAllData4Room:room:%s:hesh'

"""
捕鱼日房间投注收益情况
fishBetDayData4Room:room:$roomId:day:$day:hesh
{
    bet     :       $bet
    profit  :       &profit
}
"""
FISH_BET_DATA4DAY4ROOM = 'fishBetDayData4Room:room:%s:day:%s:hesh'
FISH_BET_DATA4DAY4ROOM_SAVE_TIME = 91 * 24 * 60 * 60

"""
捕鱼房间收益明细
fishBetDataDetail4Room:room:$roomId:day:$day:list
每次登陆的bet和profit，内为json串
"""
FISH_BET_DATA_DETAIL4ROOM = 'fishBetDataDetail4Room:room:%s:day:%s:list'
FISH_BET_DATA_DETAILL4ROOM_MAX_LEN = 100
FISH_BET_DATA_DETAILL4ROOM_SAVE_TIME = 91 * 24 * 60 * 60

"""
捕鱼在线列表
"""
ONLINE_ACCOUNTS_TABLE4FISH = "online4Fish:accounts"

AGENT2PARENT     =    'agents:id:%s:parent'

"""
GM操作记录
GMControlData:uid:$uid:list
记录gm功能操作记录，为json串，包含：时间，gameid，操作命令，房间号
"""
GM_CONTROL_DATA = 'GMControlData:uid:%s:list'
GM_CONTROL_DATA_MAX_LEN = 100

AGENT_TABLE         =     'agents:id:%s'

# 俱乐部砖石消耗日总数
CLUB_ROOM_CARDS_DAY_TOTAL = "club:roomCards:day:%s:%s:total"
# 俱乐部砖石消耗总数
CLUB_ROOM_CARDS_ALL_TOTAL = "club:roomCards:all:%s:total"


#游戏每天消耗砖石数
GAME_ROOMCARDS_DAY_TOTAL = "game:roomCards:%s:%s:total"

#游戏砖石消耗总数
GAME_ROOMCARDS_ALL_TOTAL = "game:roomCards:%s:total"
