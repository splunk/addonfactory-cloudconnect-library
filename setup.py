"""
APP Cloud Connect setup
"""

import ast
import os.path as op
import re

from setuptools import setup, find_packages, Command

_version_re = re.compile(r'__version__\s+=\s+(.*)')

_UNIT_TEST_DIR = op.sep.join([op.dirname(op.abspath(__file__)), 'test', 'unit'])

with open(op.join('package', 'cloudconnectlib', '__init__.py'), 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

if not version:
    raise RuntimeError('Version not found')


class TestCommand(Command):
    """Command to run the whole test suite."""
    description = 'Run full test suite.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Do the import here cause we need to make sure pytest exist
        import pytest

        pytest.main(['-v', _UNIT_TEST_DIR])


class JTestCommand(Command):
    """Command to run the whole test suite with junit report."""
    description = 'Run full test suite with junit report.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import pytest

        pytest.main(['-v', '--junitxml=junit_report.xml', _UNIT_TEST_DIR])


class CoverageCommand(Command):
    """Command to run the whole coverage."""
    description = 'Run full coverage.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import pytest

        pytest.main(['-v',
                     '--cov=cloudconnectlib.configuration',
                     '--cov=cloudconnectlib.core',
                     '--cov=cloudconnectlib.common',
                     _UNIT_TEST_DIR])


class CoverageHtmlCommand(Command):
    """Command to run the whole coverage."""
    description = 'Run full coverage.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import pytest

        pytest.main(['-v',
                     '--cov=cloudconnectlib.configuration',
                     '--cov=cloudconnectlib.core',
                     '--cov=cloudconnectlib.common',
                     '--cov-report=html',
                     _UNIT_TEST_DIR])


setup(
    name='cloudconnectlib',
    description='APP Cloud Connect',
    version=version,
    author='Splunk, Inc.',
    author_email='Shanghai-TA-dev@splunk.com',
    license='http://www.apache.org/licenses/LICENSE-2.0',
    url='https://git.splunk.com/projects/SOLN/repos/app-cloud-connect',

    packages=find_packages('package'),

    package_dir={'': 'package'},

    package_data={
        'cloudconnectlib.configuration': ['*.*'],
        'cloudconnectlib.core': ['cacerts/ca_certs_locater.py'],
        'cloudconnectlib.splunktalib': ['setting.conf']
    },
    install_requires=[
        "jsonschema==2.5.1",
        "jinja2==2.8",
        "jsonpath-rw==1.4.0",
        "httplib2==0.9.2",
        "splunk-sdk==1.6.0",
        "sortedcontainers==1.5.2",
        "munch==2.0.4",
        "splunktaucclib>=3.0.0-develop",
        "solnlib>=1.0.16-dev",
        "functools32==3.2.3-2",
    ],

    cmdclass={
        'test': TestCommand,
        'jtest': JTestCommand,
        'cov': CoverageCommand,
        'cov_html': CoverageHtmlCommand,
    },

    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ]
)
