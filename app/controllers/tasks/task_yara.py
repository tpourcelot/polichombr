#!/usr/bin/env python
import time

from app import app
from app.models.yara_rule import YaraRule
from app.controllers.task import Task
from app.controllers.yara_rule import run_extended_yara, YaraController
from app.controllers.sample import SampleController


class task_yara(Task):
    """
    Runs YARA signatures on the sample. This task is provided by default.
    """
    yaramatched = None

    def __init__(self, sample):
        super(task_yara, self).__init__()
        self.sid = sample.id
        """
        Execution level = 1, we need to obtain MACHOC hashes
        before any YARA-MACHOC comparison.
        MACHOC hashes are extracted by the ANALYZEITRB task,
        which has a 0 execution level.
        """
        self.execution_level = 1
        self.yaramatched = []

    def execute(self):
        """
        Extended yara execution. Stores hits on the yaramatched attribute.
        """
        s_controller = SampleController()
        sample = s_controller.get_by_id(self.sid)
        self.tstart = int(time.time())
        self.tmessage = "YARA TASK %d :: " % (sample.id)
        app.logger.debug(self.tmessage + "EXECUTE")
        for yar in YaraRule.query.all():
            if run_extended_yara(yar.raw_rule, sample) is True:
                self.yaramatched.append(yar)
        return True

    def apply_result(self):
        """
        Commits to database.
        """
        s_controller = SampleController()
        sample = s_controller.get_by_id(self.sid)
        app.logger.debug(self.tmessage + "APPLY_RESULT")
        for y in self.yaramatched:
            # use the static YaraController => the () will create a JobPool,
            # causing exceptions (daemon => child).
            YaraController.add_to_sample(sample, y)
        app.logger.debug(self.tmessage + "END - TIME %i" %
                         (int(time.time()) - self.tstart))
        return True
