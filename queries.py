ride_segments_query = """
SELECT
r.id AS ride_id,
r.line_id,
s.from_id,
s.to_id,
from_st.gmap_params AS from_stop_geoc,
to_st.gmap_params AS to_stop_geoc,
capacity,
num_buses,
c.departure_date,
c.departure_time

FROM ext.rides_ext_view AS r

JOIN ext.line_variations_segments lvs ON lvs.line_variation_id = r.line_variation_id
JOIN ext.segments s ON lvs.segment_id = s.id
JOIN ext.calendar c ON c.ride_id=r.id AND c.to_id = s.to_id AND c.from_id = s.from_id
JOIN ext.stops from_st ON from_st.id = s.from_id
JOIN ext.stops to_st ON to_st.id = s.to_id

WHERE r.status = 'on_sale' AND departure BETWEEN '2020-01-01' AND '2020-01-03'
"""

