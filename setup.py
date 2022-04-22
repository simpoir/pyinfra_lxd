from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="pyinfra_lxd",
        description="pyinfra connector using lxd client",
        author="Simon Poirier",
        author_email="simpoir@gmail.com",
        license="MIT",
        packages=find_packages(exclude=["tests"]),
        entry_points={
            "pyinfra.connectors": [
                "lxd = pyinfra_lxd.lxd",
            ],
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3 :: Only",
            "Topic :: System :: Systems Administration",
        ],
    )
