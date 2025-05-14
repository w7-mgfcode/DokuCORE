from setuptools import setup, find_packages

setup(
    name="dokucore",
    version="0.1.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.28.0",
        "fastmcp>=0.5.0",
        "pydantic>=2.7.0",
        "psycopg2-binary>=2.9.0",
        "sentence-transformers>=2.5.0",
        "GitPython>=3.1.0",
        "python-multipart>=0.0.9",
        "llama-index>=0.10.0",
        "llama-index-vector-stores-postgres>=0.1.0",
        "llama-index-readers-file>=0.1.0",
        "markdown>=3.5.0",
        "nltk>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "httpx>=0.24.0",
            "SQLAlchemy>=2.0.0",
        ],
    },
    python_requires=">=3.10",
)