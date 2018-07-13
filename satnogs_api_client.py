import requests


NETWORK_DEV_BASE_URL = 'https://network-dev.satnogs.org/api'
NETWORK_BASE_URL = 'https://network.satnogs.org/api'
DB_BASE_URL = 'https://db.satnogs.org/api'


def fetch_observation_data_from_id(norad_id, start, end, prod=True):
    # Get all observations of the satellite with the given `norad_id` in the given timeframe
    # https://network.satnogs.org/api/observations/?satellite__norad_cat_id=25544&start=2018-06-10T00:00&end=2018-06-15T00:00

    query_str = '{}/observations/?satellite__norad_cat_id={}&start={}&end={}'

    url = query_str.format(NETWORK_BASE_URL if prod else NETWORK_DEV_BASE_URL,
                           norad_id,
                           start.isoformat(),
                           end.isoformat())
    print(url)
    r = requests.get(url=url)

    if r.status_code != requests.codes.ok:
        print("No observations found for {}, start: {}, end: {}.".format(norad_id, start_time, end_time))
        raise
    return r.json()


def fetch_observation_data(observation_ids, prod=True):
    # Get station location from the observation via the observation_id
    
    observations = []
    for observation_id in observation_ids:
        r = requests.get(url='{}/observations/{}/'.format(NETWORK_BASE_URL if prod else NETWORK_DEV_BASE_URL,
                                                          observation_id))
        if r.status_code != requests.codes.ok:
            print("Observation {} not found in network.".format(observation_id))
            continue
        observations.append(r.json())

    return observations

def fetch_ground_station_data(ground_station_ids, prod=True):
    # Fetch ground station metadata from network
    ground_stations = []
    for ground_station_id in ground_station_ids:
        r = requests.get(url='{}/stations/{}/'.format(NETWORK_BASE_URL if prod else NETWORK_DEV_BASE_URL,
                                                      ground_station_id))
        if r.status_code != requests.codes.ok:
            print("Ground Station {} not found in db.".format(ground_station_id))
            raise
        data = r.json()
        ground_stations.append(r.json())
    return ground_stations

def fetch_satellite_data(norad_cat_id):
    # Fetch satellite metadata from network
    r = requests.get(url='{}/satellites/{}/'.format(DB_BASE_URL, norad_cat_id))
    if r.status_code != requests.codes.ok:
        print("ERROR: Satellite {} not found in network.".format(norad_cat_id))

    return r.json()
