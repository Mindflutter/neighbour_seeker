from setuptools import setup, find_packages

version = '0.0.1'
setup(
    name='neighbour-seeker',
    version=version,
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'neighbour-seeker = neighbour_seeker.main:main'
        ]}
)
