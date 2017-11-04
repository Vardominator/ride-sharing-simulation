import pprint
import numpy as np

class Simulation(object):
    def __init__(self, num_drivers=20):
        self.reservations = []
        self.initialize_reservations()
        self.num_drivers = num_drivers
        self.initialize_drivers(num_drivers)

    def initialize_reservations(self):
        time = 0
        while time < 7200:
            if time % 60 == 0:
                # make 2 reservations per minute
                # first reservation
                self.create_reservation(time)
                
                # second reservation: exponential distribution
                second_time = time + int(np.ceil(np.random.exponential(scale=60.0)))
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

        dropoff_coords = dropoff_coords = (np.random.choice(20, 1)[0], a2[0])
        self.reservations.append({
            'party_size': party_size,
            'reserve_time': time,
            'carpool': carpool,
            'pickup_coords': pickup_coords,
            'dropoff_coords': dropoff_coords
        })

    def initialize_drivers(self, num_drivers):
        pass


if __name__ == "__main__":
    sim = Simulation()
    for res in sim.reservations:
        print(res)