import json
import asyncio
import math
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class RideSimulationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.group_name = f'ride_{self.ride_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        ride_data = await self.get_ride_data()
        if ride_data:
            await self.send(text_data=json.dumps(ride_data))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'start_simulation':
            await self.start_simulation()
        elif action == 'get_position':
            ride_data = await self.get_ride_data()
            if ride_data:
                await self.send(text_data=json.dumps(ride_data))

    async def ride_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_ride_data(self):
        try:
            from .models import Ride
            ride = Ride.objects.select_related('driver', 'office').get(id=self.ride_id)
            passengers = ride.passengers.filter(status='confirmed').select_related('passenger')

            coords = []
            if ride.route_geometry:
                try:
                    coords = json.loads(ride.route_geometry)
                except:
                    coords = []

            return {
                'type': 'ride_state',
                'ride_id': ride.id,
                'status': ride.status,
                'progress': ride.simulation_progress,
                'current_lat': ride.current_lat or ride.departure_lat,
                'current_lon': ride.current_lon or ride.departure_lon,
                'departure_lat': ride.departure_lat,
                'departure_lon': ride.departure_lon,
                'office_lat': ride.office.lat,
                'office_lon': ride.office.lon,
                'driver_name': ride.driver.get_full_name() or ride.driver.username,
                'office_name': ride.office.name,
                'route_coords': coords,
                'passengers': [
                    {
                        'name': p.passenger.get_full_name() or p.passenger.username,
                        'lat': p.pickup_lat,
                        'lon': p.pickup_lon,
                    }
                    for p in passengers if p.pickup_lat
                ],
            }
        except Exception as e:
            return {'type': 'error', 'message': str(e)}

    async def start_simulation(self):
        try:
            from .models import Ride
            ride = await database_sync_to_async(
                lambda: Ride.objects.get(id=self.ride_id)
            )()

            if ride.status != 'active':
                await database_sync_to_async(self._set_active)(ride)

            coords = []
            if ride.route_geometry:
                try:
                    coords = json.loads(ride.route_geometry)
                except:
                    pass

            if not coords:
                coords = [
                    [ride.departure_lon, ride.departure_lat],
                    [ride.office.lon, ride.office.lat]
                ]

            total_steps = len(coords)
            if total_steps < 2:
                return

            for i, coord in enumerate(coords):
                progress = (i / (total_steps - 1)) * 100
                lon, lat = coord[0], coord[1]

                await database_sync_to_async(self._update_position)(
                    ride.id, lat, lon, progress
                )

                update_data = {
                    'type': 'position_update',
                    'ride_id': ride.id,
                    'current_lat': lat,
                    'current_lon': lon,
                    'progress': round(progress, 1),
                    'status': 'active' if progress < 100 else 'completed',
                }

                await self.channel_layer.group_send(
                    self.group_name,
                    {'type': 'ride_update', 'data': update_data}
                )

                if progress >= 100:
                    await database_sync_to_async(self._complete_ride)(ride.id)
                    break

                await asyncio.sleep(0.5)

        except Exception as e:
            await self.send(text_data=json.dumps({'type': 'error', 'message': str(e)}))

    def _set_active(self, ride):
        from .models import Ride
        Ride.objects.filter(id=ride.id).update(
            status='active',
            current_lat=ride.departure_lat,
            current_lon=ride.departure_lon
        )

    def _update_position(self, ride_id, lat, lon, progress):
        from .models import Ride
        status = 'completed' if progress >= 100 else 'active'
        Ride.objects.filter(id=ride_id).update(
            current_lat=lat,
            current_lon=lon,
            simulation_progress=progress,
            status=status
        )

    def _complete_ride(self, ride_id):
        from .models import Ride
        Ride.objects.filter(id=ride_id).update(
            status='completed',
            simulation_progress=100.0
        )


class RideListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'ride_list'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ride_list_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
