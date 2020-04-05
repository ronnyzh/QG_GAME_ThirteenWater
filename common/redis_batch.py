#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: $Author$
@Date: $Date$
@version: $Revision$

Description:
    Redis批处理导入服务端
"""

import gameobject
from redis import Redis, Connection
from redis.exceptions import (
    ConnectionError,
    TimeoutError,
)

SYM_EMPTY = ''

class RedisBatch(Redis):
    """
    自实现Redis批量插入库
    """
    def __init__(self):
        """
        初始仅需要初始化一个Redis.Connection，无需连接，只需要打包数据接口即可
        """
        self.packer = Connection()
        self.__reset()

    def __reset(self):
        """
        重置数据
        """
        self.bufferList = []
        self.buffer = []
        self.bufLen = 0
        self.countCommands = 0

    def dumpDB(self, redis):
        """
        把缓存下来的Redis协议一次批量入库，若存在缓存
        """
        tmpBuf = self.bufferList
        tmpCount = self.countCommands
        self.__reset()
        if tmpBuf:
            pool = redis.connection_pool
            connection = pool.get_connection('')
            try:
                connection.send_packed_command(tmpBuf)
                for i in xrange(tmpCount):
                    redis.parse_response(connection, '')
            except (ConnectionError, TimeoutError) as e:
                connection.disconnect()
                if not connection.retry_on_timeout and isinstance(e, TimeoutError):
                    raise
                connection.send_packed_command(tmpBuf)
                for i in xrange(tmpCount):
                    redis.parse_response(connection, '')
            finally:
                pool.release(connection)
        #subprocess.Popen('cat %s | ./redis-cli -pipe -n 15 -a '%(IP, BASE_PORT, code, NAME), shell=True)

    def execute_command(self, *args, **options):
        """
        执行命令处理重载，这里不需要
        @param p1:
        @type p1:
        @return:
        @rtype:
        """
        for chunk in self.packer.pack_command(*args):
            self.buffer.append(chunk)
            self.bufLen += len(chunk)

        if self.bufLen > 6000:
            self.bufferList.append(SYM_EMPTY.join(self.buffer))
            self.bufLen = 0
            self.buffer = []
        self.countCommands += 1

