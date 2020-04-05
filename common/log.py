# -*- coding: utf-8 -*-
import time
import sys
from twisted.python.log import msg
from twisted.python.logfile import DailyLogFile
#from twisted.python.lockfile import FilesystemLock, isLocked

LOG_LEVEL_DEBUG = 1
LOG_LEVEL_TEST = 2
LOG_LEVEL_RELEASE = 3
LOG_LEVEL_WARNING = 4
LOG_LEVEL_ERROR = 5

LOG_LEVEL_PREFIX = { \
    LOG_LEVEL_DEBUG : '[Debug]', \
    LOG_LEVEL_TEST : '[Test]', \
    LOG_LEVEL_RELEASE : '[Info]', \
    LOG_LEVEL_WARNING : '[Warning]', \
    LOG_LEVEL_ERROR : '[Error]' \
}
g_log_level = LOG_LEVEL_RELEASE
def setLogLevel(log_level):
    global g_log_level
    g_log_level = log_level

def log(txt, log_level = LOG_LEVEL_TEST):
    global g_log_level
    if log_level >= g_log_level:
        global LOG_LEVEL_PREFIX
        if log_level <= LOG_LEVEL_DEBUG:
            code = sys._getframe(1).f_code
            func_tag = '[%d:%s]'%(code.co_firstlineno, code.co_name)
        else:
            func_tag = ''
        msg(LOG_LEVEL_PREFIX[log_level] + func_tag + txt)

class HourLogFile(DailyLogFile):
    def __init__(self, name, directory, exist_postfix = ''):
#        if isLocked(name):
#            import os
#            base, ext = os.path.splitext(name)
#            name = base + exist_postfix + ext
#        self._lock = FilesystemLock(name)
#        self._lock.lock()
        DailyLogFile.__init__(self, name, directory)

    def close(self):
        #self._lock.unlock()
        DailyLogFile.close(self)

    def shouldRotate(self):
        """Rotate when the date has changed since last write"""
        cur_date = self.toDate()
        return cur_date > self.lastDate

    def toDate(self, *args):
        """Convert a unixtime to (year, month, day) localtime tuple,
        or return the current (year, month, day) localtime tuple.

        This function primarily exists so you may overload it with
        gmtime, or some cruft to make unit testing possible.
        """
        # primarily so this can be unit tested easily
        return time.localtime(*args)[:4]