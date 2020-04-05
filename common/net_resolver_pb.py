# -*- coding: utf-8 -*-
"""
B{[公共]}指令解包/封包模块。
"""
import struct, gameobject, consts
from log import log, LOG_LEVEL_RELEASE, LOG_LEVEL_DEBUG
import time
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

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

class Packer(gameobject.GameObject):
    def __init__(self, msg_code, msg_cls, compress=False, timestamp=False):
        self.msg_code = msg_code
        self.msg_cls = msg_cls
        self.compress = compress
        self.timestamp = timestamp

    def pack(self, protocol_object):
        assert isinstance(protocol_object, self.msg_cls)
        _data = struct.pack('>I', self.msg_code) + protocol_object.SerializeToString()
        if self.compress:
            mstream = StringIO()
            f = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=mstream)
            f.write(_data)
            f.close()
            _data = mstream.getvalue()
            mstream.close()
        if self.timestamp:
            insertData = chr(self.compress) + chr(self.timestamp) + struct.pack('>Q', int(time.time()*1000))
        else:
            insertData = chr(self.compress) + chr(self.timestamp)
        compressIdx = (len(_data) + len(insertData))/3
        _data = _data[:compressIdx] + insertData + _data[compressIdx:]
        return _data

class Unpacker(gameobject.GameObject):
    def __init__(self, msg_code, msg_cls, callback):
        assert callable(callback), "resolver[%s] is not a callable object"%(str(callback))
        self.msg_code = msg_code
        self.msg_cls = msg_cls
        self.callback = callback

    def unpack(self, data):
        obj = self.msg_cls()
        obj.ParseFromString(data)
        return obj

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
        assert protocol_object.__class__.__name__ in self._cmds
        msg_name = protocol_object.__class__.__name__
        cmd_inst = self._cmds[msg_name]
        log(u'pack [%s]'%(msg_name), LOG_LEVEL_RELEASE)
        log(u'data [%s]'%(protocol_object), LOG_LEVEL_DEBUG)
        msg = cmd_inst.pack(protocol_object)
        #_logData(msg)
        return msg

    def hasCmd(self, msg_name):
        return self._cmds.has_key(msg_name)

class RecvManager(gameobject.GameObject):
    def __init__(self):
        self._cmds = {}

    def registerCommand(self, cmd_inst):
        assert(isinstance(cmd_inst, Unpacker) \
            and (cmd_inst.msg_code not in self._cmds))

        self._cmds[cmd_inst.msg_code] = cmd_inst

    def registerCommands(self, commands):
        for cmd_inst in commands:
            self.registerCommand(cmd_inst)

    def unpackCall(self, arole, msg):
        #_logData(msg)
        try:
            msg_code, = struct.unpack('>I', msg[:4])
            if msg_code not in self._cmds:
                raise Exception('msg_code[%s] is not existed.'%(msg_code))
            cmd_inst = self._cmds[msg_code]
            proto_obj = cmd_inst.unpack(msg[4:])
        except Exception, e:
            log(u'try load protobuf failed[%s]'%(e))
            return False

        if arole:
            log(u'try unpack [%s] from [%s]'% \
                (cmd_inst.msg_cls, arole.descTxt), LOG_LEVEL_RELEASE)
        else:
            log(u'try unpack [%s]'%cmd_inst.msg_cls, LOG_LEVEL_RELEASE)

        log(u'unpacked [%s] [%s]'%(cmd_inst.msg_cls, proto_obj))

        params = [proto_obj]
        if arole is not None:
            log(u'peer[%s] received'%(arole.descTxt))
            params.insert(0, arole)

        apply(cmd_inst.callback, params)
        return cmd_inst.msg_code, cmd_inst.callback, params

    def clientUnpackCall(self, msg):
        return self.unpackCall(None, msg)

    def hasCmd(self, msg_header):
        return self._cmds.has_key(msg_header)