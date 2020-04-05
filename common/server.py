# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: Server factory
"""

from autobahn.twisted.websocket import WebSocketServerFactory
from twisted.internet.task import LoopingCall
from common.websocket import create_connection
from log import log, LOG_LEVEL_RELEASE, LOG_LEVEL_ERROR
import net_resolver_pb
from gameobject import GameObject
from peer import Peer
import time
import hashlib
import dynamic
import traceback

CHECK_PEER_TICK = 5000
TICK_PEERS_COUNT = 10
MAX_PACKET_PER_TICK = 100

# 动态加载时间
HOT_UPDATE_FILE_TIME = 1000
WS_ADDRESS = "ws://127.0.0.1:10079"
WS_TIMEOUT = 5

class Server(WebSocketServerFactory, GameObject):
    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
        self.peers = {}
        self.peerList = []
        self.tickPeerIdx = 0
        self.initNetManager()
        self.tickTimer = LoopingCall(self.onTick)
        self.tickTimer.start(0.2, False)
        self.lastCheckTimestamp = self.getTimestamp()

        self.dynamic = dynamic.Dynamic
        self.dynamic_md5 = self.fileMd5Check()
        self.msgBuffers = []

        self.wsConn = create_connection(WS_ADDRESS, timeout=WS_TIMEOUT)

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
        self.send(self.peerList, protocol_obj)

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
        self.peerList.append(peer)
        self.onAddPeer(peer)

    def removePeer(self, peer):
        assert peer.hashKey in self.peers, "Peer[%s] is not existed."%(peer.descTxt)
        #self.resolvePacketOnPeerClose(peer)
        self.onRemovePeer(peer)
        self.peerList.remove(peer)
        del self.peers[peer.hashKey]

    def isValidPacket(self, msgName):
        raise 'abstract interface'

    def fileMd5Check(self):
        """ 检查文件的MD5值

        :return:
        """
        rf = open("./common/dynamic.py", 'rb')
        m = hashlib.md5()
        while True:
            b = rf.read(8096)
            if not b:
                break
            m.update(b)
        rf.close()
        return m.hexdigest()

    def reloadDynamic(self):
        """ 判断文件是否更改，更改了就直接进行reload

        :return:
        """
        newMd5 = self.fileMd5Check()
        if self.dynamic_md5 != newMd5:
            print(u"检查到文件存在更改， 正在进行重载...")
            reload(dynamic)
            self.dynamic = dynamic.Dynamic
            self.dynamic_md5 = newMd5
            print(u"重载完毕")

    def onTick(self):
        timestamp = self.getTimestamp()
        if timestamp - self.lastCheckTimestamp > HOT_UPDATE_FILE_TIME:
            self.reloadDynamic()
        try:
            #self.resolvePacket(timestamp)
            self.onRefresh(timestamp)
        except:
            for tb in traceback.format_exc().splitlines():
                log(tb, LOG_LEVEL_ERROR)

    def onCheck(self, timestamp):
        self.lastCheckTimestamp = timestamp
        countPeers = len(self.peerList)
        if countPeers <= 0:
            return
        if self.tickPeerIdx >= countPeers:
            self.tickPeerIdx = 0
        peers = self.peerList[self.tickPeerIdx:self.tickPeerIdx+TICK_PEERS_COUNT]
        self.tickPeerIdx += TICK_PEERS_COUNT

        for peer in peers:
            peer.onCheck(timestamp)

    def onRefresh(self, timestamp):
        if timestamp - self.lastCheckTimestamp > CHECK_PEER_TICK:
            self.onCheck(timestamp)

    def recvPacket(self, peer, buf):
        self.msgBuffers.append((peer, buf))

    def resolveMsg(self, peer, msgData):
        recvMgr = self.recverMgr
        unpackRes = recvMgr.unpackCall(peer, msgData)
        if not unpackRes:
            peer.invalidCounter('Invalid data for resolved.')
        elif self.isValidPacket(unpackRes[0]):
            peer.lastPacketTimestamp = self.getTimestamp()

    def resolvePacket(self, timestamp):
        recvMgr = self.recverMgr
        #log(u'Packet count[%d]'%(len(self.msgBuffers)))
        for peer, packet in self.msgBuffers[:MAX_PACKET_PER_TICK]:
            unpackRes = recvMgr.unpackCall(peer, packet)
            if not unpackRes:
                peer.invalidCounter('Invalid data for resolved.')
            elif self.isValidPacket(unpackRes[0]):
                peer.lastPacketTimestamp = timestamp
        self.msgBuffers = self.msgBuffers[MAX_PACKET_PER_TICK:]

    def resolvePacketOnPeerClose(self, peer):
        recvMgr = self.recverMgr
        for buf in self.msgBuffers[:]:
            if buf[0] == peer:
                recvMgr.unpackCall(buf[0], buf[1])
                self.msgBuffers.remove(buf)
