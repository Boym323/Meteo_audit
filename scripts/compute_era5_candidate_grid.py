#!/usr/bin/env python3
"""Deterministic candidate regular lat/lon grid mapping; not a data download."""
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

SITES = {
    "loucka_2009_public": (49 + 9/60 + 55/3600, 17 + 52/60 + 39/3600),
    "loucka_wu_rounded": (49.166, 17.878),
}
GRIDS = {"era5_cds_atmosphere": 0.25, "era5_land_cds": 0.1}
EARTH_RADIUS_M = 6_371_000

def distance_m(a, b):
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat, dlon = lat2-lat1, lon2-lon1
    h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return EARTH_RADIUS_M * 2 * asin(sqrt(h))

def nearest(value, spacing):
    return round(value / spacing) * spacing

rows=[]
for site, pos in SITES.items():
    for dataset, spacing in GRIDS.items():
        grid=(nearest(pos[0], spacing), nearest(pos[1], spacing))
        rows.append({"site_coordinate_case":site,"dataset":dataset,"spacing_degrees":spacing,
                     "input_latitude":pos[0],"input_longitude":pos[1],
                     "candidate_grid_latitude":round(grid[0],6),"candidate_grid_longitude":round(grid[1],6),
                     "great_circle_distance_m":round(distance_m(pos,grid),1)})
    if site == "loucka_2009_public":
        for lon in (17.75,18.0):
            grid=(49.25,lon)
            rows.append({"site_coordinate_case":site,"dataset":"era5_cds_atmosphere_adjacent_lon_check",
                         "spacing_degrees":0.25,"input_latitude":pos[0],"input_longitude":pos[1],
                         "candidate_grid_latitude":grid[0],"candidate_grid_longitude":grid[1],
                         "great_circle_distance_m":round(distance_m(pos,grid),1)})
print(json.dumps({"method":"nearest point on regular latitude/longitude coordinates; haversine distance for comparison only",
                  "rows":rows},indent=2))
