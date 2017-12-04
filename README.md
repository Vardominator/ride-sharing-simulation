# Ride Sharing Simulation

Discrete event simulation of a ride sharing service similar to Uber and Lyft.

## Description

This program populates and maintains a future event list of a ride-sharing 
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

The simulation is ran and all of its events are created. Then a graphical
application shows the results of the simulation with Ferrari's only.

### GUI TODOs
* Track total number of idle drivers
* Track leading driver
* Show party size next to reservation
* Show capacity and passenger count for each driver

### Other TODOs
* Logging
* Finish README: prequisites and installation
* Screenshot/video of application running