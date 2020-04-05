# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: Pipo
Date: $Date$
Revision: $Revision$

Description: Redis
"""
import redis

redisdb = None

def getInst(dbNum):
    global redisdb
    redisdb = redis.ConnectionPool(host="127.0.0.1", port=6379, db=dbNum, password='168joyvick')
    redisdb4Read = redis.ConnectionPool(host="127.0.0.1", port=6379, db=dbNum, password='168joyvick') #读库地址
    redisData = redis.Redis(connection_pool=redisdb)
    redisData.connection_read_pool = redisdb4Read
    return redisData
