import os
import json
import time
import random
import shutil
import datetime

from config import WORKING_DIRECTORY, REPAIR_ROOT
from config import DATA_PATH
from config import REPAIR_TOOL_FOLDER
from filelock import FileLock

LOCK_FILE = "LOCK_INIT"


class RepairTool(object):
    def __init__(self, name, config_name):
        self.data = None
        self.main = None
        self.jar = None
        self.name = name
        self.config_name = config_name
        self.repair_begin = None
        self.parseData()
        self.seed = 0
        pass

    def parseData(self):
        path = os.path.join(DATA_PATH, 'repair_tools', self.config_name + '.json')
        if os.path.exists(path):
            with open(path) as data_file:
                self.data = json.load(data_file)
                self.main = self.data["main"]
                self.jar = os.path.join(REPAIR_TOOL_FOLDER, self.data["jar"])

    def init_bug(self, bug, bug_path):
        if os.path.exists(bug_path):
            shutil.rmtree(bug_path)

        lock = FileLock(os.path.join(REPAIR_ROOT, LOCK_FILE))
        try:
            lock.acquire()
            bug.checkout(bug_path)
        finally:
            lock.release()

        if bug.compile() != 0:
            raise RuntimeError("compile has failed!\n")

        self.repair_begin = datetime.datetime.now().__str__()
        # bug.run_test()

    def get_info(self, bug, bug_path):
        pass

    def repair(self, bug):
        bug_path = os.path.join(WORKING_DIRECTORY, "%s_%s" % (bug.project, bug.bug_id))
        self.init_bug(bug, bug_path)

        self.get_info(bug, bug_path)
        pass

    def __str__(self):
        return self.name
