#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import re
from setuptools import setup, find_packages

install_requires = [
    'aiosmtpd',
    'blinker',
    'pyyaml',
    'sdnotify',
    'setproctitle',
]

version_file = os.path.join(os.path.dirname(__file__), 'laim', '_version.py')
with open(version_file) as fh:
    version_file_contents = fh.read().strip()
    version_match = re.match(r"__version__ = '(\d\.\d.\d.*)'", version_file_contents)
    version = version_match.group(1)

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as fh:
    long_description = fh.read()

setup(
    name='laim',
    version=version,
    author='Tarjei Husøy',
    author_email='git@thusoy.com',
    url='https://github.com/thusoy/laim',
    description="Local SMTP helper",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'mailq = laim.__main__:mailq',
            'newaliases = laim.__main__:newaliases',
            'sendmail = laim.__main__:main',
        ]
    },
    data_files=[("", ["LICENSE"])],
    license='Hippocratic',
    classifiers=[
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        # 'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Communications :: Email',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
    ],
)
