from setuptools import setup, find_packages

version = '0.0.1'
description = 'KNN search web service'
long_description = \
    'A web service implementing K nearest neighbour search ' \
    'using Postgis PostgreSQL extension internally.' \
    'Provides a simple REST API for creating, updating, deleting ' \
    'users with geolocations and for performing the KNN search itself.'

setup(
    name='neighbour-seeker',
    description=description,
    long_description=long_description,
    url='https://github.com/Mindflutter/neighbour_seeker',
    classifiers=['Programming Language :: Python :: 3.8'],
    author='Igor Golyanov',
    author_email='thornograph@gmail.com',
    python_requires='~=3.8.0',
    version=version,
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'neighbour-seeker = neighbour_seeker.main:main'
        ]}
)
