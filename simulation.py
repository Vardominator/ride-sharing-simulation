import pprint
import numpy as np
from queue import PriorityQueue
import copy

class Simulation(object):
    def __init__(self, time=7200.0, num_drivers=20, num_reservations=100, carpool_threshold=3):
        self.reservations = []
        self.completed_reservations = []
        self.drivers = []
        self.future_event_list = PriorityQueue()
        self.all_events = []
        self.time = time
        self.num_drivers = num_drivers
        self.num_reservations = num_reservations
        self.carpool_threshold = carpool_threshold
        self.initialize_reservations()
        self.initialize_drivers(num_drivers)
        self.initialize_future_event_list()

        self.reservation_ids = []


        self.assignment_calls = 0
        self.assignment_calls_from_intersection_arrival = 0
        self.assignment_calls_from_intersection_reservation = 0
        self.assignment_calls_from_idle_arrival = 0

    def initialize_reservations(self):
        time = 0.0
        while time < self.time:
            if time % 60.0 == 0.0:
                # make 2 reservations per minute
                # first reservation
                if len(self.reservations) <= self.num_reservations:
                    self.create_reservation(time)

                    # second reservation: exponential distribution
                    second_time = time + np.random.exponential(scale=2)
                    self.create_reservation(second_time)

            time += 60.0

        self.reservations = self.reservations[:-2]
        print(len(self.reservations))

    def create_reservation(self, time):
        # size of party
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
            'reservation_id': len(self.reservations),
            'party_size': party_size,
            'reserve_time': time,
            'dropoff_coords': dropoff_coords,
            'carpool': carpool,
            'current_location': pickup_coords,
            'assigned': False,
            'picked_up': False,
            'pickup_time': -1,
            'dropoff_time': -1,
            'driver': None
        })

    def initialize_drivers(self, num_drivers):
        for i in range(num_drivers):
            starting_coords = pickup_coords = [np.random.choice(20, 1)[0], np.random.choice(20, 1)[0]]
            capacity = np.random.choice(list(range(1,7)), 1, p=[0.05, 0.05, 0.40, 0.30, 0.15, 0.05])[0]
            self.drivers.append({
                'driver_id': i,
                'initial_location': starting_coords,
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
                {
                    'event_type': 'reservation',
                    'event': reservation
                }
                )
            )


    def run(self):
        while not self.future_event_list.empty():

            shifter = np.random.uniform(0.0, 1.0)

            next_event = self.future_event_list.get()
            self.all_events.append(copy.deepcopy(next_event))
            # print(next_event)
            event_type = next_event[1]['event_type']
            # print(next_event)
            if event_type == 'reservation':
                # RESERVATION EVENT
                reservation1 = next_event[1]['event']
                # isolate available drivers
                available_drivers = [driver for driver in self.drivers if driver['capacity'] - driver['seats_filled'] >= reservation1['party_size']]
                # find closest driver to current reservation
                if len(available_drivers) > 0 and not reservation1['assigned']:
                    passenger_location = reservation1['current_location']
                    min_dist = 1000000
                    closest_available_driver = None
                    for driver in available_drivers:
                        driver_location = driver['current_location']
                        # dist = sum([abs(driver_location[0]-passenger_location[0]), abs(driver_location[1]-passenger_location[1])])
                        dist = np.linalg.norm(np.array(driver_location) - np.array(passenger_location))
                        if dist < min_dist:
                            min_dist = dist
                            closest_available_driver = driver
                    closest_available_driver['idle'] = False
                    # don't forget to decrease the party size once they are dropped off
                    # closest_available_driver['seats_filled'] += reservation['party_size']
                    # ADD RESERVATION ASSIGNMENT TO FEL
                    # print(closest_available_driver['current_location'])
                    # print(reservation['current_location'])
                    # print()
                    self.assignment_calls_from_intersection_reservation += 1
                    # print("From reservation event: {}".format(self.assignment_calls_from_intersection_reservation))
                    if len(self.completed_reservations) >= len(self.reservations):
                        print("reservation event overdoing")
                    if reservation1['assigned']:
                        print('already assigned (reservation)!')

                    self.future_event_list.put(
                        (
                            reservation1['reserve_time'] + shifter,
                            {
                                'event_type': 'reservation assignment',
                                'event': {
                                    'driver': closest_available_driver,
                                    'reservation': reservation1
                                }
                            }
                        )
                    )
            elif event_type == 'reservation assignment':
                self.assignment_calls += 1
                # print('reservation assignment calls: {}'.format(self.assignment_calls))
                # assign driver to reservation
                event = next_event[1]['event']
                driver = event['driver']
                reservation2 = event['reservation']
                current_time = next_event[0]
                if reservation2['assigned']:
                    print('already assigned (res assignment)!')
                if not reservation2['assigned']:
                    reservation2 = event['reservation']
                    reservation2['assigned'] = True
                    driver['current_reservations'].append(reservation2)
                    driver['seats_filled'] += reservation2['party_size']
                    reservation2['driver'] = driver
                    # start moving to intersection that is closer to destination
                    self.future_event_list.put(
                        (
                            current_time + shifter,
                            {
                                'event_type': 'intersection arrival',
                                'event': {
                                    'driver': driver
                                }
                            }
                        )
                    )

            elif event_type == 'intersection arrival':
                event = next_event[1]['event']
                driver = event['driver']
                current_time = next_event[0]
                reservations = driver['current_reservations']

                # # carpooling: check if there is an unassigned reservation nearby. If so, trigger assignment event
                # for res in self.reservations:
                #     # check for unassigned reservations
                #     if not res['assigned'] and res['carpool']:

                #         reservation_location = res['current_location']
                #         party_size = res['party_size']
                #         driver_location = driver['current_location']
                #         capacity = driver['capacity']
                #         seats_filled = driver['seats_filled']

                #         # check if driver has space
                #         if party_size <= capacity - seats_filled and not res['assigned']:
                #             # check if reservation is close enough
                #             dx = abs(reservation_location[0] - driver_location[0])
                #             dy = abs(reservation_location[1] - driver_location[1])
                #             if dx <= self.carpool_threshold and dy <= self.carpool_threshold:
                #                 self.assignment_calls_from_intersection_arrival += 1
                #                 # print('From intersection arriva: {}'.format(self.assignment_calls_from_intersection_arrival))
                #                 if len(self.completed_reservations) >= len(self.reservations):
                #                     print("intersection arrival event overdoing")
                #                 if res['assigned']:
                #                     print('already assigned (intersection arrival)!')
                #                 self.future_event_list.put(
                #                     (
                #                         current_time + shifter,
                #                         {
                #                             'event_type': 'reservation assignment',
                #                             'event': {
                #                                 'driver': driver,
                #                                 'reservation': res
                #                             }
                #                         }
                #                     )
                #                 )
                #                 break

                if len(driver['current_reservations']) > 0:

                    closest_reservation = self.closest_reservation(driver)
                    location_update_time = self.update_locations(driver, closest_reservation, closest_reservation['picked_up'])
                    arrival_time = current_time + location_update_time

                    if location_update_time == -1:
                        # issue pick up or drop off event because driver has arrived to passenger or destination
                        if not closest_reservation['picked_up']:
                            # print()
                            # print(closest_reservation['current_location'])
                            # print(driver['current_location'])
                            # print(arrival_time)
                            # print(current_time)
                            # print()
                            self.future_event_list.put(
                                (
                                    current_time + shifter,
                                    {
                                        'event_type': 'pick up',
                                        'event':{
                                            'driver': driver,
                                            'reservation': closest_reservation
                                        }
                                    }
                                )
                            )
                        else:
                            # print()
                            # print()
                            # print(driver['current_reservations'])
                            # print()
                            # print(closest_reservation)
                            # print()
                            # print()
                            self.future_event_list.put(
                                (
                                    arrival_time + shifter,
                                    {
                                        'event_type': 'drop off',
                                        'event':{
                                            'driver': driver,
                                            'reservation': closest_reservation
                                        }
                                    }
                                )
                            )
                    else:
                        # issue another intersection arrival event
                        self.future_event_list.put(
                            (
                                arrival_time + shifter,
                                {
                                    'event_type': 'intersection arrival',
                                    'event':{
                                        'driver': driver
                                    }
                                }
                            )
                        )

            elif event_type == 'pick up':
                event = next_event[1]['event']
                driver = event['driver']
                reservation = event['reservation']
                current_time = next_event[0]
                reservation['picked_up'] = True
                reservation['pickup_time'] = current_time
                # print("reserve time: {}".format(reservation['reserve_time']))
                # print("pickup time: {}".format(current_time))

                # location_update_time = self.update_locations(driver, reservation, reservation['picked_up'])
                # arrival_time = current_time + location_update_time
                self.future_event_list.put(
                    (
                        current_time + shifter,
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
                event = next_event[1]['event']
                driver = event['driver']
                reservation = event['reservation']
                current_time = next_event[0]

                # no carpool stuff
                # current_reservation = self.closest_reservation(driver)

                # driver_location = driver['current_location']
                # current_reservation = driver['current_reservations'][0]
                # current_reservation_location = current_reservation['current_location']

                # # find closest reservation
                # min_dist = 1000000
                # for reservation in reservations:
                #     reservation_location = reservation['current_location']
                #     dist = np.linalg.norm(np.array(driver_location) - np.array(reservation_location))
                #     if dist < min_dist:
                #         min_dist = dist
                #         current_reservation = reservation
                #         current_reservation_location = reservation_location

                reservation['dropoff_time'] = current_time

                driver['serviced_passengers'].append(reservation)
                driver['seats_filled'] -= reservation['party_size']
                self.completed_reservations.append(reservation)

                reservations = driver['current_reservations']
                # print()
                # print()
                # print(reservations)
                # print()
                # print(reservation)
                # print()
                # print()
                reservations.remove(reservation)

                # only trigger idle arrival if reservation list is empty. otherwise trigger, intersection arrival
                if len(reservations) == 0:
                    self.future_event_list.put(
                        (
                            current_time + shifter,
                            {
                                'event_type': 'idle_arrival',
                                'event': {
                                    'driver': driver
                                }
                            }
                        )
                    )
                else:
                    self.future_event_list.put(
                        (
                            current_time + shifter,
                            {
                                'event_type': 'intersection arrival',
                                'event': {
                                    'driver': driver
                                }
                            }
                        )
                    )

            elif event_type == 'idle_arrival':
                event = next_event[1]['event']
                driver = event['driver']
                current_time = next_event[0]
                driver['idle'] = True

                # available_drivers = [driver for driver in self.drivers if driver['idle'] and driver['capacity'] - driver['seats_filled'] >= reservation['party_size']]
                for res in self.reservations:
                    if not res['assigned']:
                        self.assignment_calls_from_idle_arrival += 1
                        # print("from idle arrival: {}".format(self.assignment_calls_from_idle_arrival))
                        if len(self.completed_reservations) >= len(self.reservations):
                            print("idle arrival event overdoing")
                        if res['assigned']:
                            print('already assigned (idle arrival)!')
                        self.future_event_list.put(
                            (
                                current_time,
                                {
                                    'event_type': 'reservation',
                                    'event': res
                                }
                            )
                        )
                        break

    @staticmethod
    def update_locations(driver, closest_reservation, picked_up = False):
        """Take driver and passenger to an intersection that is closer to the destination"""
        # uses normal distribution
        # print(picked_up)
        # 1. check if driver is at pickup location
        # 2. if not, move driver closer to passenger location using normal distribution

        # move closest reservation to front of current reservations list
        # print(len(driver['current_reservations']))
        driver_location = driver['current_location']
        current_reservation = closest_reservation
        current_reservation_location = closest_reservation['current_location']

        # find closest reservation
        # min_dist = 1000000
        # for reservation in driver['current_reservations']:
        #     reservation_location = reservation['current_location']
        #     dist = np.linalg.norm(np.array(driver_location) - np.array(reservation_location))
        #     if dist < min_dist:
        #         min_dist = dist
        #         current_reservation = reservation
        #         current_reservation_location = reservation_location


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
        # print()
        # pass

    @staticmethod
    def closest_reservation(driver):
        driver_location = driver['current_location']
        reservations = driver['current_reservations']
        current_reservation = reservations[0]
        current_reservation_location = current_reservation['current_location']

        # find closest reservation
        min_dist = 1000000
        for reservation in driver['current_reservations']:
            reservation_location = reservation['current_location']
            dist = np.linalg.norm(np.array(driver_location) - np.array(reservation_location))
            if dist < min_dist:
                min_dist = dist
                current_reservation = reservation
                current_reservation_location = reservation_location
        return current_reservation

if __name__ == "__main__":

    # while True:
    #     try:
    sim = Simulation(num_reservations=100, num_drivers=5)
    print(len(sim.reservations))
    # for driver in sim.drivers:
    #     print(driver)
    sim.run()
    for res in sim.reservations:
        print(res['reserve_time'])
        print(res['pickup_time'])
        # print(res['current_location'])
        # print(res['dropoff_coords'])
        # print(res['pickup_time'])
        # print(res)
        # print((res['reserve_time']))
        # print((res['pickup_time']))
        # print()[']
        # print((res['pickup_time'] - res['reserve_time'])/60)
    # # for driver in sim.drivers:
    # #     print(driver)
    # # for event in sim.all_events:
    # #     print(event)
    # print(len(sim.completed_reservations))

        #     break
        # except TypeError:
        #     print('type error')
    # for driver in sim.drivers:
    #     print(driver)
