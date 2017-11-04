from cocos.actions import *

class Sprite(object):
    def __init__(self, cocos_sprite):
        self.cocos_sprite = cocos_sprite
    def set_location(self, location):
        self.cocos_sprite.do()
        raise NotImplementedError
    def move_to(self, location):
        raise NotImplementedError

class Driver(Sprite):
    def __init__(self):
        pass

class Passenger(Sprite):
    def __init__(self):
        pass