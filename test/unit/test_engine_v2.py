#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from future import standard_library
standard_library.install_aliases()
from builtins import range
from builtins import object
import threading
import time

import cloudconnectlib.core.engine_v2 as engine


class Counter(object):
    def __init__(self, default=0):
        self._count = default
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._count += 1

    def value(self):
        return self._count


class HTTPJob(object):
    def __init__(self, counter, stop_counter=None):
        self._counter = counter
        self._stop_counter = stop_counter
        self._started = False
        self._stopped = False
        self._lock = threading.Lock()

    def run(self):
        with self._lock:
            if self._stopped:
                return
            self._started = True
        time.sleep(1)
        self._counter.increment()

    def stop(self):
        with self._lock:
            self._stopped = True
            if not self._started and self._stop_counter:
                self._stop_counter.increment()


class SplitJob(object):
    def __init__(self, counter, stop_counter=None):
        self._counter = counter
        self._stop_counter = stop_counter

    def run(self):
        return [HTTPJob(self._counter, self._stop_counter) for x in range(10)]

    def stop(self):
        pass


def test_run_http_jobs():
    counter = Counter()
    cc_engine = engine.CloudConnectEngine()
    cc_engine.start([HTTPJob(counter)])
    assert counter.value() == 1


def test_run_split_jobs():
    counter = Counter()
    split_counter = Counter()
    cc_engine = engine.CloudConnectEngine()
    cc_engine.start([HTTPJob(counter), SplitJob(split_counter)])
    assert counter.value() == 1
    assert split_counter.value() == 10
    assert cc_engine._counter == 12


def test_stop_jobs():
    counter = Counter()
    split_counter = Counter()
    stop_counter = Counter()
    cc_engine = engine.CloudConnectEngine(3)

    def shutdown(cc_engine):
        time.sleep(3)
        cc_engine.shutdown()

    thread = threading.Thread(target=shutdown, args=(cc_engine,))
    thread.start()
    cc_engine.start([HTTPJob(counter), SplitJob(split_counter, stop_counter)])
    assert counter.value() == 1
    assert stop_counter.value() + split_counter.value() <= 10

