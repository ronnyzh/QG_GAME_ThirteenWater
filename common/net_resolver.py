# -*- coding: utf-8 -*-
"""
B{[公共]}指令解包/封包模块。
"""
import struct, gameobject, consts
from log import log, LOG_LEVEL_RELEASE, LOG_LEVEL_DEBUG
import json

def _logData(data):
    log("+"*96, LOG_LEVEL_DEBUG)
    buf = ''
    for idx, ch in enumerate(data):
        buf += '%02x '%(ord(ch))
        if not ((idx & 0x1f) ^ 0x1f):
            log(buf, LOG_LEVEL_DEBUG)
            buf = ''
    if buf:
        log(buf, LOG_LEVEL_DEBUG)
    log("-"*96, LOG_LEVEL_DEBUG)

def _convertJson(obj):
    d = {}
    d.update(obj.__dict__)
    return d

class Packer(gameobject.GameObject):
    def __init__(self, msg_cls):
        self.msg_cls = msg_cls

    def pack(self, protocol_object):
        assert isinstance(protocol_object, self.msg_cls)
        if isinstance(protocol_object, dict):
            data = json.dumps(protocol_object)
        else:
            data = json.dumps(protocol_object, default=_convertJson)
        return data

class Unpacker(gameobject.GameObject):
    def __init__(self, msg_cls, callback):
        assert callable(callback), "resolver[%s] is not a callable object"%(str(callback))
        self.msg_cls = msg_cls
        self.callback = callback

    def unpack(self, jsonObj):
        ob = self.msg_cls()
        if not ob.parseFromJson(jsonObj):
            return None
        return ob

class SendManager(gameobject.GameObject):
    def __init__(self):
        self._cmds = {}
        
    def registerComand(self, cmd_inst):
        assert isinstance(cmd_inst, Packer) \
            and (cmd_inst.msg_cls.__name__ not in self._cmds)
        
        self._cmds[cmd_inst.msg_cls.__name__] = cmd_inst
        
    def registerCommands(self, commands):
        for cmd_inst in commands:
            self.registerComand(cmd_inst)
        
    def pack(self, protocol_object):
        assert protocol_object.msgName in self._cmds
        cmd_inst = self._cmds[protocol_object.msgName]
        log(u'pack [%s]'%(protocol_object.msgName))
        log(u'data [%s]'%(protocol_object), LOG_LEVEL_DEBUG)
        msg = self._cmds[protocol_object.msgName].pack(protocol_object)
        _logData(msg)
        return msg
    
    def hasCmd(self, msg_header):
        return self._cmds.has_key(msg_header)
        
class RecvManager(gameobject.GameObject):
    def __init__(self):
        self._cmds = {}

    def registerCommand(self, cmd_inst):
        assert(isinstance(cmd_inst, Unpacker) \
            and (cmd_inst.msg_cls.__name__ not in self._cmds))
        
        self._cmds[cmd_inst.msg_cls.__name__] = cmd_inst

    def registerCommands(self, commands):
        for cmd_inst in commands:
            self.registerCommand(cmd_inst)

    def unpackCall(self, arole, msg):
        _logData(msg)
        try:
            jsonObj = json.loads(msg)
        except:
            log(u'try json loads failed[%s]'%(msg))
            return False
        if 'msgName' not in jsonObj:
            log(u'msgName not existed.[%s]'%(jsonObj))
            return False
        if jsonObj['msgName'] in self._cmds:
            cmd_inst = self._cmds[jsonObj['msgName']]

            if arole:
                log(u'try unpack [%s] from [%s]'% \
                    (cmd_inst.msg_cls, arole.descTxt), LOG_LEVEL_RELEASE)
            else:
                log(u'try unpack [%s]'%cmd_inst.msg_cls, LOG_LEVEL_RELEASE)
            res = cmd_inst.unpack(jsonObj)
            if res is None:
                log(u'jsonObj[%s] unpack failed.'%(jsonObj))
                return False
            log(u'unpacked [%s] [%s]'%(cmd_inst.msg_cls, str(res)))

            params = [res]
            if arole is not None:
                log(u'peer[%s] received'%(arole.descTxt))
                params.insert(0, arole)
            
            apply(cmd_inst.callback, params)
            return res.msgName, cmd_inst.callback, params
        else:
            log(u'Invalid msgName[%s]'%(jsonObj['msgName']))
            return False
            
    def clientUnpackCall(self, msg):
        return self.unpackCall(None, msg)

    def hasCmd(self, msg_header):
        return self._cmds.has_key(msg_header)