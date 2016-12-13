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

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

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
    install_requires=install_requires,

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
