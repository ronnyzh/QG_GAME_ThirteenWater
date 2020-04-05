#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    Client peer
"""

from log import log, LOG_LEVEL_RELEASE
from autobahn.twisted.websocket import WebSocketClientProtocol
from gameobject import GameObject
import time
import struct
import gzip
import StringIO

import baseProto_pb2
import poker_pb2

KICK_OUT_TICK = 300000
MAX_INVALID_COUNT = 30

class Peer(WebSocketClientProtocol, GameObject):
    def __init__(self):
        super(Peer, self).__init__()
        self.reset()

    def reset(self):
        """
        Reset peer data
        """
        self.hashKey = None
        self.descTxt = None
        self.lastPacketTimestamp = 0

        self.firstPacketTimestamp = 0
        self.firstPacketClientTimestamp = 0
        self.packetClientTimestamps = []
        self.invalidCount = 0

        self.JoinRule = '[1,1]'

    def onConnect(self, request):
        super(Peer, self).onConnect(request)

        self.hashKey = hash(request.peer)
        self.descTxt = str(request.peer)
        log(u'server[%s] hash[%s] try connecting.'%(self.descTxt, self.hashKey), LOG_LEVEL_RELEASE)

    def onOpen(self):
        super(Peer, self).onOpen()
        if self.hashKey:
            log(u'server[%s] handshake finished.'%(self.descTxt), LOG_LEVEL_RELEASE)
            self.factory.addPeer(self)
            self.lastPacketTimestamp = self.factory.getTimestamp()

        proto = baseProto_pb2.C_S_DebugConnecting()
        proto.account = self.factory.account
        proto.passwd = self.factory.passwd
        proto.mode = 0
        proto.roomSetting.action = self.factory.regAction
        proto.roomSetting.roomid = self.factory.roomId
        proto.roomSetting.rule = self.JoinRule
        self.factory.sendOne(self, proto)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            return
        log(u'received server[%s] data:'%(self.descTxt), LOG_LEVEL_RELEASE)

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
                mstream = StringIO.StringIO(payload)
                f = gzip.GzipFile(mode='rb', fileobj=mstream)
                payload = f.read()
                f.close()
        except Exception, e:
            self.invalidCounter('Received packet error[%s]'%(e))
            return
        if isValidTimestamp:
            self.packetClientTimestamps.append(timestamp)
            if not self.firstPacketTimestamp:
                self.firstPacketTimestamp = self.factory.getTimestamp()
                self.firstPacketClientTimestamp = timestamp

        senderMgr, recvMgr = self.factory.getResolverMgr()
        unpackRes = recvMgr.unpackCall(self, payload)
        if not unpackRes:
            self.drop(u'Invalid data for received.')
        elif self.factory.isValidPacket(unpackRes[0]):
            self.lastPacketTimestamp = self.factory.getTimestamp()

    def onClose(self, wasClean, code, reason):
        super(Peer, self).onClose(wasClean, code, reason)
        if self.hashKey:
            log(u'server[%s] disconnected reason[%s]'%(self.descTxt, reason), LOG_LEVEL_RELEASE)
            self.factory.removePeer(self)
            self.reset()

    def drop(self, reason):
        log(u'try disconnect server[%s] reason[%s]'%(self.descTxt, reason), LOG_LEVEL_RELEASE)
        self.dropConnection(False)

    def isTimeout(self, timestamp):
        return timestamp - self.lastPacketTimestamp > KICK_OUT_TICK

    def checkPacketTimestamp(self, clientTimestamp):
        if self.firstPacketTimestamp:
            deltaTime = clientTimestamp - self.firstPacketClientTimestamp
            if self.factory.getTimestamp() < self.firstPacketTimestamp + deltaTime:
                return False
            for i in xrange(len(self.packetClientTimestamps)-1, -1, -1):
                if clientTimestamp - self.packetClientTimestamps[i] > PACKET_TICK_LIMIT:
                    break
            del self.packetClientTimestamps[:i]
            return len(self.packetClientTimestamps) < PACKET_COUNT_LIMIT
        return True

    def invalidCounter(self, reason):
        self.invalidCount += 1
        log(u'client[%s] invalid reason[%s] count[%s]'%(self.descTxt, reason, self.invalidCount), LOG_LEVEL_RELEASE)
        if self.invalidCount >= MAX_INVALID_COUNT:
            self.drop('Too many invalid count.')

    def onSkipViolationProtocol(self):
        self.onMessage(self.data, self.message_is_binary)
        self.data = b''