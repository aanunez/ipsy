#!/usr/bin/env python3

from setuptools import setup

setup(
	name = 'ipsy',
	version = '0.1',
	description = 'Command line IPS (Internal Patch System) applier and differ',
	author = 'Adam Nunez',
	author_email = 'adam.a.nunez@gmail.com',
	license = 'GPLv3',
	url = 'https://github.com/aanunez/ipsy',
	packages = ['ipsy'],
    entry_points={
        'console_scripts': [
            'ipsy = ipsy.__main__:main'
        ]
    },
)
