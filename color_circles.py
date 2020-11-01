# TODO group by city
# exclude train
# get data from before crisis
# refactor preprocessing to pull stuff from plot circles
# why is 1:09 displayed instead of 1:10? can we round to 10s?
# add additional graphs to corner? look for python paste image into image

import pandas as pd
import logging
import numpy as np
import os
import sqlalchemy as sa

from folium import plugins
from queries import ride_segments_query

import folium
from folium import plugins
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib.colors import LinearSegmentedColormap, rgb_to_hsv, hsv_to_rgb
import scipy.ndimage.filters
import time
import datetime
import os.path


from circle_helpers import (
    get_long_lat,
    group_cap_per_hour,
    scale_color_column,
    create_interpol_color_cap_frame,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(processName)s %(levelname)s %(name)s %(message)s',
)

# ============
# Get data
# ============
logger.info(f'Reading the data...')

# CCOPTI_PROD = os.environ['POSTGRES_CONN_STR_PROD']
# pg_prod = sa.create_engine(CCOPTI_PROD)

# query data or read from saved file
# rides = pd.read_sql(ride_segments_query, pg_prod)
# pd.to_pickle(rides, "rides.pkl")
rides = pd.read_pickle(
    '/Users/davidbiermann/Python_projects/network_visualization/rides.pkl'
)

# ============
# Preprocessing
# ============
logger.info(f'Preprocessing the data...')
rides.departure_time = [
    datetime.datetime.strptime(x, '%H:%M:%S') for x in rides['departure_time']
]

rides = get_long_lat(rides)

# group data to get capacity by departure hour
hour_grouped_cap = group_cap_per_hour(rides)

del rides

hour_grouped_cap['pax_per_cap'] = (
    hour_grouped_cap.passengers / hour_grouped_cap.capacity
)
# skewed distribution is normalized
hour_grouped_cap['pax_per_cap_norm'] = (
    (hour_grouped_cap.pax_per_cap-hour_grouped_cap.pax_per_cap.mean())
    / hour_grouped_cap.pax_per_cap.std()
)
# color column is scaled to match the colormap
hour_grouped_cap = scale_color_column(
    hour_grouped_cap, 'pax_per_cap_norm', limits=(0, 200)
)

# ============
# Create map
# ============
logger.info(f'Create the maps...')
# create colormap
cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
    "", ["red", "lime"], N=100
)

for i, dep_hour in enumerate(np.arange(0, 24, 1/6)):
    logger.info(f"creating map for dep hour {dep_hour}")
    create_interpol_color_cap_frame(
        i=i,
        df=hour_grouped_cap,
        dep_hour=dep_hour,
        color_column='pax_per_cap_norm_scaled',
        cmap=cmap,
        zoom_start=5,
        radius_scale=2000,
    )
