from setuptools import setup, find_packages

setup(
    name="video-wall-control",
    version="1.0.0",
    description="Video Wall Control Panel Backend Server",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/video-wall-control",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.3.0",
        "Flask-CORS>=4.0.0",
        "Flask-SocketIO>=5.3.0",
        "python-socketio>=5.8.0",
        "requests>=2.31.0",
        "aiohttp>=3.8.0",
        "pyserial>=3.5",
        "schedule>=1.2.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "video-wall-server=video_wall_server:main",
        ],
    },
)
