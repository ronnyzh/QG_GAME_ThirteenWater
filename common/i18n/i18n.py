#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Author: $Author$
Date: $Date$
Revision: $Revision$

Description:
    翻译模块
"""

LANGS = {}

def initializeWeb():
    global LANGS
    langModules = __import__('common.i18n.web', fromlist=['cn'])
    LANGS['CHN'] = langModules.cn
    setattr(LANGS['CHN'], '__code__', 'CHN')

def initializeGame():
    global LANGS
    langModules = __import__('common.i18n.game', fromlist=['cn'])
    LANGS['CHN'] = langModules.cn

def isValidLang(lang):
    global LANGS
    return lang in LANGS

def getLangInst(lang = 'CHN'):
    global LANGS
    assert lang in LANGS
    return LANGS[lang]
