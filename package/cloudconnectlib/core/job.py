import copy
import threading

from cloudconnectlib.common.log import get_cc_logger
from task import BaseTask

logger = get_cc_logger()


class CCEJob(object):
    """
    One CCEJob is composed of a list of tasks. The task could be HTTP task or Split task(currently supported task types).
    Job is an executing unit of CCE engine.
    All tasks in one job will be run sequentially but different jobs could be run concurrently.
    So if there is no dependency among tasks, then suggest to create different Job for them to improve performance.
    """

    def __init__(self, context, tasks=None):
        self._context = context
        self._tasks = []

        self._stop_signal_received = False
        self._stopped = threading.Event()

        if tasks:
            self._tasks.extend(tasks)

    def add_task(self, task):
        """
        Add a task instance into a job.

        :param task: TBD
        :type task: TBD
        """
        if not isinstance(task, BaseTask):
            raise ValueError('Unsupported task type: {}'.format(type(task)))
        self._tasks.append(task)

    def _check_if_stop_needed(self):
        if self._stop_signal_received:
            logger.info('Stop job signal received, stopping job.')
            self._stopped.set()
            return True
        return False

    def run(self):
        """
        Run current job, which executes tasks in it sequentially..

        :param context:
        :type context: dict
        """
        logger.debug('Start to run job')

        if not self._tasks:
            logger.debug('No task found in job')
            return

        if self._check_if_stop_needed():
            return

        task = self._tasks[0]
        self._tasks = self._tasks[1:]
        contexts = list(task.perform(self._context) or ())

        if self._check_if_stop_needed():
            return

        if not self._tasks:
            logger.debug('No more task need to perform, exiting job')
            return

        for ctx in contexts:
            yield CCEJob(context=copy.deepcopy(ctx),
                         tasks=copy.deepcopy(self._tasks))

            if self._check_if_stop_needed():
                return

        logger.debug('Job execution finished successfully.')

    def stop(self, block=False, timeout=30):
        """
        Stop current job.
        """
        if self._stopped.is_set():
            logger.info('Job is not running, cannot stop it.')
            return
        self._stop_signal_received = True

        if not block:
            return

        self._stopped.wait(timeout)
