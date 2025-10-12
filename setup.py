# ABOUTME: Package setup configuration for legal-mcp CLI
# ABOUTME: Defines console script entry point and package metadata

from setuptools import setup, find_packages

setup(
    name="legal-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer==0.15.1",
        "rich==13.9.4",
        "httpx==0.28.1",
    ],
    entry_points={
        "console_scripts": [
            "legal-mcp=cli.main:app",
        ],
    },
    python_requires=">=3.10",
)
