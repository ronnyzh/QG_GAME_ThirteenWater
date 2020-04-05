#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    手动关闭某些服务器
    python close_server.py -g $gameId -n $IP
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from optparse import OptionParser
_cmd_parser = OptionParser(usage="usage: %prog [options]")
_opt = _cmd_parser.add_option
_opt("-n", "--name", action="store", type="string", default='', help="Service find string.")
_opt("-g", "--gameId", action="store", type="string", default='1007', help="Game id.")
_cmd_options, _cmd_args = _cmd_parser.parse_args()

from common.common_db_define import *
from common.db_utils import sendProtocol2GameService
import redis_instance

redis = redis_instance.getInst(1)
sendProtocol2GameService(redis, _cmd_options.gameId, HEAD_SERVICE_PROTOCOL_GAME_CLOSE, _cmd_options.name)
