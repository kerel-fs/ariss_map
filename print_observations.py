#!/usr/bin/env python3

import argparse
from datetime import datetime, date

from satnogs_api_client import *


def show_obs(observations):
    for o in observations:
        print('{} {} {} {} {} {}'.format(o['id'], o['start'], o['end'], o['norad_cat_id'], o['transmitter'], o['vetted_status']))

def show_obs_url(observations):
    for o in observations:
        print('{}/observations/{}/'.format(NETWORK_BASE_URL,
                                           o['id']))



def print_observations(norad_id,
                       start,
                       end):
    observations = fetch_observation_data_from_id(norad_id, start, end)

    observations_failed = list(filter(lambda o: o['vetted_status'] == 'failed', observations))
    observations_bad = list(filter(lambda o: o['vetted_status'] == 'bad', observations))
    observations_unkown = list(filter(lambda o: o['vetted_status'] == 'unknown', observations))
    observations_good = list(filter(lambda o: o['vetted_status'] == 'good', observations))

    print("GOOD/UNKOWN/BAD/FAILED = {}/{}/{}/{}".format(len(observations_good),
                                                        len(observations_unkown),
                                                        len(observations_bad),
                                                        len(observations_failed)))
    if len(observations) < 1:
       print("No good observations available.")
       return

    # Find the first start time and the last end time of the observations
    # NOTE: Assuming a full coverage in between here!
    #       The ipython notebook for SSTV drops the assumption and calculates all
    #       non-overlapping, continuous observation windows
    start_time_str = sorted(observations, key=lambda obs: obs['start'])[0]['start']
    end_time_str = sorted(observations, key=lambda obs: obs['end'])[-1]['end']

    if observations_good:
        print("GOOD:")
        show_obs(sorted(observations_good, key=lambda o: o['id']))

    if observations_unkown:
        print("UNKOWN:")
        show_obs_url(sorted(observations_unkown, key=lambda o: o['id']))

    if observations_bad:
        print("BAD:")
        show_obs(sorted(observations_bad, key=lambda o: o['id']))

    if observations_failed:
        print("FAILED:")
        show_obs(sorted(observations_failed, key=lambda o: o['id']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get all SatNOGS observations for a given satellite within the given start and end times and pretty-print them on stdput.')
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

    args = parser.parse_args()

    print_observations(norad_id=args.norad_id,
                       start=args.start,
                       end=args.end)
