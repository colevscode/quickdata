import os
from distutils.core import setup

root = os.path.dirname(os.path.realpath(__file__))

setup(
    name='quickdata',
    version='0.1.0',
    author='Cole Krumbholz',
    author_email='cole@brace.io',
    description='Python document based persistence inspired by backbone.js with dict and object syntax.',
    packages=['quickdata'],
    install_requires=open(root+"/requirements.txt").read().splitlines(),
    long_description=open(root+"/README.md").read(),
    license='LICENSE',
)