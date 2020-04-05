# -*- coding:utf-8 -*-
#!/bin/python

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description: Protocol Base
"""

from common.gameobject import GameObject

class Protocol(GameObject):
    def __init__(self):
        self.msgName = self.__class__.__name__
        self.init()

    def __repr__(self):
        return str(self.__dict__)
    __str__ = __repr__

    def init(self):
        raise 'abstract interface'

    def parseFromJson(self, jsonObj):
        raise 'abstract interface'