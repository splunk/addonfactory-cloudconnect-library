import concurrent.futures as cf
import threading
from collections import Iterable
from ..common.log import get_cc_logger
logger = get_cc_logger()


class CloudConnectEngine(object):

    def __init__(self, max_workers=4):
        self._executor = cf.ThreadPoolExecutor(max_workers)
        self._intermediate_results = set()
        self._shutdown = False
        self._all_running_jobs = []
        self._lock = threading.RLock()

    def start(self, jobs=None):
        if not jobs:
            return
        for job in jobs:
            self._add_job(job)
        while self.is_running():
            if not self._intermediate_results:
                break
            done_and_not_done_futures = cf.wait(self._intermediate_results,
                                                return_when=cf.FIRST_COMPLETED)
            self._intermediate_results = done_and_not_done_futures.not_done
            done_futures = done_and_not_done_futures.done
            for future in done_futures:
                result = future.result()
                if result:
                    if isinstance(result, Iterable):
                        for temp in result:
                            self._add_job(temp)
                    else:
                        self._add_job(result)
        self._teardown()

    def _add_job(self, job):
        if not self.is_running():
            return False
        self._all_running_jobs.append(job)
        result = self._executor.submit(self._invoke_job, job)
        self._intermediate_results.add(result)
        return True

    def _invoke_job(self, job):
        if not self.is_running():
            return
        invoke_result = None
        try:
            invoke_result = job.run()
        except:
            logger.exception("invoke job exception")
        finally:
            with self._lock:
                self._all_running_jobs.remove(job)
            return invoke_result

    def is_running(self):
        return not self._shutdown

    def shutdown(self):
        self._shutdown = True

    def _teardown(self):
        self.shutdown()
        with self._lock:
            for job in self._all_running_jobs:
                job.stop()
        self._executor.shutdown(wait=True)
