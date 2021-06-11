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
import os.path as op

PROJECT_ROOT = op.dirname(op.dirname(op.dirname(op.abspath(__file__))))

EXAMPLE_DIR = op.join(PROJECT_ROOT, 'examples', '1.0')
TEST_DATA_DIR = op.join(PROJECT_ROOT, 'test', 'data')
CONFIGURATION_DIR = op.join(PROJECT_ROOT, 'cloudconnectlib', 'configuration')
SCHEMA_FILE = op.join(CONFIGURATION_DIR, 'schema_1_0_0.json')
