"""
GuardianAI SDK

A zero-friction instrumentation library for LLM applications.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="guardianai-sdk",
    version="0.1.0",
    author="GuardianAI Team",
    author_email="team@guardianai.example.com",
    description="Zero-friction LLM monitoring and observability SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guardianai/sdk",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.11",
    install_requires=[
        "ddtrace>=2.0.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "hypothesis>=6.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
        "vertex": [
            "google-cloud-aiplatform>=1.38.0",
        ],
        "openai": [
            "openai>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "guardianai=guardianai.cli:main",
        ],
    },
    keywords=[
        "llm",
        "monitoring",
        "observability",
        "datadog",
        "apm",
        "tracing",
        "vertex-ai",
        "gemini",
    ],
)
