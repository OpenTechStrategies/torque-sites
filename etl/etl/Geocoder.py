from geopy.geocoders import OpenCage
from etl import utils

class Geocoder:
    def __init__(
        self,
        api_key,
    ):
        """Takes a list of columns which need to be geocoded"""
        self.geolocator = OpenCage(api_key)

    def geocode(
        self,
        query,
    ):
        return self.geolocator.geocode(
            query,
            exactly_one=True,
        )

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

    @staticmethod
    def generate_address_query_lambda(
        address1='',
        address2='',
        city='',
        state='',
        country='',
        locality='',
        zipCode='',
    ):
      return (lambda proposal:
        Geocoder.get_address_query(
          address1=proposal.cell(address1),
          address2=proposal.cell(address2),
          city=proposal.cell(city),
          state=proposal.cell(state),
          country=proposal.cell(country),
          locality=proposal.cell(locality),
          zipCode=proposal.cell(zipCode),
        )
    )
