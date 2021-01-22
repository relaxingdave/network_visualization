import ast
import folium
import io
import logging
import matplotlib
import numpy as np
import os
import config

from sklearn.preprocessing import minmax_scale
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(processName)s %(levelname)s %(name)s %(message)s',
)


# get dictionaries out of strings with ast and save coordinates
def get_long_lat(rides):
    rides['from_lat'] = rides['from_stop_geoc'].apply(
        lambda x: ast.literal_eval(f"""{x}""")['latitude'])
    rides['from_long'] = rides['from_stop_geoc'].apply(
        lambda x: ast.literal_eval(f"""{x}""")['longitude'])
    rides['to_lat'] = rides['to_stop_geoc'].apply(
        lambda x: ast.literal_eval(f"""{x}""")['latitude'])
    rides['to_long'] = rides['to_stop_geoc'].apply(
        lambda x: ast.literal_eval(f"""{x}""")['longitude'])

    return rides


def group_cap(
        rides,
        groupby_cols,
):
    """Group capacity by defined cols

    :param rides: DataFrame to group
    :param groupby_cols: list of grouping cols
    :return: DataFrame
    """

    agg_dict = {
        'from_lat': 'min',
        'from_long': 'max',
        'capacity': 'sum',
        'num_buses': 'sum',
        'passengers': 'sum',
    }

    rides = rides.groupby(
        groupby_cols,
        as_index=False
    ).agg(agg_dict)

    return rides


def scale_color_column(df, color_column, limits=(0, 200)):
    # to query the color map, we need to scale the values
    # Since colormap is scaled from 0 to 100 and we want the
    # values > mean to have the highest color, we scale it up
    # to 200.
    df[f"{color_column}_scaled"] = minmax_scale(
        df[color_column], feature_range=limits
    )
    return df


def get_color_from_colormap(cmap, value):
    """Outputs a color hex value according to a number.

    :param cmap: colormap
    :param value: value to get color for
    :return: hex color value
    """

    color_int = int(round(value))
    rgb = cmap(color_int)[:3]
    hex_color = matplotlib.colors.rgb2hex(rgb)

    return hex_color


# TODO pull out preprocessing steps like radius and color definition and save
# them as columns in the dataframe to increase speed of generating maps.
def plot_color_circles(df, color_column, cmap, zoom_start=5, radius_scale=50):

    # initialize map
    folium_map = folium.Map(location=[50.109900, 8.648916],
                            zoom_start=zoom_start,
                            tiles="CartoDB dark_matter")

    # draw circle for all rows
    # (since we grab every segment, this corresponds to segments)
    for index, row in df.iterrows():

        radius = row['capacity'] / radius_scale

        # query colormap with normalized values
        color_int = int(round(row[color_column]))
        rgb = cmap(color_int)[:3]
        color_hex = matplotlib.colors.rgb2hex(rgb)

        marker = folium.CircleMarker(
            location=(
                row["from_lat"],
                row["from_long"]
            ),
            radius=radius,
            color=color_hex,
            opacity=0.2,
            fill_opacity=0.3,
            fill=True
        )

        marker.add_to(folium_map)

    return folium_map


def interpolate(
        df1, df2, float_hour, int_cols=['capacity', 'pax_per_cap_norm_scaled']
):
    """return a weighted average of two dataframes"""

    merged_df = df1.merge(
        df2,
        on=['from_lat', 'from_long'],
        how='left')
    merged_df = merged_df.fillna(0)

    intpol_factor = float_hour % 1

    for col in int_cols:
        merged_df[col] = (
                merged_df[f'{col}_x'] * (1 - intpol_factor)
                + merged_df[f'{col}_y'] * intpol_factor
        )
        merged_df = merged_df.drop([f'{col}_x', f'{col}_y'], axis=1)

    return merged_df.replace(np.nan, 0)


def get_interpolated_cap(float_unit, grouped_data):
    """get an interpolated dataframe for any time, based
    on hourly data"""

    time_unit = config.groupby_cols[1]

    df1 = grouped_data.query(
        f"{config.groupby_cols[1]}=={int(float_unit)}"
    )

    if (
            (time_unit == 'dep_week' and float_unit < 52) or
            (time_unit == 'dep_hour' and float_unit < 23)
    ):
        df2 = grouped_data.query(
            f"{time_unit}=={int(float_unit) + 1}"
        )
    else:
        df2 = grouped_data.query(f"{time_unit}=={int(0)}")

    columns = ['from_lat', 'from_long', 'capacity', 'pax_per_cap_norm_scaled']

    # add other columns
    df = interpolate(df1.loc[:, columns],
                     df2.loc[:, columns],
                     float_unit)

    return df


def create_interpol_color_cap_frame(
        i,
        grouped_data,
        time_unit,
        color_column,
        cmap,
        zoom_start=5,
        radius_scale=50
):
    interpol_cap = get_interpolated_cap(time_unit, grouped_data)

    plot = plot_color_circles(
        df=interpol_cap,
        color_column=color_column,
        cmap=cmap,
        zoom_start=zoom_start,
        radius_scale=radius_scale
    )

    # generate the png file as a byte array
    png = plot._to_png()
    # create a PIL image object
    image = Image.open(io.BytesIO(png))
    draw = ImageDraw.ImageDraw(image)

    # load a font
    font = ImageFont.truetype("RobotoCondensed-Light.ttf", 30)

    if config.groupby_cols[1] == 'dep_hour':

        # add a caption to the image to indicate the time-of-day.
        hour = int(time_unit)
        minutes = int((time_unit % 1) * 60)

        # draw time of day text
        draw.text((20, image.height - 50),
                  "time: {:0>2}:{:0>2}h".format(hour, minutes),
                  fill=(255, 255, 255),
                  font=font)

    elif config.groupby_cols[1] == 'dep_week':
        # add a caption to the image to indicate the week of the year.
        week = int(time_unit)

        # draw time of day text
        draw.text((20, image.height - 50),
                  f"Week {week}",
                  fill=(255, 255, 255),
                  font=font)

    # draw title
    draw.text((image.width - 450, 20),
              "Offered Capacity 2020",
              fill=(255, 255, 255),
              font=font)

    filename = os.path.join(
        "interpol_color_animation/frame_{:0>5}.png".format(i))
    image.save(filename, "PNG")
