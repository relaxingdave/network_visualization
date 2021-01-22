# TODO
# why is 1:09 displayed instead of 1:10? can we round to 10s?
# add additional graphs to corner? look for python paste image into image
# weekly development Corona / all time

import datetime
import pandas as pd
import logging
import numpy as np
import os
import matplotlib.colors
import sqlalchemy as sa


from circle_helpers import (
    get_long_lat,
    group_cap,
    scale_color_column,
    create_interpol_color_cap_frame,
)
from queries import ride_segments_query
import config


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(processName)s %(levelname)s %(name)s %(message)s',
)


def main():

    # ============
    # Get data
    # ============
    logger.info(f'Reading the data from {config.data_source}')

    if config.data_source == 'local file':
        rides = pd.read_pickle(
            '/Users/davidbiermann/Python_projects/network_visualization/'
            f'{config.file_name}'
        )

    elif config.data_source == 'database':
        CCOPTI_PROD = os.environ['POSTGRES_CONN_STR_PROD']
        pg_prod = sa.create_engine(CCOPTI_PROD)

        rides = pd.read_sql(ride_segments_query, pg_prod)
        pd.to_pickle(rides, "city_rides_2020.pkl")
    else:
        raise ValueError(f"{config.data_source} not allowed as data source.")

    # ============
    # Preprocessing
    # ============
    logger.info(f'Preprocessing the data with {len(rides)} rows')
    rides.departure_time = [
        datetime.datetime.strptime(x, '%H:%M:%S') for x in rides['departure_time']
    ]
    rides = get_long_lat(rides)
    rides['dep_hour'] = [x.hour for x in rides.departure_time]
    rides['dep_week'] = [x.week for x in rides.departure_date]

    # group data to get capacity by departure hour
    grouped_data = group_cap(rides, config.groupby_cols)

    logger.info(f'Grouped data has {len(grouped_data)} rows. Computing metrics...')
    grouped_data['pax_per_cap'] = (
            grouped_data.passengers / grouped_data.capacity
    )
    # skewed distribution is normalized
    grouped_data['pax_per_cap_norm'] = (
            (grouped_data.pax_per_cap - grouped_data.pax_per_cap.mean())
            / grouped_data.pax_per_cap.std()
    )
    grouped_data = scale_color_column(
        grouped_data, 'pax_per_cap_norm', limits=config.scale_limits
    )

    # ============
    # Generating map parameters
    # ============
    logger.info(f'Generating map parameters...')

    # create colormap
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "", ["red", "lime"], N=config.cmap_limit
    )

    # ============
    # Create map
    # ============
    logger.info(f'Create the maps...')

    loop_array = np.arange(1, 45, 1/7)

    for i, time_unit in enumerate(loop_array):
        logger.info(
            f"creating map for time unit {time_unit}"
            f"({i} out of {len(loop_array)-1})."
        )
        create_interpol_color_cap_frame(
            i=i,
            grouped_data=grouped_data,
            time_unit=time_unit,
            color_column='pax_per_cap_norm_scaled',
            cmap=cmap,
            zoom_start=5,
            radius_scale=config.radius_scale,
        )


if __name__ == '__main__':
    # here we go
    main()
