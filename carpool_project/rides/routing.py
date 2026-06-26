from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ride/(?P<ride_id>\d+)/$', consumers.RideSimulationConsumer.as_asgi()),
    re_path(r'ws/rides/$', consumers.RideListConsumer.as_asgi()),
]
