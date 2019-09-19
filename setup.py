from os import path

from setuptools import setup, find_packages

HERE = path.dirname(__file__)
extras_require = {
    'yaml':  ["PyYAML==5.1.1"],
    'toml': ["toml==0.10.0"],
    'properties': ["jproperties==2.0.0"]
}

extras_require.update(all=sorted(set().union(*extras_require.values())))

setup(
    name='pyconfigloader',
    version=open(path.join(HERE, 'VERSION')).read(),
    author="Stéphan Aimé",
    author_email="stephan.aime@gmail.com",
    description="Application config loader helper with multiple config file format supported",
    long_description=open(path.join(HERE, 'README.md')).read(),
    url='https://github.com/Fifan31/pyconfigloader',
    download_url='https://github.com/Fifan31/pyconfigloader/archive/{}.tar.gz'.format(
        open(path.join(HERE, 'VERSION')).read()),
    packages=['pyconfigloader'],
    package_dir={'pyconfigloader': 'src/pyconfigloader'},
    install_requires=[f'{lib}' for lib in open(path.join(HERE, 'requirements.txt')).read().splitlines()],
    extras_require=extras_require,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        ],
    )
