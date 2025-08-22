from setuptools import setup, find_packages

setup(
    name="puzzle-challenger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-chess>=1.9.0",
        "pandas>=1.3.0",
        "sqlalchemy>=1.4.0",
        "click>=8.0.0",
        "tqdm>=4.61.0",
        "matplotlib>=3.4.0",
        "pytest>=6.2.0",
        "numpy>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "puzzle-challenger=src.main:main",
        ],
    },
)
