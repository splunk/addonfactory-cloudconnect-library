import Queue
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

    def __init__(self):
        self._tasks = Queue.Queue()
        self._stop_signal_received = False
        self._stopped = threading.Event()

    def add_task(self, task):
        """
        Add a task instance into a job.

        :param task: TBD
        :type task: TBD
        """
        if not isinstance(task, BaseTask):
            raise ValueError('Invalid task')
        self._tasks.put(task)

    def run(self, context):
        """
        Run current job, which executes tasks in it sequentially..

        :param context:
        :type context: dict
        """
        logger.debug('Start to run job')

        self._stopped.clear()

        while not self._stopped.is_set():
            if self._stop_signal_received:
                logger.info('Stop job signal received, stopping job.')
                self._stopped.set()
                break
            task = self._tasks.get()
            result = task.perform()
            
            for r in result:
                pass

        logger.debug('Job execution finished successfully.')

    def stop(self, block=True, timeout=30):
        """
        Stop current job.
        """
        if self._stopped.is_set():
            logger.info('Job is not running, cannot stop it.')
            return
        self._stop_signal_received = True

        if not block:
            return

        while not self._stopped.is_set():
            self._stopped.wait(timeout)
