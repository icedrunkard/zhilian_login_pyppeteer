# coding=utf-8
import time
import inspect
import codecs
import sys
from os.path import split as os_split, abspath, dirname, join as os_join, exists
from .settings import *


class Logger(object):

    def __init__(self, log_file='logger.log'):
        self.log_file = os_join(LOG_DIR, log_file)
        print('log_file:', abspath(self.log_file))

    @property
    def funcname(self):
        return inspect.stack()[1][3] + ': '

    def log(self, *msg, log_in_file=True):
        log_file = self.log_file
        filename = os_split(inspect.stack()[1][1])[-1]
        funcname = inspect.stack()[1][3] + ': '
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        log_msg = '\n'
        for each in msg:
            if isinstance(each, Exception):
                s = sys.exc_info()
                line_num = s[2].tb_lineno
                err = '{err_type}: {err_value}'.format(err_type=type(s[1]), err_value=s[1])
                s0 = '{},ERR L:{},{}'.format(filename, line_num, funcname)
                s1 = err
                log_msg += '[{}] {}{}'.format(now, s0, s1)
        if len(log_msg) > 3:
            log_msg += '\t\t'
        line_num = inspect.stack()[1][2]
        s0 = '{},L:{},{}'.format(filename, line_num, funcname)
        s1 = ''
        for each in msg:
            try:
                if isinstance(each, Exception):
                    continue
                each = str(each)
            except Exception as e:
                each = str(type(e)) + str(e)
            s1 += each + ' '
        info = '{}'.format(s1) if log_msg[-1] == '\t' else '[{}] {}{}'.format(now, s0, s1)
        log_msg += info
        print(log_msg[1:])
        if not log_in_file:
            return
        try:
            f = codecs.open(log_file, 'a+', encoding='utf-8')
            f.write(log_msg)
            f.close()
        except Exception as e:
            print(type(e), e)


logger = Logger()


if __name__ == '__main__':
    l = Logger()
    l.log(1, 22, 3, 4, )
