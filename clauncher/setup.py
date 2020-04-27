# sample setup.py (https://packaging.python.org/tutorials/packaging-projects/)

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='clauncher',
    version='0.1.0',
    description='CONIX Launcher',
    long_description=long_description,
    author='Nuno Pereira',
    author_email='npereira@cmu.edu',
    url='',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    python_requires='>=3.6',
)

