import requests
import xmltodict


class MuniClient(object):
    def __init__(self, token):
        self.token = token

    def _api_request(self, url, **params):
        if 'token' not in params:
            params['token'] = self.token

        response = requests.get(url, params)
        response.raise_for_status()

        parsed_response = xmltodict.parse(response.text)
        return parsed_response

    def get_agencies(self):
        API_URL = "http://services.my511.org/Transit2.0/GetAgencies.aspx"
        response = self._api_request(API_URL)
        return response['RTT']['AgencyList']['Agency']

    def get_routes_for_agency(self, agency):
        API_URL = "http://services.my511.org/Transit2.0/GetRoutesForAgency.aspx"
        response = self._api_request(API_URL, agencyName=agency)
        return response['RTT']['AgencyList']['Agency']['RouteList']['Route']

    def get_routes_for_agencies(self, *agencies):
        API_URL = "http://services.my511.org/Transit2.0/GetRoutesForAgencies.aspx"
        agency_names = "|".join(agencies)
        response = self._api_request(API_URL, agencyNames=agency_names)
        return response['RTT']['AgencyList']

    def get_stops_for_route(self, agency, route_code, route_direction_code):
        API_URL = "http://services.my511.org/Transit2.0/GetStopsForRoute.aspx"
        routeIDF = "~".join([agency, route_code, route_direction_code])
        response = self._api_request(API_URL, routeIDF=routeIDF)
        return response['RTT']['AgencyList']['Agency']['RouteList']['Route']['RouteDirectionList']['RouteDirection']['StopList']['Stop']

    def get_stops_for_routes(self, *routes):
        """
        Routes should be formatted as a list of three-tuples in the format:
        (Agency, Route Code, Direction).
        """
        routeIDF = "|".join(["~".join(route) for route in routes])
        API_URL = "http://services.my511.org/Transit2.0/GetStopsForRoutes.aspx"
        response = self._api_request(API_URL, routeIDF=routeIDF)
        return response

    def get_next_departures_by_stop_name(self, agency, stop_name):
        API_URL = "http://services.my511.org/Transit2.0/GetNextDeparturesByStopName.aspx"
        response = self._api_request(API_URL, agencyName=agency, stopName=stop_name)
        return response['RTT']['AgencyList']['Agency']['RouteList']['Route']

    def get_next_departures_by_stop_code(self, stop_code):
        API_URL = "http://services.my511.org/Transit2.0/GetNextDeparturesByStopCode.aspx"
        response = self._api_request(API_URL, stopCode=stop_code)
        return response['RTT']['AgencyList']['Agency']['RouteList']['Route']

