#!/usr/bin/env python

from distutils.core import setup

setup(
    name="etl",
    version="1.0.0",
    description="Generic ETL pipeline for use by torque-site competitions",
    author="Open Tech Strategies, LLC",
    author_email="intentionally@left.blank.com",
    url="https://github.com/OpenTechStrategies/torque-sites",
    packages=["etl"],
    install_requires=["mwclient", "bs4", "unidecode", "geopy"],
)
