#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: Describe module function
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from optparse import OptionParser
_cmd_parser = OptionParser(usage="usage: %prog [options]")
_opt = _cmd_parser.add_option
_opt("-c", "--currency", action="store", type="string", default='GUEST', help="Service port.")
_opt("-p", "--port", action="store", type="int", default=9601, help="Service port.")
_opt("-i", "--address", action="store", type="string", default="192.168.0.155", help="Service ip.")
_opt("-n", "--name", action="store", type="string", default="game test", help="Game name tag.")
_cmd_options, _cmd_args = _cmd_parser.parse_args()

from twisted.python import log
from common.log import HourLogFile
#log.startLogging(HourLogFile('ghost_poker_server_%s_%s.log'%(_cmd_options.address, _cmd_options.port), 'log'))

import os
if os.name == 'nt':
    sys.path.insert(0, "win32")
    sys.path.insert(0, 'win32/lib')
    from twisted.internet import iocpreactor
    iocpreactor.install()
else:
    from twisted.internet import epollreactor
    epollreactor.install()

print('+++++++')
from twisted.internet import reactor
from poker.server import PokerServer
serviceTag = '%s:%s:%s'%(_cmd_options.currency, _cmd_options.address, _cmd_options.port)
print(serviceTag)
print('reactor.listenTCP(%s' % _cmd_options.port, 'PokerServer("ws://%s:%s"' % (_cmd_options.address, _cmd_options.port), 'debug=False', 'debugCodePaths=False', 'skipViolation=False', 'serviceTag=%s' % serviceTag)
reactor.listenTCP(_cmd_options.port, PokerServer("ws://%s:%s"%(_cmd_options.address, _cmd_options.port), debug=False, debugCodePaths=False, skipViolation=False, serviceTag=serviceTag))
print('-------------')
reactor.run()
