from math import pi
 
class Sphere:
    def __init__(self, *arg):
        if len(arg) == 0:
            arg = (1, 0, 0, 0)
        elif len(arg) == 1:
            arg = (arg[0], 0, 0, 0)
        else:
            raise TypeError # raise TypeError("<Последняя строчка лога об ошибке>")
        self.r, self.x, self.y, self.z = arg
 
    def get_volume(self):
        return (self.r ** 3) * pi * 4 / 3
 
    def get_square(self):
        return (self.r ** 2) * pi * 4
 
    def get_radius(self):
        return self.r
 
    def get_center(self):
        return (self.x, self.y, self.z)
 
    def set_radius(self, r):
        self.r = r
 
    def set_center(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
 
    def is_point_inside(self, x, y, z):
        return (self.x-x)**2 + (self.y-y)**2 + (self.z-z)**2 < self.r**2
