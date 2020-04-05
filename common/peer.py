# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: TV peer
"""

from log import log, LOG_LEVEL_RELEASE, LOG_LEVEL_ERROR
from autobahn.twisted.websocket import WebSocketServerProtocol
from gameobject import GameObject
import time
import consts

import traceback
import struct
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

KICK_OUT_TICK = 2 * 60 * 60 * 1000
# KICK_OUT_TICK = 3 * 60 * 1000
PACKET_TICK_LIMIT = 200
PACKET_COUNT_LIMIT = 18
MAX_INVALID_COUNT = 300

class Peer(WebSocketServerProtocol, GameObject):
    def __init__(self):
        super(Peer, self).__init__()
        self.reset()
        self.game = None
        self.controlPlayer = self #控制者，非一控四测试模式时为自己

    def reset(self):
        """
        Reset peer data
        """
        self.hashKey = None
        self.descTxt = None
        self.protoTag = None
        self.ip = None
        self.port = None
        self.isConnected = False
        self.lastPacketTimestamp = 0

        self.firstPacketTimestamp = 0
        self.firstPacketClientTimestamp = 0
        self.packetClientTimestamps = []
        self.invalidCount = 0

    def onConnect(self, request):
        super(Peer, self).onConnect(request)

        self.hashKey = hash(request.peer)
        self.descTxt = str(request.peer)
        self.protoTag, self.ip, self.port = self.descTxt.split(':')
        log(u'client[%s] hash[%s] try connecting.'%(self.descTxt, self.hashKey), LOG_LEVEL_RELEASE)

    def onOpen(self):
        super(Peer, self).onOpen()
        if self.hashKey:
            log(u'client[%s] handshake finished.'%(self.descTxt), LOG_LEVEL_RELEASE)
            self.factory.addPeer(self)
            self.isConnected = True
            self.lastPacketTimestamp = self.factory.getTimestamp()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            return
        log(u'received client[%s] data'%(self.descTxt), LOG_LEVEL_RELEASE)
        isValidTimestamp = False
        try:
            compressIdx = len(payload)/3
            isCompresed = ord(payload[compressIdx])
            isCheckTimestamp = ord(payload[compressIdx+1])
            if isCheckTimestamp:
                timestamp, = struct.unpack('>Q', payload[compressIdx+2:compressIdx+10])
                if not self.checkPacketTimestamp(timestamp):
                    raise Exception('timestamp[%s] invalid.'%(timestamp))
                isValidTimestamp = True
                payload = payload[:compressIdx] + payload[compressIdx+10:]
            else:
                payload = payload[:compressIdx] + payload[compressIdx+2:]
            if isCompresed:
                mstream = StringIO(payload)
                f = gzip.GzipFile(mode='rb', fileobj=mstream)
                payload = f.read()
                f.close()
            self.factory.resolveMsg(self, payload)
        except Exception, e:
            for tb in traceback.format_exc().splitlines():
                log(tb, LOG_LEVEL_ERROR)
            self.invalidCounter('Received or Resolved packet error[%s]'%(e))
            return
        if isValidTimestamp:
            self.packetClientTimestamps.append(timestamp)
            if not self.firstPacketTimestamp:
                self.firstPacketTimestamp = self.factory.getTimestamp()
                self.firstPacketClientTimestamp = timestamp

        #self.factory.recvPacket(self, payload)

    def onClose(self, wasClean, code, reason):
        super(Peer, self).onClose(wasClean, code, reason)
        if self.isConnected:
            log(u'client[%s] disconnected reason[%s]'%(self.descTxt, reason), LOG_LEVEL_RELEASE)
            self.factory.removePeer(self)
            self.reset()
        else:
            log(u'client[%s] disconnected error:no found descTxt'%(self.descTxt), LOG_LEVEL_RELEASE)

    def drop(self, reason, reasonCode):
        log(u'try disconnect client[%s] reason[%s]'%(self.descTxt, reason), LOG_LEVEL_RELEASE)
        self.dropConnection(False)

    def isTimeout(self, timestamp):
        return timestamp - self.lastPacketTimestamp > KICK_OUT_TICK

    def onCheck(self, timestamp):
        # if self.isTimeout(timestamp):
            # self.lastPacketTimestamp = self.factory.getTimestamp()
            # self.drop("received packet time out")
            # return False
        return True

    def checkPacketTimestamp(self, clientTimestamp):
        if self.firstPacketTimestamp:
            deltaTime = clientTimestamp - self.firstPacketClientTimestamp
#            curTime = self.factory.getTimestamp() + 1000
#            clientTime = self.firstPacketTimestamp + deltaTime
            #log('Packet check: clientTime[%s] curTime[%s] clientCurTime[%s] handshakeTime[%s]'% \
            #    (clientTimestamp, curTime, clientTime, self.firstPacketTimestamp))
#            if curTime < clientTime:
#                log('Server timestamp[%s] < Client timestamp[%s].'%(curTime, clientTime), LOG_LEVEL_RELEASE)
#                return False
            idx = 0
            for i in xrange(len(self.packetClientTimestamps)-1, -1, -1):
                if clientTimestamp - self.packetClientTimestamps[i] > PACKET_TICK_LIMIT:
                    idx = i + 1
                    break
            del self.packetClientTimestamps[:idx]
            #log('packetClientTimestamps[%s]'%(self.packetClientTimestamps))
            return len(self.packetClientTimestamps) < PACKET_COUNT_LIMIT
        return True

    def invalidCounter(self, reason):
        self.invalidCount += 1
        log(u'client[%s] invalid reason[%s] count[%s]'%(self.descTxt, reason, self.invalidCount), LOG_LEVEL_RELEASE)
        if self.invalidCount >= MAX_INVALID_COUNT:
            self.drop('Too many invalid count.', consts.DROP_REASON_INVALID)

    def onSkipViolationProtocol(self):
        #self.onMessage(self.data, self.message_is_binary)
        self.data = b''

