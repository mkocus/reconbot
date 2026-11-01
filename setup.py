#!/usr/bin/env python

from setuptools import setup

setup(
    name='Reconbot',
    version='2.0',
    license='MIT License',
    description='Reconbot for Eve Online',
    python_requires='>=3.10',
    packages=[
        'reconbot',
        'reconbot.notifiers',
        'reconbot.notificationprinters',
        'reconbot.notificationprinters.esi',
    ]
)
