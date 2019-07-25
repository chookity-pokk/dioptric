# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 15:31:01 2019

@author: Aedan
"""

import csv
import matplotlib.pyplot as plt
time = []
voltage = []

with open('F:\T0000CH4.csv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
#    line_count = 0
    
    for row in csv_reader:
#        print(row)
        time.append(row[0])
        voltage.append(row[1])
#        print(row[0])
        
#        line_count += 1
    
    
fig, ax= plt.subplots(1, 1, figsize=(10, 8))
fig.set_tight_layout(True)
ax.plot(time, voltage)
ax.set_xlabel('Time')
ax.set_ylabel('Voltage (V)')