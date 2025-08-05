#!/usr/bin/env python3
"""
Setup configuration for OpenAPI CLI Tool
"""

from setuptools import setup, find_packages
import os

# Read README file
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "A generic CLI tool for any OpenAPI documented API"

setup(
    name="openapi-cli",
    version="1.0.0",
    author="OpenAPI CLI Tool",
    author_email="openapi-cli@example.com",
    description="A generic CLI tool for any OpenAPI documented API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/openapi-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Shells",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "pyyaml>=5.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "openapi-cli=openapi_cli.__main__:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/example/openapi-cli/issues",
        "Source": "https://github.com/example/openapi-cli",
    },
)

