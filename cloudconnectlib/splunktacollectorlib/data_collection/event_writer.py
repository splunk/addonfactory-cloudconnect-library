#
# Copyright 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Queue preformatted modular-input XML for writing to stdout."""

import queue
import sys
import threading

from solnlib import log

logger = log.Logs().get_logger("util")


class EventWriter:
    def __init__(self):
        self._events = queue.Queue(1000)
        self._started = False
        self._failed = threading.Event()
        self._thread = None

    def start(self):
        if self._started:
            return
        self._failed.clear()
        self._started = True
        self._thread = threading.Thread(target=self._write_events, daemon=True)
        self._thread.start()

    def isopen(self):
        return self._started and not self._failed.is_set()

    def write_events(self, events):
        if events is None:
            return self.isopen()
        while self.isopen():
            try:
                self._events.put(events, timeout=0.1)
                return True
            except queue.Full:
                continue
        return False

    def tear_down(self):
        if not self._started:
            return
        self._started = False
        while self._thread.is_alive():
            try:
                self._events.put(None, timeout=0.1)
                break
            except queue.Full:
                continue
        self._thread.join()

    def _write_events(self):
        try:
            while True:
                events = self._events.get()
                if events is None:
                    return
                if isinstance(events, str):
                    events = (events,)
                for event in events:
                    sys.stdout.write(event)
                sys.stdout.flush()
        except Exception:
            self._failed.set()
            logger.exception("Failed to write modular-input events")
