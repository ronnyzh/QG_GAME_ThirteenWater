# -*- coding: utf-8 -*-
"""
B{[公共]}常量定义模块。
"""
LANGUAGE_CODE = 'utf-8'

# game states
GAME_STATE_IDLE = 0    # waiting for players to enter
GAME_STATE_START = 1   # server players are playing game

# unknown side
SIDE_UNKNOWN = -1

DROP_REASON_INVALID = 0
DROP_REASON_TIMEOUT = 1
DROP_REASON_FREEZE = 2
DROP_REASON_CLOSE_SERVER = 3
DROP_REASON_REPEAT_LOGIN = 4

LAG_MS = 15 * 1000

LANG_CODE = 'utf8'
ERR_MSG ={
        'typeErr':'控制命令类型错误'.decode(LANG_CODE),
        'cardErr':'不存在的牌'.decode(LANG_CODE),
        'sideErr':'不存在的边'.decode(LANG_CODE),
        'lenErr' :'牌长度不对'.decode(LANG_CODE)
    }

