import pprint
import json
import numpy as np
import scipy.stats as st
from queue import PriorityQueue
import copy
import math

pp = pprint.PrettyPrinter(indent=4)
f = open('events.txt', 'w')

class Simulation(object):
    def __init__(self, time=7200.0, num_drivers=20, num_reservations=100, carpool_threshold=3):
        """Ride Sharing Discrete Event Simulation

        This module populates and maintains a future event list of a ride-sharing 
        discrete event simulation. There are two types of entities: reservations and 
        drivers. There are six types of events: Reservation, Reservation Assignment, 
        Intersection Arrival, Pick Up, Drop Off, and Idle Arrival. The simulation 
        terminates when either the maximum input time is reached or the goal number 
        of reservations are fulfilled. This class is instantiated by the LynxRideSharing 
        game object. Other information: 20x20 intersections, intersection arrival
        follows a normal distribution, reservations follow an exponential distribution.
        Pickup destinations are random, but dropoff destinations depend on the "time 
        of day" and "type of street", party size of a reservation and driver capacity
        follows a particular distribution, and whether or not a reservations approves
        of a carpool depends on its party size.

        Args:
            time (float): The maximum time at which an event can take place
            num_drivers (int): The number of drivers fulfilling reservations
            num_reservations (int): The goal number of reservations
            carpool_threshold (int): The maximum number of blocks a driver should
                veer off its path given that its fulfulling a reservation and the
                reservations approves of a carpool.
        
        Attributes:
            reservations: list of reservation dictionaries
            drivers: list of driver dictionaries
            future_event_list: priority queue of all events in the simulation
            all_events: list of all events handled in order, used in GUI
            time: time of the simulation (argument)
            num_drivers: number of drivers (argument)
            num_reservations: number of reservations (argument)
            carpool_threshold: carpool threshold when drivers are fulfilling reservations

        """

        self.reservations = []
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

    def initialize_reservations(self):
        """Called in __init__. Every minute a reservation is initialized followed by another
           reservation that follows an exponential distribution."""

        time = 0.0
        while time < self.time:
            # if time % 60.0 == 0.0:
            if len(self.reservations) < self.num_reservations:
                # self.create_reservation(time)
                time += np.random.exponential(scale=30.0)
                self.create_reservation(time)
                # ime += new_time
                # print(time)
            else:
                break
        # self.reservations = self.reservations[:-2]

    def create_reservation(self, time):
        """Creates a reservation given the time. The pickup location is random, 
           but the dropoff location depends on the time of day and street type.
           This follows a particular distribution. The reservation party size
           is also follows a particular distribution.
        
        Args:
            time (float): The time of the reservation

        """

        party_size = np.random.choice(np.arange(1,5), 1, p=[0.6, 0.25, 0.10, 0.05])[0]
        reserve_time = time

        # RESERVATION PARTY SIZE WHICH DETERMINES PROBABILITY OF ACCEPTING CARPOOLS
        if party_size == 1:
            prob = [0.5, 0.5]
        elif party_size == 2:
            prob = [0.35, 0.65]
        elif party_size == 3:
            prob = [0.55, 0.45]
        else:
            prob = [0.70, 0.30]
        carpool = np.random.choice(2, 1, p=prob)[0]

        # STREETS
        gov_streets = [4,8,12,16]
        streets = list(range(20))

        # S1, A1 (PICKUP LOCATION)
        pickup_coords = [np.random.choice(20, 1)[0], np.random.choice(20, 1)[0]]

        # S2, A2 (DROPOFF LOCATION, DEPENDS ON TIME OF DAY AND TYPE OF STREET)
        time_of_day = np.random.choice(2, 1, p=[0.75, 0.25])[0]

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
        """Called in __init__. Initializes and creates the drivers based on random 
           starting location and a capacity that follows a particular distribution.

        Args:
            The number of drivers given as a class parameter

        """

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
        
        # print(self.drivers)

    def initialize_future_event_list(self):
        """Initializes the future event list of inserting all reservations as events. """
        # print(self.reservations)
        for reservation in self.reservations:
            # print(reservation)
            self.future_event_list.put(
                (reservation['reserve_time'],
                {
                    'event_type': 'reservation',
                    'event': {
                        'reservation': reservation
                    }
                }
                )
            )


    def run(self):
        """Pops events from the future event list until it is empty. Inserts events if
           necessary. An events priority is the time of the event. A uniform random
           is added to each new event time in case events have the same priority. This
           makes it much easier than keeping track of a second priority. One an event
           is popped, its event type is checked an action is taken accordingly. """

        while not self.future_event_list.empty():
            shifter = np.random.uniform(0.0, 1.0)
            next_event = self.future_event_list.get()
            self.all_events.append(copy.deepcopy(next_event))
            event_type = next_event[1]['event_type']

            # all reservation, pick up and drop off times should be rounded to the nearest minute
            # interestion arrival and idle arrival times should be rounded to the nearest tenth of a minute
            
            # f.write('{}: {}'.format(next_event[0], pp.pprint(next_event[1])))
            # event = {'event_type': event_type, 'event': next_event[1]['event'], 'time': next_event[0]}
            # f.write(pprint.pformat(event) + '\n\n')

            if event_type == 'reservation':
                # RESERVATION EVENT
                reservation1 = next_event[1]['event']['reservation']
                current_time = next_event[0]
                # ISOLATE AVAILABLE DRIVERS
                available_drivers = [driver for driver in self.drivers if driver['capacity'] - driver['seats_filled'] >= reservation1['party_size']]
                # FIND THE CLOSEST DRIVER TO THE CURRENT RESERVATION
                if len(available_drivers) > 0 and not reservation1['assigned']:
                    passenger_location = reservation1['current_location']
                    min_dist = 1000000
                    closest_available_driver = None
                    for driver in available_drivers:
                        driver_location = driver['current_location']
                        dist = np.linalg.norm(np.array(driver_location) - np.array(passenger_location))
                        if dist < min_dist:
                            min_dist = dist
                            closest_available_driver = driver
                    closest_available_driver['idle'] = False

                    # TRIGGER A 'reservation assignment' EVENT
                    self.future_event_list.put(
                        (
                            current_time + shifter,
                            {
                                'event_type': 'reservation assignment',
                                'event': {
                                    'driver': closest_available_driver,
                                    'reservation': reservation1
                                }
                            }
                        )
                    )
                
                f.write('{}, {}, {}, ResId: {}, Party: {}, Pool: {}\n'.format(
                                              round(current_time), 
                                              event_type,
                                              tuple(reservation1['current_location']),
                                              reservation1['reservation_id'],
                                              reservation1['party_size'],
                                              reservation1['carpool']
                                              ))


            elif event_type == 'reservation assignment':
                # ASSIGN A DRIVER TO THE RESERVATION
                event = next_event[1]['event']
                driver = event['driver']
                reservation2 = event['reservation']
                current_time = next_event[0]

                if not reservation2['assigned']:
                    reservation2 = event['reservation']
                    reservation2['assigned'] = True
                    driver['current_reservations'].append(reservation2)
                    driver['seats_filled'] += reservation2['party_size']
                    reservation2['driver'] = driver

                    # TRIGGER FIRST INTERSECTION ARRIVAL EVENT
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


                    f.write('{}, {}, ResId: {}, DriverId: {}, SeatsFilled: {}/{}\n'.format(
                                                round(current_time),
                                                event_type,
                                                reservation2['reservation_id'],
                                                driver['driver_id'],
                                                driver['seats_filled'],
                                                driver['capacity']))


            elif event_type == 'intersection arrival':
                # ARRIVE AT AN INTERSECTION
                event = next_event[1]['event']
                driver = event['driver']
                current_time = next_event[0]
                reservations = driver['current_reservations']

                # # an optimized version of carpooling that does not yet work: check if there is an unassigned reservation nearby. If so, trigger assignment event
                for res in self.reservations:
                    # check for unassigned reservations
                    if not res['assigned'] and res['carpool']:
                        print('carpool')
                        reservation_location = res['current_location']
                        party_size = res['party_size']
                        driver_location = driver['current_location']
                        capacity = driver['capacity']
                        seats_filled = driver['seats_filled']

                        # check if driver has space
                        if party_size <= capacity - seats_filled and not res['assigned']:
                            # check if reservation is close enough
                            dx = abs(reservation_location[0] - driver_location[0])
                            dy = abs(reservation_location[1] - driver_location[1])
                            if dx <= self.carpool_threshold and dy <= self.carpool_threshold:
                                # print('From intersection arriva: {}'.format(self.assignment_calls_from_intersection_arrival))

                                self.future_event_list.put(
                                    (
                                        current_time + shifter,
                                        {
                                            'event_type': 'reservation assignment',
                                            'event': {
                                                'driver': driver,
                                                'reservation': res
                                            }
                                        }
                                    )
                                )
                                break

                if len(driver['current_reservations']) > 0:
                    # GO TO NEAREST RESERVATION
                    closest_reservation = self.closest_reservation(driver)
                    location_update_time = self.update_locations(driver, closest_reservation, closest_reservation['picked_up'])
                    arrival_time = current_time + location_update_time

                    if location_update_time == -1:
                        # ISSUE PICKUP OR DROPOFF SINCE DRIVER HAS ARRIVED TO RESERVATION OR THE DROPOFF LOCATION
                        if not closest_reservation['picked_up']:
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
                        # IF THE DRIVER HAS NOT ARRIVED AT RESERVATION OR A DROPOFF LOCATION, ISSUE ANOTHER INTERSECTION ARRIVAL EVENT
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

                    print(reservations)
                    res_ids = ','.join([str(res['reservation_id']) for res in reservations])
                    res_locations = ','.join([str(tuple(res['current_location'])) for res in reservations])

                    f.write('{}, {}, DriverId: {}, DriverLoc: {}, ResIds: ({}), AssignedResLocations: ({})\n'.format(
                                            round(current_time, 1),
                                            event_type,
                                            driver['driver_id'],
                                            tuple(driver['current_location']),
                                            res_ids,
                                            res_locations
                                            ))


            elif event_type == 'pick up':
                event = next_event[1]['event']
                driver = event['driver']
                reservation = event['reservation']
                current_time = next_event[0]
                reservation['picked_up'] = True
                reservation['pickup_time'] = current_time

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


                f.write('{}, {}, {}, DriverId: {}, ResId: {}\n'.format(
                                        round(current_time),
                                        event_type,
                                        tuple(driver['current_location']),
                                        driver['driver_id'],
                                        reservation['reservation_id']
                                        ))


            elif event_type == 'drop off':
                event = next_event[1]['event']
                driver = event['driver']
                reservation = event['reservation']
                current_time = next_event[0]
                reservation['dropoff_time'] = current_time
                driver['serviced_passengers'].append(reservation)
                driver['seats_filled'] -= reservation['party_size']

                reservations = driver['current_reservations']
                reservations.remove(reservation)

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

                f.write('{}, {}, {}, DriverId: {}, ResId: {}\n'.format(
                        round(current_time),
                        event_type,
                        tuple(driver['current_location']),
                        driver['driver_id'],
                        reservation['reservation_id']
                        ))

            elif event_type == 'idle_arrival':
                event = next_event[1]['event']
                driver = event['driver']
                current_time = next_event[0]
                driver['idle'] = True

                for res in self.reservations:
                    if not res['assigned']:
                        self.future_event_list.put(
                            (
                                current_time,
                                {
                                    'event_type': 'reservation',
                                    'event': {
                                        'reservation': res
                                    }
                                }
                            )
                        )
                        break
                

                f.write('{}, {}, {}, DriverId: {}\n'.format(round(current_time, 1), event_type, tuple(driver['current_location']), driver['driver_id']))


        f.close()

    @staticmethod
    def update_locations(driver, closest_reservation, picked_up = False):
        """Take driver and passenger to an intersection that is closer to the destination"""

        driver_location = driver['current_location']
        current_reservation = closest_reservation
        current_reservation_location = closest_reservation['current_location']
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

    @staticmethod
    def closest_reservation(driver):
        """FINDS CLOSEST RESERVATION THAT THE DRIVER HAS BEEN ASSIGNED"""
        driver_location = driver['current_location']
        reservations = driver['current_reservations']
        current_reservation = reservations[0]
        current_reservation_location = current_reservation['current_location']
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
    num_drivers = 40
    passengers = 0
    ninety_percent_runs = 0
    N = 100
    percentages = [0]*N

    for i in range(N):
        sim = Simulation(num_reservations=100000, num_drivers=num_drivers, time=7200.0)
        sim.run()
        passengers = 0
        free_ride_passengers = 0
        free_ride_reservations = 0
        # print(sim.reservations)
        for res in sim.reservations:
            passengers += res['party_size']
            if (res['pickup_time'] - res['reserve_time'])/60 > 15.0:
                free_ride_passengers += res['party_size']
                free_ride_reservations += 1
        percentage = 1.0 - free_ride_passengers/passengers
        percentage_res = 1.0 - free_ride_passengers/len(sim.reservations)
        # print('Percentage of passengers that paid for a ride: {}'.format(percentage))
        print(i)
        percentages[i] = percentage
        if percentage >= 0.90:
            ninety_percent_runs += 1

    
    runs = [1]*ninety_percent_runs
    runs.extend([0]*(N - ninety_percent_runs))
    print(runs)
    conf_int = st.t.interval(0.90, N - 1, loc=np.mean(percentages), scale=st.sem(percentages))
    print(conf_int)

    # print('P: {}'.format(ninety_percent_runs/N))
    # print('Number of drivers where the probability of no more than 5% rides being free is at least 90%: {}'.format(num_drivers))