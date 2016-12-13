"""
APP Cloud Connect setup
"""

import ast
import re

from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('package/cloudconnectlib/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

if not version:
    raise RuntimeError('Version not found')

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
        '': ['LICENSE']
    },
    install_requires=[
        'jsonschema==2.5.1',
        'jinja2==2.8',
        'jsonpath-rw==1.4.0',
        'httplib2==0.9.2',
        'splunk-sdk==1.6.0',
        'sortedcontainers==1.5.2',
        'munch==2.0.4',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ]
)
