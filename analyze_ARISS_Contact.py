#!/usr/bin/env python3

import os
import requests
import csv
import geojson
import json
import ephem

from collections import defaultdict
from datetime import datetime, date


DISCUSSION_URL = 'https://community.libre.space/t/ariss-contact-kardinal-frings-gymnasium-bonn-germany-direct-via-dloil/2268'

BASE_DIR = './ARISS_Contact20180703/'
INFILE_OBSERVATION_IDs = os.path.join(BASE_DIR, 'observation_ids.txt')
OBSERVATIONS_DUMP = os.path.join(BASE_DIR, 'observations.json')
GROUND_STATIONS_DUMP = os.path.join(BASE_DIR, 'ground_stations.json')
TLE = ['ISS (ZARYA)',
       '1 25544U 98067A   18183.60070602  .00001547  00000-0  30742-4 0  9999',
       '2 25544  51.6424 301.8800 0003452 254.6052 284.2649 15.54000368120912']
GEOJSON_OUTPUT = os.path.join(BASE_DIR, 'ARISSContact_map.geojson')


NETWORK_BASE_URL = 'https://network.satnogs.org/api'
DB_BASE_URL = 'https://db.satnogs.org/api'


def fetch_observation_ids(infile_observation_ids):
    # Read observation ids from file
    observation_ids = []

    with open(infile_observation_ids, 'r') as infile:
        for line in infile:
            if len(line[:-2]) < 2:
                continue
            if line[0] == '#':
                if 'dev' in line[2:]:
                    # Ignore observations from dev instance for now
                    break
                continue
                    
            observation_ids.append(int(line[:-1]))

    return observation_ids


def fetch_observation_data(observation_ids):
    # Get station location from the observation via the observation_id
    
    observations = []
    for observation_id in observation_ids:
        r = requests.get(url='{}/observations/{}/'.format(NETWORK_BASE_URL, observation_id))
        if r.status_code != requests.codes.ok:
            print("Observation {} not found in network.".format(observation_id))
            continue
        observations.append(r.json())

    return observations

def fetch_ground_station_data(ground_station_ids):
    # Fetch ground station metadata from network
    ground_stations = []
    for ground_station_id in ground_station_ids:
        r = requests.get(url='{}/stations/{}/'.format(NETWORK_BASE_URL, ground_station_id))
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


# Create ground station GeoJSON feature collection
def create_ground_stations_GeoJSON(observations):
    gs_features = []
    for observation in observations:
        ob_feature = geojson.Feature(geometry=geojson.Point((observation['station_lng'],
                                                             observation['station_lat'])),
                                     properties=observation)
        gs_features.append(ob_feature)

    return gs_features
    # gs_collection = geojson.FeatureCollection(features)


# Return 'num' evenly spaced datetimes in the range from 'start' to 'stop'
def lin_datetime_range(start, end, num=50):
    time_step = (end - start)/num
    for n in range(num):
        yield start + n * time_step


def create_satellite_track_GeoJSON(tle, start_time, end_time, satellite_metadata, num=50):
    # Calculate satellite ground track using pyephem
    satellite = ephem.readtle(tle[0], tle[1], tle[2])
    sat_positions = []
    for t in lin_datetime_range(start_time, end_time, num=num):
        satellite.compute(t)
        sat_positions.append((satellite.sublong/ephem.degree,
                             satellite.sublat/ephem.degree))
    sat_linestring = geojson.LineString(sat_positions)
    sat_feature = geojson.Feature(geometry=sat_linestring, properties=satellite_metadata)
    return sat_feature


if __name__ == '__main__':
    observation_ids = fetch_observation_ids(INFILE_OBSERVATION_IDs)
    # print(observation_ids)

    cached_data = True

    if (cached_data):
        # Load observation data from file
        with open(OBSERVATIONS_DUMP, 'r') as f:
            observations = json.load(f)
    else:
        observations = fetch_observation_data(observation_ids)
        # print(observations)

        # Store fetched observation data in a local file
        with open(OBSERVATIONS_DUMP, 'w') as outfile:
            json.dump(observations, outfile)

    # Get list of all ground_stations
    ground_station_ids = set(map(lambda observation: observation['ground_station'], observations))

    if (cached_data):
        # Load ground station data from file
        with open(GROUND_STATIONS_DUMP, 'r') as f:
            ground_stations = json.load(f)
    else:
        ground_stations = fetch_ground_station_data(ground_station_ids)
        # print(ground_stations)

        # Store fetched observation data in a local file
        with open(GROUND_STATIONS_DUMP, 'w') as outfile:
            json.dump(ground_stations, outfile)

    satellite_data = fetch_satellite_data(observations[0]['norad_cat_id'])
    # We don't cache the satellite data because it's a single API call
    # print(satellite_data)

    gs_features = create_ground_stations_GeoJSON(observations)
    # print(gs_features)

    # Find the first start time and the last end time of the observations
    # NOTE: Assuming a full coverage in between here!
    #       The ipython notebook for SSTV drops the assumption and calculates all
    #       non-overlapping, continuous observation windows
    start_time_str = sorted(observations, key=lambda obs: obs['start'])[0]['start']
    end_time_str = sorted(observations, key=lambda obs: obs['end'])[-1]['end']
    
    start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M:%SZ')
    # print("Duration: {}".format(end_time - start_time))

    # Add this metadata to satellite information
    satellite_data['start'] = start_time_str
    satellite_data['end'] = end_time_str

    sat_feature = create_satellite_track_GeoJSON(TLE,
                                                 start_time,
                                                 end_time,
                                                 satellite_data,
                                                 num=50)
    # print(sat_feature)

    # Combine ground station and satellite features
    collection = geojson.FeatureCollection([*gs_features, sat_feature])

    # Write GeoJSON collection in a file
    with open(GEOJSON_OUTPUT, 'w') as out_file:
        json.dump(collection, out_file)
