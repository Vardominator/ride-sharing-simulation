import cocos
from cocos.director import director
from cocos.actions import *

class HelloWorld(cocos.layer.Layer):
    def __init__(self):
        super(HelloWorld, self).__init__()
        self.shift = 20
        self.num_cars = 5
        self.intersections = []
        self.icoords = []
        self.cars = []
        self.carcoords = []

        self.initialize_map()

    def initialize_map(self):
        # place intersections
        for x in range(0 + self.shift, 1000 + self.shift, 50):
            for y in range(0 + self.shift, 1000 + self.shift, 50):
                isection = cocos.sprite.Sprite('resources/intersection.jpg')
                isection.position = x, y
                self.intersections.append(isection)
                self.icoords.append((x,y))
                self.add(isection)
        
        # place cars
        for x in range(self.num_cars):
            car = cocos.sprite.Sprite('resources/ferrari.png')
            car.position = self.icoords[random.choice(range(len(self.icoords)))]
            self.cars.append(car)
            self.carcoords.append(car.position)
            self.add(car)

    def run_simulation(self):
        pass

    def move_to_intersection(self, sprite, location):
        sprite.do(MoveTo(location, duration=5))



if __name__ == "__main__":
    # initialize and create a window
    director.init(width=1000, height=1000, caption="Lynx - Ferrari's Only", fullscreen=False)

    # create a hello world instance
    lynx_layer = HelloWorld()

    # create a scene that contains the HelloWorld layer
    main_scene = cocos.scene.Scene(lynx_layer)

    # run the scene
    director.run(main_scene)