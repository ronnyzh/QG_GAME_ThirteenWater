#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Copyright (c) 2018 yu.liu <showmove@qq.com>
# All rights reserved

""" 动态更新游戏数据统计


"""
import time
import traceback
import trasfer_pb2

class Dynamic(object):


    @classmethod
    def useRoomCards(cls, game, server, user_id, club_number):
        """ 消耗房卡之后的操作

        :param game:
        :param server:
        :param player:
        :return:
        """
        try:
            gameNumber = "%s-%s-%s" % (server.ID, game.curTimeGenerate, game.roomId)
            print("开始执行远程写入数据")
            agent_id = game.parentAg
            game_id = server.ID
            room_cards = game.needRoomCards
            room_id = game.roomId
            create_time = int(time.time())
            insertSql = """
            insert into `lj_game`.`room_cards` (
              `cards`,
              `room_id`,
              `agent_id`,
              `user_id`,
              `game_id`,
              `club_number`,
              `room_number`,
              `create_time`
            ) 
            values
              (
                '%s',
                '%s',
                '%s',
                '%s',
                '%s',
                '%s',
                '%s',
                '%s'
              ) ;
            """ % (room_cards, room_id, agent_id, user_id,
                   game_id, club_number, gameNumber,create_time)
            # print(insertSql)
            # print(insertSql)
            resp = trasfer_pb2.S_S_MysqlCommandsData()
            # resp.commands.append(insertSql)
            commands = resp.commands.add()
            commands.commands = insertSql
            commands.type = 1
            server.wsConn.send_binary(server.senderMgr.pack(resp))
            print("开始执行远程写入数据, 执行结束")
        except Exception as err:
            traceback.print_exc()

    @classmethod
    def startGame(cls, game, server, player):
        """ 开始游戏的操作

        :param game:
        :param server:
        :param player:
        :return:
        """
        try:
            curTime = int(time.time())
            gameNumber = "%s-%s-%s" % (server.ID, game.curTimeGenerate, game.roomId)
            if game.curGameCount < 1 and game.players[0] == player:
                insertRecordSql = """
                        INSERT INTO `game_record` (
                          `game_id`,
                          `owner`,
                          `start_time`,
                          `end_time`,
                          `room_number`,
                          `game_type`,
                          `game_number`,
                          `create_time`,
                          `total_round`
                        ) 
                        VALUES
                          (
                            '%s',
                            '%s',
                            '%s',
                            '%s',
                            '%s',
                            '%s',
                            '%s',
                            '%s',
                            '%s'
                          ) ;
                        """ % (server.ID, player.uid, curTime, 0, game.roomId, 0, gameNumber, game.curTimeGenerate, game.gameTotalCount)
                resp = trasfer_pb2.S_S_MysqlCommandsData()
                commands = resp.commands.add()
                commands.commands = insertRecordSql
                commands.type = 1

                print("记录第一局， 的玩家信息. %s" % gameNumber)
                playerResp = trasfer_pb2.S_S_MysqlCommandsData()
                for curplayer in game.players:
                    playerCommands = resp.commands.add()
                    insertPlayerSql = """
                    INSERT INTO `player_room` (
                      `user_id`,
                      `room_id`,
                      `room_number`,
                      `create_time`
                    ) 
                    VALUES
                      (
                        '%s',
                        '%s',
                        '%s',
                        '%s'
                      ) ;
                    """ % (curplayer.uid, game.roomId, gameNumber, curTime)
                    playerCommands.commands = insertPlayerSql
                    playerCommands.type = 1
                server.wsConn.send_binary(server.senderMgr.pack(resp))
            print(game.curGameCount)
            print("执行开始游戏的动态逻辑")
        except Exception as err:
            traceback.print_exc()

    @classmethod
    def endGame(cls, game, server):
        """ 结束游戏之后的操作
        :param game:
        :param server:
        :param player:
        :return:
        """
        try:
            curTime = int(time.time())
            gameNumber = "%s-%s-%s" % (server.ID, game.curTimeGenerate, game.roomId)
            print("房间玩家列表信息:%s, gameNumber: %s" % (game.players, gameNumber))
            updateSql = """
            update `game_record` SET `round`='%s' ,`end_time` = '%s' , `update_time`='%s' where game_number='%s';
            """ % (game.curGameCount, curTime, curTime,gameNumber)
            resp = trasfer_pb2.S_S_MysqlCommandsData()
            commands = resp.commands.add()
            commands.commands = updateSql
            commands.type = 2
            server.wsConn.send_binary(server.senderMgr.pack(resp))
            print("执行结束游戏的动态逻辑")
        except Exception as err:
            traceback.print_exc()

    @classmethod
    def joinRoom(cls, game, server, player, resp):
        """ 玩家加入房间后的操作

        :param game:
        :param server:
        :param player:
        :return: True or False
        """
        # print("执行加入房间玩家的动态逻辑")
        gameNumber = "%s-%s-%s" % (server.ID, game.curTimeGenerate, game.roomId)
        print("房间玩家列表信息:%s, gameNumber: %s" % (game.players, gameNumber))
        return True

