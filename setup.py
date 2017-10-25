import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


install_requirements = list(
    requirement for requirement in open('requirements.txt')
    if not requirement.lstrip().startswith('#')
)

setup(
    name='Sikorka',
    version='0.0.1',
    author='Lefteris Karapetsas',
    author_email='lefteris@refu.co',
    description=('Sikorka desktop client'),
    license='BSD-3',
    keywords='ethereum location dapp',
    url='http://packages.python.org/sikorka',
    packages=['sikorka', 'tests'],
    install_requires=install_requirements,
    long_description=read('README.MD'),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Topic :: Utilities',
    ],
)
