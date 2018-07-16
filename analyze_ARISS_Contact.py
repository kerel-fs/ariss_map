#!/usr/bin/env python3

import os
import csv
import geojson
import json
import ephem
import argparse

from collections import defaultdict
from datetime import datetime, date
from satnogs_api_client import *



def load_observation_ids(infile_observation_ids):
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


def generate_geojson_and_cache(norad_id,
                               start,
                               end,
                               cached_data,
                               observations_dump,
                               ground_stations_dump,
                               geojson_output):

    if (cached_data):
        # Load observation data from file
        with open(OBSERVATIONS_DUMP, 'r') as f:
            observations = json.load(f)
    else:
        observations = fetch_observation_data_from_id(norad_id, start, end)
        unkown_len = len(list(filter(lambda o: o['vetted_status'] == 'unknown', observations)))
        observations = list(filter(lambda o: o['vetted_status'] == 'good', observations))

        print("UNKOWN/GOOD = {}/{}".format(unkown_len, len(observations)))
        if len(observations) < 1:
            print("No good observations available.")
            return

        # Store fetched observation data in a local file
        with open(observations_dump, 'w') as outfile:
            json.dump(observations, outfile)

    # Get list of all ground_stations
    ground_station_ids = set(map(lambda observation: observation['ground_station'], observations))

    if (cached_data):
        # Load ground station data from file
        with open(ground_stations_dump, 'r') as f:
            ground_stations = json.load(f)
    else:
        ground_stations = fetch_ground_station_data(ground_station_ids)
        # print(ground_stations)

        # Store fetched observation data in a local file
        with open(ground_stations_dump, 'w') as outfile:
            json.dump(ground_stations, outfile)

    satellite_data = fetch_satellite_data(observations[0]['norad_cat_id'])
    # We don't cache the satellite data because it's a single API call
    # print(satellite_data)

    # Get the TLE used by one of the observations
    tle1 = 'ISS (ZARYA)'
    [tle2, tle3] = fetch_tle_of_observation(observations[0]['id'])
    tle = [tle1, tle2, tle3]

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
    print("Start: {}".format(start_time))
    print("End: {}".format(end_time))
    print("Duration: {}".format(end_time - start_time))

    # Add this metadata to satellite information
    satellite_data['start'] = start_time_str
    satellite_data['end'] = end_time_str

    sat_feature = create_satellite_track_GeoJSON(tle,
                                                 start_time,
                                                 end_time,
                                                 satellite_data,
                                                 num=50)
    # print(sat_feature)

    # Combine ground station and satellite features
    collection = geojson.FeatureCollection([*gs_features, sat_feature])

    # Write GeoJSON collection in a file
    with open(geojson_output, 'w') as out_file:
        json.dump(collection, out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a geojson file and observations metadata based on observations filtered on start and end time.')
    parser.add_argument('--norad-id',
                        metavar='norad_id',
                        help='The NORAD ID of the selected satellite. Default is the ISS: 25544',
                        default=25544,
                        type=int)
    parser.add_argument('start',
                        metavar='start',
                        help='The start time of the observation filter, formatted as %%Y-%%m-%%dT%%H:%%M:%%SZ',
                        type=lambda s: datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ'))
    parser.add_argument('end',
                        metavar='end',
                        help='The end time of the observation filter, formatted like the start time',
                        type=lambda s: datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ'))
    parser.add_argument('output_dir',
                        metavar='output_dir',
                        help='The directory where all ouput files (metadata cache and geojson file) are written to',
                        type=str)

    args = parser.parse_args()

    BASE_DIR = args.output_dir
    OBSERVATIONS_DUMP = os.path.join(BASE_DIR, 'observations.json')
    GROUND_STATIONS_DUMP = os.path.join(BASE_DIR, 'ground_stations.json')
    GEOJSON_OUTPUT = os.path.join(BASE_DIR, 'ARISSContact_map.geojson')

    generate_geojson_and_cache(norad_id=args.norad_id,
                               start=args.start,
                               end=args.end,
                               cached_data=False,
                               observations_dump=OBSERVATIONS_DUMP,
                               ground_stations_dump=GROUND_STATIONS_DUMP,
                               geojson_output=GEOJSON_OUTPUT)
