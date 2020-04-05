#!/usr/bin/env python
# -*- coding:utf-8 -*-

""" 
    统计数据
    common_game.py
        onGameStart
        
        removeRoom
    
    common_server.py
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
"""

import datetime
import traceback

REDIS_KEY = 'gameRedisDatas2Mysql:hesh'
CUSHION_QUEUE = 'task:redis:mysql:queue'


def dig_game_start(game):
    """ 
        游戏开始
    """
    try:
        if not game.gameStartTime:
            return
        redis = game.server.getMysqlRedis()
        room_id = game.roomId
        game_id = game.server.ID
        users = [player.account for player in game.getPlayers()]
        users = ','.join(users)
        club_id = 0
        stamp = str(game.gameStartTime/1000)
        room_id = str(room_id) + '-' + stamp
        cur_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        value = 'dig_game_start:' + room_id + '|' + str(game_id) + '|' + cur_time + '|' + users + '|' + str(club_id)
        redis.rpush(CUSHION_QUEUE, value)
        return stamp
    except Exception, ex:
        traceback.print_exc()


def dig_game_end(game):
    """ 
        游戏结束
    """
    try:
        if not game.gameStartTime:
            return
        redis = game.server.getMysqlRedis()
        stamp = str(game.gameStartTime/1000)
        room_id = game.roomId
        game_id = game.server.ID
        # users = [player.account for player in game.getPlayers()]
        # users = ','.join(users)
        small_round = game.curGameCount
        cost_diamond = game.needRoomCards
        club_id = 0
        room_id = str(room_id) + '-' + stamp
        cur_time = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
        value = 'dig_game_end:' + room_id + '|' + str(game_id) + '|' + cur_time + '|' + str(small_round) + '|' + str(cost_diamond) + '|' + str(club_id)
        redis.rpush(CUSHION_QUEUE, value)
    except Exception, ex:
        traceback.print_exc()


def dig_login_times(user_id):
    """ 
        登陆大厅
    """
    return
    cur_time = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
    value = "dig_hall_login:" + str(user_id) + "|" + cur_time


