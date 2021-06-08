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
from __future__ import print_function
import os
from distutils.version import StrictVersion

basedir = os.path.dirname(os.path.abspath(__file__))


def install_cc_ucc_libs():
    os.chdir(basedir)
    pip_version = os.popen("pip -V").read().rstrip().split()[1]

    target = os.path.join(basedir, "cc_ucc_lib")

    install_cmd = "pip install " \
                  "--requirement requirements-qa.txt  --upgrade " \
                  "-i http://repo.splunk.com/artifactory/api/pypi/pypi-virtual/simple " \
                  "--no-compile --no-binary :all: --target  " + target

    if StrictVersion(pip_version) > StrictVersion("1.5.6"):
        install_cmd += " --trusted-host repo.splunk.com"

    print("command: " + install_cmd)
    os.system(install_cmd)
    os.system("rm -rf " + target + "/*.egg-info")
    os.system("rm -rf " + target + "/_yaml.so")
