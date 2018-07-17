## Installation
```
pip install -r requirements.txt
```

## Usage
```

$ ./analyze_ARISS_Contact.py --help
usage: analyze_ARISS_Contact.py [-h] [--norad-id norad_id]
                                start end output_dir

Generate a geojson file and observations metadata based on observations
filtered on start and end time.

positional arguments:
  start                The start time of the observation filter, formatted as
                       %Y-%m-%dT%H:%M:%SZ
  end                  The end time of the observation filter, formatted like
                       the start time
  output_dir           The directory where all ouput files (metadata cache and
                       geojson file) are written to

optional arguments:
  -h, --help           show this help message and exit
  --norad-id norad_id  The NORAD ID of the selected satellite. Default is the
                       ISS: 25544
```

```

$ ./print_observations.py --help
usage: print_observations.py [-h] [--norad-id norad_id] start end

Get all SatNOGS observations for a given satellite within the given start and
end times and pretty-print them on stdput.

positional arguments:
  start                The start time of the observation filter, formatted as
                       %Y-%m-%dT%H:%M:%SZ
  end                  The end time of the observation filter, formatted like
                       the start time

optional arguments:
  -h, --help           show this help message and exit
  --norad-id norad_id  The NORAD ID of the selected satellite. Default is the
                       ISS: 25544
```

Example usage of `print_observations.py`:
```

$ ./print_observations.py 2018-07-17T08:10:00Z 2018-07-17T09:10:00Z
https://network.satnogs.org/api/observations/?satellite__norad_cat_id=25544&start=2018-07-17T08:10:00&end=2018-07-17T09:10:00
GOOD/UNKOWN/BAD/FAILED = 0/4/0/0
UNKOWN:
https://network.satnogs.org/observations/184743/
https://network.satnogs.org/observations/184744/
https://network.satnogs.org/observations/184745/
https://network.satnogs.org/observations/184779/
```

The provided data files for some ARISS contacts were produced using
the following calls of this script:
```
./analyze_ARISS_Contact.py 2018-07-03T06:00:00Z 2018-07-03T10:50:50Z ARISS_Contact20180703
./analyze_ARISS_Contact.py 2018-07-13T13:50:00Z 2018-07-13T14:20:00Z ARISS_Contact20180713
./analyze_ARISS_Contact.py 2018-07-17T08:10:00Z 2018-07-17T09:10:00Z ARISS_Contact20180717
```
