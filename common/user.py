# -*- coding: utf-8 -*-
from gameobject import GameObject

class User(GameObject):
    def __init__(self, peer, uid, nickname, coin, diamond, vip):
        self.peer = peer
        self.uid = uid
        self.nickname = nickname
        self.coin = coin
        self.diamond = diamond
        self.vip = vip
        self.player = None

    def __repr__(self):
        return 'User(peer(%s) uid(%s) nickname(%s) coin(%d) diamond(%d) vip(%d) player[%s])'%(self.peer.descTxt, self.uid, self.nickname, self.coin, self.diamond, self.vip, self.player)
    __str__ = __repr__