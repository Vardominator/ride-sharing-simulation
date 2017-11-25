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
        self.shift_x = 400
        self.shift_y = 20
        self.duration = 0.1
        self.dt = 0.1
        self.intersections = []
        self.icoords = []
        self.cars = []
        self.car_labels = []
        self.active_reservations = []
        self.simulation = Simulation(time=200.0, num_drivers=3)
        self.initialize_map()
        self.initialize_monitor()

        self.reservation_ids = []
        
        self.keys_being_pressed = set()

        self.simulation.run()

        self.all_events = self.simulation.all_events
        self.frame = 0

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
            event_type = next_event[2]['event_type']
            event = next_event[2]['event']
            if event_type == 'reservation':
                if event['reservation_id'] not in self.reservation_ids:
                    self.reservation_ids.append(event['reservation_id'])
                    reservation = cocos.sprite.Sprite('resources/reservation.png')
                    location = (event['current_location'][0]*50 + self.shift_x, event['current_location'][1]*50 + self.shift_y)
                    reservation.position = location
                    self.active_reservations.append(reservation)
                    self.add(reservation)
            elif event_type == 'intersection arrival':
                driver = event['driver']
                self.move_to_intersection(driver)
            self.frame += 1

    def move_to_intersection(self, driver):
        id = driver['driver_id']
        driver_position = driver['current_location']
        driver_sprite = self.cars[id]
        driver_new_position = (driver_position[0]*50 + self.shift_x, driver_position[1]*50 + self.shift_y)
        driver_sprite.do(MoveTo(driver_new_position, self.duration))

        for reservation in driver['current_reservations']:
            reservation_location = reservation['current_location']
            reservation_destination = reservation['dropoff_coords']
            reservation_id = reservation['reservation_id']
            reservation_sprite = self.active_reservations[reservation_id]

            if reservation_location[0] == reservation_destination[0] and reservation_location[1] == reservation_destination[1]:
                reservation_sprite.do(Place((-100, -100)))
            elif driver_position[0] == reservation_location[0] and driver_position[1] == reservation_location[1]:
                reservation_sprite.do(MoveTo(driver_new_position, self.duration))

        car_id_sprite = self.car_labels[id]
        car_id_sprite_new_position = (driver_position[0]*50 + self.shift_x + 20, driver_position[1]*50 + self.shift_y - 20)
        car_id_sprite.do(MoveTo(car_id_sprite_new_position, self.duration))

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