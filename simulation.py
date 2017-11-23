import pprint
import numpy as np
from queue import PriorityQueue

class Simulation(object):
    def __init__(self, time=7200.0, num_drivers=20):
        self.reservations = []
        self.drivers = []
        self.future_event_list = PriorityQueue()
        self.time = time
        self.num_drivers = num_drivers
        self.initialize_reservations()
        self.initialize_drivers(num_drivers)
        self.initialize_future_event_list()

    def initialize_reservations(self):
        time = 0.0
        while time < self.time:
            if time % 60.0 == 0.0:
                # make 2 reservations per minute
                # first reservation
                self.create_reservation(time)
                
                # second reservation: exponential distribution
                second_time = time + np.random.exponential(scale=2)
                self.create_reservation(second_time)

            time += 60.0
        
        if self.reservations[-1]['reserve_time'] > 7200.0:
            self.reservations = self.reservations[:-1]

    def create_reservation(self, time):
        # size of part
        party_size = np.random.choice(np.arange(1,5), 1, p=[0.6, 0.25, 0.10, 0.05])[0]
        
        # reservation 1 time
        reserve_time = time
        
        # carpool
        if party_size == 1:
            prob = [0.5, 0.5]
        elif party_size == 2:
            prob = [0.35, 0.65]
        elif party_size == 3:
            prob = [0.55, 0.45]
        else:
            prob = [0.70, 0.30]
        carpool = np.random.choice(2, 1, p=prob)[0]

        # S1, A1
        pickup_coords = [np.random.choice(20, 1)[0], np.random.choice(20, 1)[0]]
        # S2, A2
        time_of_day = np.random.choice(2, 1, p=[0.75, 0.25])[0]
        gov_streets = [4,8,12,16]
        streets = list(range(20))
        if time_of_day == 0:
            a2 = np.random.choice(gov_streets, 1)
        else:
            a2 = np.random.choice([x for x in streets if x not in gov_streets], 1)

        dropoff_coords = (np.random.choice(20, 1)[0], a2[0])
        self.reservations.append({
            'party_size': party_size,
            'reserve_time': time,
            'dropoff_coords': dropoff_coords,
            'carpool': carpool,
            'current_location': pickup_coords,
            'picked_up': False,
            'pickup_time': -1,
            'dropoff_time': -1
        })

    def initialize_drivers(self, num_drivers):
        for i in range(num_drivers):
            starting_coords = pickup_coords = [np.random.choice(20, 1)[0], np.random.choice(20, 1)[0]]
            capacity = np.random.choice(list(range(1,7)), 1, p=[0.05, 0.05, 0.40, 0.30, 0.15, 0.05])[0]
            self.drivers.append({
                'current_location': starting_coords,
                'idle': True,
                'capacity': capacity,
                'seats_filled': 0,
                'current_reservations': [],
                'serviced_passengers': []
            })

    def initialize_future_event_list(self):
        for reservation in self.reservations:
            self.future_event_list.put(
                (reservation['reserve_time'],
                0, 
                {
                    'event_type': 'reservation',
                    'event': reservation
                }
                )
            )

    def run(self):
        while not self.future_event_list.empty():
            next_event = self.future_event_list.get()
            # print(next_event)
            event_type = next_event[2]['event_type']
            # print(next_event)
            if event_type == 'reservation':
                # RESERVATION EVENT
                reservation = next_event[2]['event']
                # isolate idle drivers
                idle_drivers = [driver for driver in self.drivers 
                                            if driver['idle'] and 
                                               driver['capacity'] - driver['seats_filled'] >= reservation['party_size']]
                # find closest driver to current reservation
                if len(idle_drivers) > 0:
                    passenger_location = reservation['current_location']
                    min_dist = 1000000
                    closest_available_driver = idle_drivers[0]
                    for driver in idle_drivers:
                        driver_location = driver['current_location']
                        dist = sum([abs(driver_location[0]-passenger_location[0]), abs(driver_location[1]-passenger_location[1])])
                        if dist < min_dist:
                            min_dist = dist
                            closest_available_driver = driver
                    closest_available_driver['idle'] = False
                    # don't forget to decrease the party size once they are dropped off
                    closest_available_driver['seats_filled'] += reservation['party_size']
                    # ADD RESERVATION ASSIGNMENT TO FEL
                    self.future_event_list.put(
                        (reservation['reserve_time'],
                        0,
                        {
                            'event_type': 'reservation assignment',
                            'event': {
                                'driver': closest_available_driver,
                                'reservation': reservation 
                            }
                        }
                        )
                    )
            elif event_type == 'reservation assignment':
                # assign driver to reservation
                event = next_event[2]['event']
                driver = event['driver']
                reservation = event['reservation']
                driver['current_reservations'].append(reservation)
                # start moving to intersection that is closer to destination
                # first_location_update = self.update_locations(driver, reservation)
                self.future_event_list.put(
                    (
                        reservation['reserve_time'],
                        0,
                        {
                            'event_type': 'intersection arrival',
                            'event':{
                                'driver': driver
                            }
                        }
                    )
                )

            elif event_type == 'intersection arrival':
                event = next_event[2]['event']
                driver = event['driver']
                current_time = next_event[0]
                reservations = driver['current_reservations']
                location_update_time = self.update_locations(driver, reservations[0]['picked_up'])
                arrival_time = current_time + location_update_time
                
                if location_update_time == -1:
                    # issue pick up or drop off event because driver has arrived to passenger or destination
                    if not reservations[0]['picked_up']:
                        self.future_event_list.put(
                            (
                                arrival_time,
                                0,
                                {
                                    'event_type': 'pick up',
                                    'event':{
                                        'driver': driver
                                    }
                                }
                            )
                        )
                    else:
                        self.future_event_list.put(
                            (
                                arrival_time,
                                0,
                                {
                                    'event_type': 'drop off',
                                    'event':{
                                        'driver': driver
                                    }
                                }
                            )
                        )
                else:
                    # issue another intersection arrival event
                    second_priority = 0
                    if any(arrival_time in event for event in self.future_event_list.queue):
                        second_priority += 1
                    self.future_event_list.put(
                        (
                            arrival_time,
                            second_priority,
                            {
                                'event_type': 'intersection arrival',
                                'event':{
                                    'driver': driver
                                }
                            }
                        )
                    )
            elif event_type == 'pick up':
                event = next_event[2]['event']
                driver = event['driver']
                current_time = next_event[0]
                reservations = driver['current_reservations']
                reservations[0]['picked_up'] = True
                reservations[0]['pickup_time'] = current_time
                location_update_time = self.update_locations(driver, reservations[0]['picked_up'])
                arrival_time = current_time + location_update_time
                second_priority = 0
                if any(arrival_time in event for event in self.future_event_list.queue):
                    second_priority += 1
                self.future_event_list.put(
                    (
                        arrival_time,
                        second_priority,
                        {
                            'event_type': 'intersection arrival',
                            'event': {
                                'driver': driver
                            }
                        }
                    )
                )
            elif event_type == 'drop off':
                # drop off passenger and issue idle_arrival event for driver to look for reservation
                event = next_event[2]['event']
                driver = event['driver']
                current_time = next_event[0]
                reservations = driver['current_reservations']
                reservations[0]['dropoff_time'] = current_time
                driver['serviced_passengers'].append(reservations[0])
                driver['seats_filled'] -= reservations[0]['party_size']
                reservations.remove(reservations[0])
                self.future_event_list.put(
                    (
                        arrival_time,
                        0,
                        {
                            'event_type': 'idle_arrival',
                            'event': {
                                'driver': driver
                            }
                        }
                    )
                )
            elif event_type == 'idle_arrival':
                event = next_event[2]['event']
                driver = event['driver']
                current_time = next_event[0]
                driver['idle'] = True
                for reservation in self.reservations:
                    if not reservation['picked_up']:
                        print(reservation)
                        self.future_event_list.put(
                            (
                                current_time,
                                0,
                                {
                                    'event_type': 'reservation',
                                    'event': reservation
                                }
                            )
                        )
                        break

    @staticmethod
    def update_locations(driver, picked_up = False):
        """Take driver and passenger to an intersection that is closer to the destination"""
        # uses normal distribution
        # print(picked_up)
        # 1. check if driver is at pickup location
        # 2. if not, move driver closer to passenger location using normal distribution
        current_reservation = driver['current_reservations'][0]
        current_reservation_location = current_reservation['current_location']

        # reservation_location = reservation['current_location']
        driver_location = driver['current_location']
        dx = current_reservation_location[0] - driver_location[0]
        dy = current_reservation_location[1] - driver_location[1]

        intersection_arrival_time_length = np.random.normal(60, 20)

        if dx == 0 and dy == 0:
            if not picked_up:
                return -1
            else:
                # move driver and passenger to closest location
                dropoff_coords = current_reservation['dropoff_coords']
                dx2 = dropoff_coords[0] - driver_location[0]
                dy2 = dropoff_coords[1] - driver_location[1]
                if dx2 == 0 and dy2 == 0:
                    return -1
                else:
                    if dx2 == 0:
                        if dy2 < 0:
                            driver_location[1] -= 1
                            current_reservation_location[1] -= 1
                        else:
                            driver_location[1] += 1
                            current_reservation_location[1] += 1
                    elif dy2 == 0:
                        if dx2 < 0:
                            driver_location[0] -= 1
                            current_reservation_location[0] -= 1
                        else:
                            driver_location[0] += 1
                            current_reservation_location[0] += 1
                    else:
                        # move randomly in either x or y
                        x_or_y = np.random.choice([0, 1], 1)[0]
                        if x_or_y == 0:
                            if dx2 < 0:
                                driver_location[0] -= 1
                                current_reservation_location[0] -= 1
                            else:
                                driver_location[0] += 1
                                current_reservation_location[0] += 1
                        else:
                            if dy2 < 0:
                                driver_location[1] -= 1
                                current_reservation_location[1] -= 1
                            else:
                                driver_location[1] += 1
                                current_reservation_location[1] += 1

                return intersection_arrival_time_length

        if dx == 0:
            # move 1 step in the y direction
            if dy < 0:
                driver_location[1] -= 1
            else:
                driver_location[1] += 1
        elif dy == 0:
            # move 1 step in the x direction
            if dx < 0:
                driver_location[0] -= 1
            else:
                driver_location[0] += 1
        else:
            # move randomly in either x or y
            x_or_y = np.random.choice([0, 1], 1)[0]
            if x_or_y == 0:
                # move in the x direction
                if dx < 0:
                    driver_location[0] -= 1
                else:
                    driver_location[0] += 1
            else:
                # move in the y direction
                if dy < 0:
                    driver_location[1] -= 1
                else:
                    driver_location[1] += 1
            
        return intersection_arrival_time_length

        # print('driver location: {}'.format(driver_location))
        # print('reservation location: {}'.format(reservation_location))
        # print(dx)
        # print(dy)


        # return intersection arrival time
        print()
        # pass

if __name__ == "__main__":

    while True:
        try:
            sim = Simulation()
            sim.run()
            for res in sim.reservations:
                print(res)
            break
        except TypeError:
            print('type error')
    # for driver in sim.drivers:
    #     print(driver)
