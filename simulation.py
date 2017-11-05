import pprint
import numpy as np
from queue import PriorityQueue

class Simulation(object):
    def __init__(self, num_drivers=20):
        self.reservations = []
        self.drivers = []
        self.future_event_list = PriorityQueue()
        self.initialize_reservations()
        self.num_drivers = num_drivers
        self.initialize_drivers(num_drivers)
        self.initialize_future_event_list()

    def initialize_reservations(self):
        time = 0
        while time < 7200:
            if time % 60 == 0:
                # make 2 reservations per minute
                # first reservation
                self.create_reservation(time)
                
                # second reservation: exponential distribution
                second_time = time + int(np.ceil(np.random.exponential(scale=2)))
                self.create_reservation(second_time)

            time += 60
        
        if self.reservations[-1]['reserve_time'] > 7200:
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
        pickup_coords = (np.random.choice(20, 1)[0], np.random.choice(20, 1)[0])
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
            starting_coords = pickup_coords = (np.random.choice(20, 1)[0], np.random.choice(20, 1)[0])
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
                {
                    'event_type': 'reservation',
                    'event': reservation
                }
                )
            )

    def update_driver_location(self, driver, intersection):
        pass

    def run(self):
        while not self.future_event_list.empty():
            next_event = self.future_event_list.get()            
            event_type = next_event[1]['event_type']
            
            if event_type == 'reservation':
                # RESERVATION EVENT
                reservation = next_event[1]['event']
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
                event = next_event[1]['event']
                driver = event['driver']
                reservation = event['reservation']
                driver['current_reservations'].append(reservation)
                print(driver)
            elif event_type == 'intersection arrival':
                pass
            elif event_type == 'pick up':
                pass
            elif event_type == 'drop off':
                pass
            elif event_type == 'idle_arrival':
                pass



if __name__ == "__main__":
    sim = Simulation()
    for res in sim.reservations:
        print(res)


    sim.run()

    # for driver in sim.drivers:
    #     print(driver)
