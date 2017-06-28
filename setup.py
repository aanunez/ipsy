#!/usr/bin/env python3

from setuptools import setup

setup(
	name = 'ipsy',
	version = '0.2',
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
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='emulation ips rom patch emulator'
)
