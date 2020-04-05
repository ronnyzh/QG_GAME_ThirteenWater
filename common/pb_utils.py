#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    protobuf utilities
"""

def pbGetMahjong(getMahjong, chair, getType, mahjongs):
    data = getMahjong.add()
    data.side = chair
    data.getType = getType
    data.mahjong.extend(mahjongs)
    return data

def pbPlayMessage(resp, game, side, score, bird, player = None, hu = None):
    resp.kong = game.giveKongCount[side]
    resp.concealedKong.extend(game.players[side].mahjongList.concealedKongTiles)
    resp.exposed.extend(game.players[side].mahjongList.kongTiles)
    resp.score = score
    resp.bird = bird
    resp.nickname = game.players[side].nickname
    resp.side = side
    resp.mahjong.extend(game.players[side].mahjongList.getTiles())
    resp.points = game.points[side]
    resp.pong.extend(game.players[side].mahjongList.pongTiles)
    if hu:
        resp.hu = hu
    return resp

def pbWinData(resp, kongScore, birdScore, huScore, side, nickname):
    resp.kong = kongScore
    resp.bird = birdScore
    resp.hu = huScore
    resp.nickname = nickname
    resp.side = side
    return resp

def pbHuData(resp, huMahjong, mahjongList, huSide, bird):
    resp.huMahjong = huMahjong
    if mahjongList:
        resp.mahjong.extend(mahjongList)
    resp.huSide = huSide
    resp.bird = bird
    return resp

def pbPlayedData(resp, mySide, side, game):
    player = game.players[side]
    concealedKongTiles = player.mahjongList.concealedKongTiles
    playedData = resp.add()
    playedData.side = side
    playedData.kong.extend(player.mahjongList.kongTiles)
    playedData.pong.extend(player.mahjongList.pongTiles)
    playedData.playedTile.extend(player.mahjongList.playedTile)
    # 暗杠
    # if player.account != player.account:
        # concealedKongTiles = [''] * len(concealedKongTiles)
    playedData.concealedKong.extend(concealedKongTiles)
    if side != mySide:
        playedData.isOnline = game.isInGame[playerSide]
    else:
        playedData.isOnline = True
    return resp

def pbPlayerInfo(resp, game, side, isNeedMyData = False):
    player = game.players[side]
    resp.side = side
    resp.nickname = player.nickname
    resp.coin = player.totalGameScore
    resp.ip = player.ip #gamePlayer.region
    resp.sex = player.sex
    resp.headImgUrl = player.headImgUrl
    if isNeedMyData:
        resp.roomCards = player.roomCards
        resp.isGM = player.isGM
        resp.id = int(player.uid)
        resp.account = player.account
    return resp

def pbRoomInfo(resp, server, game):
    resp.roomId = game.roomId
    resp.roomName = game.roomName.decode('utf-8')
    resp.timestamp = game.server.getTimestamp()
    resp.roomSetting = game.ruleDescs
    resp.count = game.gameTotalCount
    if game.ownner:
        resp.ownerSide = 100
    else:
        resp.ownerSide = 0
    resp.currentRound = game.curGameCount
    resp.playerCount = game.maxPlayerCount
    resp.cardCount = game.dealMgr.getTotalCards()
    if game.extendStr:
        resp.extend = game.extendStr
    return resp

def pbBalanceData(player, resp):
    resp.nickname = player.nickname
    resp.side = player.chair
    resp.id = int(player.uid)
    if player.game and player.game.ownner:
        resp.isOwner =False
    else:
        resp.isOwner = (player.chair == 0)
    resp.roomSetting = player.game.ruleDescs
    resp.timestamp = player.game.server.getTimestamp()
    resp.headImgUrl = player.headImgUrl
    resp.isDealer = (player.chair == player.game.dealerSide)
    return resp

