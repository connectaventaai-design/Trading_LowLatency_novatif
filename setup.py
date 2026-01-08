from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hft-gold-trading",
    version="1.0.0",
    author="Trading System Team",
    description="High-Frequency Trading System for GOLD/XAUUSD with MT5 Integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/connectaventaai-design/Trading_LowLatency_novatif",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "MetaTrader5>=5.0.45",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "polars>=0.18.0",
        "numba>=0.57.0",
        "torch>=2.0.0",
        "scikit-learn>=1.3.0",
        "hmmlearn>=0.3.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "websockets>=11.0.0",
        "aiohttp>=3.8.0",
        "uvloop>=0.17.0",
        "redis>=4.5.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "structlog>=23.1.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "ruff>=0.0.285",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hft-trading=main:main",
            "hft-backtest=backtest_runner:main",
            "hft-train=train_models:main",
        ],
    },
)
