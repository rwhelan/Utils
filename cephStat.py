

import re
import time
import signal

reDataLogParser = re.compile('(\d*) GB data, (\d*) GB used, (\d*) GB / (\d*) GB avail;.*?(\d*)op/s$')

class NotAMonLogEntry(Exception):
    pass

class Log(object):
    def __init__(self, logtext):
        self.logtext = logtext

        (self.useddata, self.allocated,
        self.rawused, self.rawtotal, self.ops) = self._parseLog()

    def _parseLog(self):
        results = reDataLogParser.findall(self.logtext)
        if not results: raise NotAMonLogEntry

        try: 
            self.timestamp = time.strptime(self.logtext[:19], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise NotAMonLogEntry

        return results[0]

    def __repr__(self):
        return 'Log(useddata=%s, allocated=%s, rawused=%s, rawtotal=%s, ops=%s)' %\
                (self.useddata, self.allocated, self.rawused, self.rawtotal, self.ops)


class LogEntries(list):
    def __init__(self):
        super(LogEntries, self).__init__()
        self.stamps = []
        self.maxlen = 600

    def add_log(self, logtext):
        try:
            _log = Log(logtext)
        except NotAMonLogEntry:
            return False

        if _log.timestamp not in self.stamps:
            self.append(_log)
            self.stamps.append(_log.timestamp)
       
            while len(self) > self.maxlen:
                del self[0]
                del self.stamps[0]

            return True

        return False

logs = LogEntries()
def dispatch(sig, frm):
    global wakecount
    if sig == signal.SIGALRM:
        updatelogs()
        updatestats()

def updatestats():
    with open('/var/run/cephiops.new', 'a') as stats:
        avgops30 = round(sum([int(i.ops) for i in logs[-30:]]) / 30.0, 2)
        avgops60 = round(sum([int(i.ops) for i in logs[-60:]]) / 60.0, 2)
        avgops300 = round(sum([int(i.ops) for i in logs[-300:]]) / 300.0, 2)

        llog = logs[-1] # Last log

        stats.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' %\
                  (time.ctime(), llog.useddata, llog.allocated, llog.rawused,
                                 llog.rawtotal, llog.ops, avgops30, avgops60, avgops300))

def updatelogs():
    with open('/var/log/ceph/ceph.log', 'r') as logfile:
        try:
            logfile.seek(-400, 2)
            for line in logfile.readlines():
                if line: # After log rotation, this will be null
                    if logs.add_log(line):
                        print 'added: %s' % logs[-1]
                        print 'logtotal: %s' % len(logs)
        except IOError:
            pass



signal.signal(signal.SIGALRM, dispatch)
signal.setitimer(signal.ITIMER_REAL, 1, 1)
signal.siginterrupt(signal.SIGALRM, False)

while True: signal.pause()
