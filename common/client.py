#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    client factory
"""

from autobahn.twisted.websocket import WebSocketClientFactory
from twisted.internet.task import LoopingCall

from log import log, LOG_LEVEL_RELEASE
import net_resolver_pb
from gameobject import GameObject
from client_peer import Peer
import time

CHECK_PEER_TICK = 60000

class Client(WebSocketClientFactory, GameObject):
    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        self.peers = {}
        self.initNetManager()
        #self.tickTimer = LoopingCall(self.onTick)
        #self.tickTimer.start(0.2, False)
        self.lastTimestamp = self.getTimestamp()

    def getTimestamp(self):
        return int(time.time()*1000)

    def logPrefix(self):
        """
        Describe this factory for log messages.
        """
        return self.__class__.__name__

    def sendData(self, peer, data):
        log(u'Send to [%s]'%(peer.descTxt))
        peer.sendMessage(data, True)

    def sendOne(self, peer, protocol_obj):
        assert isinstance(peer, Peer)
        self.sendData(peer, self.senderMgr.pack(protocol_obj))

    def send(self, peers, protocol_obj, excludes=()):
        data = self.senderMgr.pack(protocol_obj)
        for peer in peers:
            if peer not in excludes:
                self.sendData(peer, data)

    def sendAll(self, protocol_obj):
        self.send(self.peers.values(), protocol_obj)

    def getResolverMgr(self):
        return self.senderMgr, self.recverMgr

    def initNetManager(self):
        self.senderMgr = net_resolver_pb.SendManager()
        self.recverMgr = net_resolver_pb.RecvManager()
        self.registerProtocolResolver()

    def registerProtocolResolver(self):
        raise 'abstract interface'

    def onAddPeer(self, peer):
        raise 'abstract interface'

    def onRemovePeer(self, peer):
        raise 'abstract interface'

    def addPeer(self, peer):
        assert peer.hashKey not in self.peers, "Peer[%s] is existed."%(peer.descTxt)
        self.peers[peer.hashKey] = peer
        self.onAddPeer(peer)

    def removePeer(self, peer):
        assert peer.hashKey in self.peers, "Peer[%s] is not existed."%(peer.descTxt)
        self.onRemovePeer(peer)
        del self.peers[peer.hashKey]

    def isValidPacket(self, msgName):
        raise 'abstract interface'

    def onTick(self):
        timestamp = self.getTimestamp()
        self.onRefresh(timestamp)

    def onCheck(self, timestamp):
        removePeers = []
        for peer in self.peers.itervalues():
            if peer.isTimeout(timestamp):
                removePeers.append(peer)
        for peer in removePeers:
            peer.drop("received packet time out")
        self.lastTimestamp = timestamp

    def onRefresh(self, timestamp):
        if timestamp - self.lastTimestamp > CHECK_PEER_TICK:
            self.onCheck(timestamp)
