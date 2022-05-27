import os

from setuptools import setup

def package_data(pkg, roots):
    """Generic function to find package_data.
    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.
    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}

setup(
    name="cmmapi",
    version="0.1",
    author="Luis Santana",
    author_email="luis.santana@uchile.cl",
    description=".",
    packages=['cmmapi'],
    install_requires=["unidecode>=1.1.1"],
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "lms.djangoapp": ["cmmapi = cmmapi.apps:CMMAPIConfig"]
    },
    package_data=package_data("cmmapi", ["static", "public"]),
)

