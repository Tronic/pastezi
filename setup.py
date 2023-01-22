from setuptools import setup, find_packages

setup(
    name="pastezi",
    author="L. Kärkkäinen",
    author_email="tronic@noreply.users.github.com",
    description="A pastebin that doesn't suck",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Tronic/pastezi",
    packages=find_packages(),
    keywords=["pastebin", "sanic"],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    python_requires = ">=3.9",
    use_scm_version=True,
    setup_requires = ["setuptools_scm"],
    install_requires = [
        "sanic>=22.12",
        "aioredis>=2.0",
        "pygments",
        "metaphone",
        "nltk",
        "pronounceable",
    ],
    package_data={"": ["static/**"]},
    include_package_data = True,
)

