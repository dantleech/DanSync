import os, re, time
import subprocess
from iniparse import INIConfig
from pyinotify import Notifier, ThreadedNotifier, EventsCodes, ProcessEvent

class DanSync(ProcessEvent):
    def process_IN_CREATE(self, event):
        if ignoreName(relName(event)):
            return
        log("Created %s"% os.path.join(event.path, event.name))
        gitExec("git add " + relName(event))
    def process_IN_MODIFY(self, event):
        if ignoreName(relName(event)):
            return
        log("Modified %s"% os.path.join(event.path, event.name))
        gitExec("git add " + relName(event))
    def process_IN_DELETE(self, event):
        if ignoreName(relName(event)):
            return
        log("Deleted %s"% os.path.join(event.path, event.name))
        gitExec("git rm --cached " + relName(event))

def gitCommit():
    global doCommit
    if doCommit:
        gitExec("git commit -am 'Auto commit'")
        doCommit = False

def gitExec(cmd):
    global doCommit
    doCommit = True
    log("Executing GIT command: " + cmd)
    pipe = subprocess.Popen(cmd, shell=True, cwd=config.sync.directory)
    code = pipe.wait()
    return code

def relName(event):
    name = os.path.join(event.path, event.name)
    name = name.replace(config.sync.directory + '/', '')
    return name

def log(message):
    print message

def ignoreName(name):
    if re.match('.git|.*\.swp', name):
        return True
    return False

def gitInit():
    global doCommit
    if !path.exists(config.sync.directory + ".git"):
        log('Initializing new git repo')
        gitExec('git init')
        gitExec('git config --global user.name "%s"'% config.sync.username)
        gitExec('git config --global user.email "%s"'% config.sync.email)
        gitExec('git add *')

    doCommit = False


# main code
config = INIConfig(open("dansync.ini"))
mask = EventsCodes.ALL_FLAGS["IN_DELETE"] | EventsCodes.ALL_FLAGS["IN_CREATE"] | EventsCodes.ALL_FLAGS["IN_MODIFY"]
wm = WatchManager()

notifier = Notifier(wm, DanSync())
print "Motitoring files in " + config.sync.directory
wd = wm.add_watch(config.sync.directory, mask, rec=True)
doCommit = False

gitInit()

while True:
    try:
        notifier.process_events()
        if notifier.check_events():
            notifier.read_events()
        gitCommit()
        time.sleep(float(config.sync.pollInterval))
    except KeyboardInterrupt:
        notifier.stop()
        print "Quitting. Bye."
        break
