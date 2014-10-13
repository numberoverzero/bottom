""" Setup file """
import os
import re
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()
# Remove custom RST extensions for pypi
CHANGES = re.sub(r'\(\s*:(issue|pr|sha):.*?\)', '', CHANGES)

REQUIREMENTS = [
]

TEST_REQUIREMENTS = [
    'pytest',
]

if __name__ == "__main__":
    setup(
        name='bottom',
        version='0.9.0',
        description="asyncio-based rfc2812-compliant IRC Client",
        long_description=README + '\n\n' + CHANGES,
        classifiers=[
            'Development Status :: 3 - Alpha',
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
        url='http://bottom.readthedocs.org/',
        license='MIT',
        keywords='meta metaclass declarative orm',
        platforms='any',
        include_package_data=True,
        py_modules=['bottom'],
        packages=find_packages(exclude=('tests',)),
        install_requires=REQUIREMENTS,
        tests_require=REQUIREMENTS + TEST_REQUIREMENTS,
    )
