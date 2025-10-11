"""
Setup file for ocrmyproject package.
"""
from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]


setup(
    name="ocrmyproject",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A complete OCR and PDF processing toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ocrmyproject",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ocrmyproject=ocrmyproject.cli:main",
        ],
    },
    keywords="ocr,pdf,document-processing,image-processing",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ocrmyproject/issues",
        "Source": "https://github.com/yourusername/ocrmyproject",
    },
)