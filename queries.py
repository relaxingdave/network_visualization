ride_segments_query = """
WITH rides AS 
(
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

WHERE r.status = 'on_sale'
AND departure BETWEEN '2020-01-01' AND '2020-10-01'
)

SELECT rd.*,
COUNT(oi.id) AS passengers
FROM rides AS rd
JOIN ext.api_order_items oi
	ON oi.from_id = rd.from_id AND oi.to_id = rd.to_id AND oi.ride_id = rd.ride_id
AND oi.status = 'paid' AND oi.type IN ('adult', 'child')

GROUP BY 1,2,3,4,5,6,7,8,9,10
"""

