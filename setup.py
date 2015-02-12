""" Setup file """
import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.markdown')).read()

REQUIREMENTS = [
    'simplex'
]

TEST_REQUIREMENTS = [
    'tox',
    'pytest',
    'pytest-cov',
    'coverage',
    'flake8'
]

if __name__ == "__main__":
    setup(
        name='bottom',
        version='0.9.13',
        description="asyncio-based rfc2812-compliant IRC Client",
        long_description=README,
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Software Development :: Libraries',
            'Topic :: Communications :: Chat',
            'Topic :: Communications :: Chat :: Internet Relay Chat'
        ],
        author='Joe Cross',
        author_email='joe.mcross@gmail.com',
        url='https://github.com/numberoverzero/bottom',
        license='MIT',
        keywords='irc bot asnycio client',
        platforms='any',
        include_package_data=True,
        packages=find_packages(exclude=('tests',)),
        install_requires=REQUIREMENTS,
        tests_require=REQUIREMENTS + TEST_REQUIREMENTS,
    )
