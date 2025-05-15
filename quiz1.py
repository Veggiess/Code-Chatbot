# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 14:50:42 2023

@author: admin
"""
"""side = int(input("Enter the number of sides: "))
length = int(input("enter the length of the sides: "))"""
import math
side = 4
length = 20
perimeter = side * length
print("The perimeter of this polygon is: " ,perimeter)
apothem = length / (2 * math.tan((180 / side) * math.pi / 180))
print("The apothem of this polygon is: ", round(apothem,2))
area = (side * length * apothem) / 2
print("The area of this polygon is:", round(area,2))