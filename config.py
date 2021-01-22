# 'local file' or 'database'
data_source = 'local file'
# if data is loaded from local file, provide file name:
file_name = 'city_rides_2020.pkl'

# columns that the data is grouped by. Should be compatible with file name
# if data is loaded from file.
groupby_cols = ['from_city', 'dep_week']

# color column is scaled to match the colormap
# actually the limit end should match the number of colors in the colormap
# which is generated below. But since the distribution of pax per cap is so
# skewed, we decide to assign even to the top 2/3 values (scaled: 100 from 300)
# to have the color of the highest values.
scale_limits = (0, 300)
cmap_limit = 100

radius_scale = 2000
