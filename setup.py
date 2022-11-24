from setuptools import find_packages, setup
import os

setup(
    name='rok4lib',
    version=os.environ["VERSION"],
    packages=find_packages(include=['rok4']),
    description='Python core libraries for ROK4 project',
    author='Géoportail<tout_rdev@ign.fr>',
    url='https://github.com/rok4/core-python',
    install_requires=['boto3'],
    setup_requires=['pytest-runner','wheel'],
    tests_require=['pytest==4.4.1', 'moto[s3]==4.0.8'],
    test_suite='tests',
)