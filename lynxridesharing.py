from __future__ import division, print_function, unicode_literals

# This code is so you can run the samples without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
#

import cocos
from cocos.director import director
from cocos.actions import *

from pyglet.window.key import symbol_string
from simulation import Simulation

class LynxRideSharing(cocos.layer.Layer):

    is_event_handler = True
    def __init__(self):

        super(LynxRideSharing, self).__init__()

        self.completed_amount_label = cocos.text.Label(
            '0',
            font_name = 'Arial',
            font_size = 20,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (270,820),
            color = (124,252,0, 255)
        )
        self.add(self.completed_amount_label)

        self.free_amount_label = cocos.text.Label(
            '0',
            font_name = 'Arial',
            font_size = 20,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (270,770),
            color = (255,0,0, 255)
        )
        self.add(self.free_amount_label)

        self.time_label = cocos.text.Label(
            '0',
            font_name = 'Arial',
            font_size = 18,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (225,700),
            color = (255,255,255, 255)
        )
        self.add(self.time_label)

        self.shift_x = 400
        self.shift_y = 20
        self.duration = 0.05
        self.dt = 0.005
        self.intersections = []
        self.icoords = []
        self.cars = []
        self.car_labels = []
        self.active_reservations = []
        self.simulation = Simulation(num_drivers=10, num_reservations=40)
        self.initialize_map()
        self.initialize_monitor()

        self.reservation_ids = []
        self.first_time_moves = []

        self.keys_being_pressed = set()

        self.simulation.run()
        # for reservantion in self.simulation.reservations:
        #     print(reservantion)
        # for reservation in self.simulation.reservations:
        #     self.reservation_ids.append(reservation['reservation_id'])
        #     self.first_time_moves.append(False)
        #     reservation_str = cocos.sprite.Sprite('resources/reservation.png')
        #     location = (reservation['current_location'][0]*50 + self.shift_x, reservation['current_location'][1]*50 + self.shift_y)
        #     reservation_str.position = location
        #     self.active_reservations.append(reservation_str)
        #     self.add(reservation_str)

        self.all_events = self.simulation.all_events
        self.frame = 0

        self.free_rides = 0
        self.completed_reservations = set()

        self.schedule_interval(self.run_simulation, self.dt)


    def initialize_monitor(self):
        title = cocos.text.Label(
            'Lynx Ride Sharing',
            font_name = 'Arial',
            font_size = 28,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (190,970)
        )
        self.add(title)
        reservation_goal = cocos.text.Label(
            'Goal: {} Reservations'.format(self.simulation.num_reservations),
            font_name = 'Arial',
            font_size = 20,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (190,870)
        )
        self.add(reservation_goal)
        completed = cocos.text.Label(
            'Completed: ',
            font_name = 'Arial',
            font_size = 20,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (175,820),
        )
        self.add(completed)
        free = cocos.text.Label(
            'Free Rides: ',
            font_name = 'Arial',
            font_size = 20,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (175,770),
        )
        self.add(free)
        time = cocos.text.Label(
            'Time: ',
            font_name = 'Arial',
            font_size = 18,
            anchor_x = 'center',
            anchor_y = 'center',
            position = (160,700),           
        )
        self.add(time)

    def initialize_map(self):
        # place intersections
        for x in range(0 + self.shift_x, 1000 + self.shift_x, 50):
            for y in range(0 + self.shift_y, 1000 + self.shift_y, 50):
                isection = cocos.sprite.Sprite('resources/intersection.jpg')
                isection.position = x, y
                self.intersections.append(isection)
                self.icoords.append((x,y))
                self.add(isection)

        # place cars
        for driver in self.simulation.drivers:
            car = cocos.sprite.Sprite('resources/ferrari.png')
            car.position = (driver['initial_location'][0]*50 + self.shift_x, driver['initial_location'][1]*50 + self.shift_y)
            car_id_label = cocos.text.Label(
                str(driver['driver_id']),
                font_name = 'Arial',
                font_size = 12,
                anchor_x = 'center',
                anchor_y = 'center',
                position = (driver['initial_location'][0]*50 + self.shift_x + 20, driver['initial_location'][1]*50 + self.shift_y - 20)
            )
            self.cars.append(car)
            self.car_labels.append(car_id_label)
            self.add(car)
            self.add(car_id_label)

    def run_simulation(self, dt):
        if self.frame < len(self.all_events):
            next_event = self.all_events[self.frame]
            event_time = next_event[0]
            event_type = next_event[1]['event_type']
            event = next_event[1]['event']

            self.time_label.element.text = '{}:{}'.format(int(event_time/60), '{0:0>2}'.format(int(event_time%60)))

            if event_type == 'reservation':
                print(event['reservation_id'])
                if event['reservation_id'] not in self.reservation_ids:
                    print(event['reservation_id'])
                    self.reservation_ids.append(event['reservation_id'])
                    self.first_time_moves.append(False)
                    reservation = cocos.sprite.Sprite('resources/reservation.png')
                    location = (event['current_location'][0]*50 + self.shift_x, event['current_location'][1]*50 + self.shift_y)
                    reservation.position = location
                    self.active_reservations.append(reservation)
                    # self.add(reservation)
            elif event_type == 'intersection arrival':
                driver = event['driver']
                self.move_to_intersection(driver, event_time)
            self.frame += 1


    def move_to_intersection(self, driver, time):
        id = driver['driver_id']
        driver_position = driver['current_location']
        driver_sprite = self.cars[id]
        driver_new_position = (driver_position[0]*50 + self.shift_x, driver_position[1]*50 + self.shift_y)
        driver_sprite.do(MoveTo(driver_new_position, self.duration))

        car_id_sprite = self.car_labels[id]
        car_id_sprite_new_position = (driver_position[0]*50 + self.shift_x + 20, driver_position[1]*50 + self.shift_y - 20)
        car_id_sprite.do(MoveTo(car_id_sprite_new_position, self.duration))

        for reservation in driver['current_reservations']:
            reservation_location = reservation['current_location']
            reservation_destination = reservation['dropoff_coords']
            reservation_id = reservation['reservation_id']
            reservation_sprite = self.active_reservations[reservation_id]

            reserve_time = reservation['reserve_time']
            dropoff_time = reservation['dropoff_time']
            # print(dropoff_time)
            if time >= reserve_time:
                self.add(reservation_sprite)

            if reservation_location[0] == reservation_destination[0] and reservation_location[1] == reservation_destination[1]:
                reservation_sprite.do(Place((-100, -100)))
                # self.completed_rides += 1
                # print("completed rides: {}".format(self.completed_rides))
                self.completed_reservations.add(reservation_id)
                # print("completed_rides: {}".format(len(self.completed_reservations)))
                self.completed_amount_label.element.text = str(len(self.completed_reservations))
            elif driver_position[0] == reservation_location[0] and driver_position[1] == reservation_location[1]:
                new_reservation_location = (reservation_location[0]*50 + self.shift_x, reservation_location[1]*50 + self.shift_y)
                reservation_sprite.do(MoveTo(new_reservation_location, self.duration))

                if not self.first_time_moves[reservation_id]:
                    # print('time: {}'.format(time))
                    # print('reservation time: {}'.format(reservation['reserve_time']))
                    # print('wait time(m): {}'.format((time - reservation['reserve_time'])/60.0))
                    self.first_time_moves[reservation_id] = True
                    # print(reservation['pickup_time'] - reservation['reserve_time'])
                    if (time - reservation['reserve_time'])/60.0 > 15.0:
                        self.free_rides += 1
                        self.free_amount_label.element.text = str(self.free_rides)
                        # print("free rides: {}".format(self.free_rides))
                        # print("percentage: {}%".format(100 * len(self.completed_reservations)/(len(self.completed_reservations) + self.free_rides)))

            # if reservation_location[0] == reservation_destination[0] and reservation_location[1] == reservation_destination[1]:
            #     reservation_sprite.do(Place((-100, -100)))
            #     # self.completed_rides += 1
            #     # print("completed rides: {}".format(self.completed_rides))
            #     self.completed_reservations.add(reservation_id)
            #     # print("completed_rides: {}".format(len(self.completed_reservations)))
            #     self.completed_amount_label.element.text = str(len(self.completed_reservations))

        for reservation in driver['serviced_passengers']:
            reservation_id = reservation['reservation_id']
            reserve_spr = self.active_reservations[reservation_id]
            reserve_spr.do(Place((-100,-100)))


    def on_key_press(self, key, modifiers):
        self.keys_being_pressed.add(key)

        if symbol_string(key) == "RIGHT":
            print(symbol_string(key))
            self.run_simulation()


if __name__ == "__main__":
    # initialize and create a window
    director.init(width=1400, height=1000, caption="Lynx - Ferrari's Only", fullscreen=False)

    # create a hello world instance
    lynx_layer = LynxRideSharing()

    # create a scene that contains the LynxRideSharing layer
    main_scene = cocos.scene.Scene(lynx_layer)

    # run the scene
    director.run(main_scene)