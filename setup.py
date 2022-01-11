import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()


def get_version():
    with open("bottom/__init__.py") as f:
        for line in f:
            if line.startswith("__version__"):
                return eval(line.split("=")[-1])

REQUIREMENTS = []

TEST_REQUIREMENTS = [
    "coverage==6.2",
    "flake8==4.0.1",
    "mypy==0.931",
    "pytest==6.2.5",
    "sphinx==3.1.2",
    "sphinx-rtd-theme==0.5.0",
    "tox==3.24.5",
]

if __name__ == "__main__":
    setup(
        name="bottom",
        version=get_version(),
        description="asyncio-based rfc2812-compliant IRC Client",
        long_description=README,
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.10",
            "Topic :: Software Development :: Libraries",
            "Topic :: Communications :: Chat",
            "Topic :: Communications :: Chat :: Internet Relay Chat"
        ],
        author="Joe Cross",
        author_email="joe.mcross@gmail.com",
        url="https://github.com/numberoverzero/bottom",
        license="MIT",
        keywords="irc bot asyncio client",
        platforms="any",
        include_package_data=True,
        packages=find_packages(exclude=("tests", "examples")),
        install_requires=REQUIREMENTS,
        tests_require=REQUIREMENTS + TEST_REQUIREMENTS,
    )
