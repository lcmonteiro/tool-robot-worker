# #######################################################################################
# ---------------------------------------------------------------------------------------
# File:   setup.py
# Author: Luis Monteiro
# ---------------------------------------------------------------------------------------
# #######################################################################################
# imports
from setuptools import setup, find_packages
from sys import platform
# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------
with open('readme.md', 'r') as fh:
    long_description = fh.read()
# -----------------------------------------------------------------------------
# setup
# -----------------------------------------------------------------------------
setup(
    name='robotworker',  
    version='0.3',
    author='Luis Monteiro',
    author_email='monteiro.lcm@gmail.com',
    description='Interface for Robot Worker',
    long_description=long_description,
    packages=[
        'robotworker',
        'robotworker.system'
    ],
    install_requires=[
        'robotremoteserver',
        'robotframework',
        'pywin32' if platform == 'win32' else '',
        'pyyaml',
        'click',
        'psutil'
    ],
    entry_points={
      'console_scripts': [
          'work            = robotworker.client:main',
          'robotworker     = robotworker.worker:main',
          'robotworker_srv = robotworker.system.service:main',
      ]
    }
 )
# #######################################################################################
# ---------------------------------------------------------------------------------------
# End
# ---------------------------------------------------------------------------------------
# #######################################################################################