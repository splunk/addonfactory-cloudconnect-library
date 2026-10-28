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
import io
import sys
import threading

import pytest

from cloudconnectlib.splunktacollectorlib.data_collection.event_writer import (
    EventWriter,
)
from cloudconnectlib.splunktacollectorlib.data_collection.ta_data_loader import (
    GlobalDataLoader,
    create_data_loader,
)


@pytest.mark.parametrize("event_type", [str, list, iter])
def test_writer_drains_xml_before_shutdown(monkeypatch, event_type):
    output = io.StringIO()
    monkeypatch.setattr(sys, "stdout", output)
    writer = EventWriter()
    event = "<stream><event><data>zażółć</data></event></stream>"
    assert not writer.write_events(event)
    writer.start()
    try:
        writer.start()
        events = event if event_type is str else event_type([event])
        assert writer.write_events(events)
        assert writer.write_events([event, event])
        assert writer.write_events(None)
    finally:
        writer.tear_down()
    assert output.getvalue() == event * 3
    assert not writer.isopen()
    assert not writer.write_events(event)
    writer.tear_down()


def test_writer_closes_after_output_failure(monkeypatch):
    attempted = threading.Event()

    class BrokenOutput:
        def write(self, data):
            attempted.set()
            raise OSError("output closed")

    monkeypatch.setattr(sys, "stdout", BrokenOutput())
    writer = EventWriter()
    writer.start()
    try:
        assert writer.write_events("<stream/>")
        assert attempted.wait(timeout=5)
        assert writer._failed.wait(timeout=5)
        assert not writer.isopen()
        assert not writer.write_events("<stream/>")
    finally:
        writer.tear_down()


def test_default_loader_uses_compatible_event_writer():
    GlobalDataLoader.reset()
    try:
        loader = create_data_loader()
        assert isinstance(loader.get_event_writer(), EventWriter)
    finally:
        GlobalDataLoader.reset()
