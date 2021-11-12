from geopy.geocoders import OpenCage
from etl import utils
import pickle
from pathlib import Path
import os

class Geocoder:
    def __init__(
        self,
        api_key,
    ):
        """Takes a list of columns which need to be geocoded"""
        self.geolocator = OpenCage(api_key)

        self.cache_file = os.path.join(Path.home(), ".torque-geocode-cache.dat")
        try:
            with open(self.cache_file, "rb") as infile:
                self.cache = pickle.load(infile)
        except FileNotFoundError:
            self.cache = {}

    def geocode(
        self,
        query,
    ):
        if query not in self.cache:
            self.cache[query] = self.geolocator.geocode(
                query,
                exactly_one=True,
            )

            with open(self.cache_file, "wb") as outfile:
                pickle.dump(self.cache, outfile)

        return self.cache[query]

    @staticmethod
    def get_address_query(
        address1='',
        address2='',
        city='',
        state='',
        country='',
        locality='',
        zipCode='',
    ):
        """Combines address components into an address query to be parsed by the geocoder"""
        address_arts = utils.remove_empty_strings([
            address1,
            address2,
            city,
            state,
            country,
            locality,
            zipCode,
        ])
        return ", ".join(address_arts)
