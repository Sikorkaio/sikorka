import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def walk_subpkg(name):
    data_files = []
    package_dir = 'sikorka'
    for parent, dirs, files in os.walk(os.path.join(package_dir, name)):
        # remove package_dir from the path
        sub_dir = os.sep.join(parent.split(os.sep)[1:])
        for f in files:
            data_files.append(os.path.join(sub_dir, f))
    return data_files


install_requires_replacements = {
    'git+git://github.com/ojii/pymaging.git#egg=pymaging': 'pymaging',
    'git+https://github.com/ojii/pymaging-png@master#egg=pymaging-png': 'pymaging-png',
}

install_requirements = list(set(
    install_requires_replacements.get(requirement.strip(), requirement.strip())
    for requirement in open('requirements.txt') if not requirement.lstrip().startswith('#')
))

pkg_data = {
    "sikorka": walk_subpkg('ui')
}


setup(
    name='Sikorka',
    version='0.0.1',
    author='Lefteris Karapetsas',
    author_email='lefteris@refu.co',
    description=('Sikorka desktop client'),
    license='BSD-3',
    keywords='ethereum location dapp',
    url='http://packages.python.org/sikorka',
    packages=['sikorka', 'sikorka.api', 'tests'],
    package_data=pkg_data,
    dependency_links=[
        'http://github.com/ojii/pymaging-png/tarball/master#egg=pymaging-png',
        'http://github.com/ojii/pymaging/tarball/master#egg=pymaging'
    ],
    install_requires=install_requirements,
    long_description=read('README.MD'),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'sikorka = sikorka.__main__:main'
        ]
    }
)
