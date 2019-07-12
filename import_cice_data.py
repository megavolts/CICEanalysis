#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
2019-02-04
Paper: property variability in sea ice

Import input and output data from CICE run
"""

import configparser
import os
import pickle

from cice import cice

DEBUG = 1
LOCATION = 'BRW'

if os.uname()[1] == 'adak':
    config_dir = '/home/megavolts/git/CICEanalysis'
else:
    print('No directory defined for this machine')

#config_path = os.path.join(config_dir, 'CICE.ini')
config_path = os.path.join(config_dir, 'CICE-1948-2013.ini')

# -------------------------------------------------------------------------------------------------------------------- #
# LOAD CONFIG
# -------------------------------------------------------------------------------------------------------------------- #
config_file = configparser.ConfigParser()
config_file.read(config_path)

# -------------------------------------------------------------------------------------------------------------------- #
# IMPORTATION
# -------------------------------------------------------------------------------------------------------------------- #
print('Run: %s' % os.path.join(config_file['DEFAULT']['data_dir'], config_file[LOCATION]['subdir']))

# import input
weather_path = os.path.join(config_file['DEFAULT']['data_dir'], config_file[LOCATION]['subdir'],
                            config_file[LOCATION]['input'])
weather_data = cice.import_input(weather_path)

# import output
cice_path = os.path.join(config_file['DEFAULT']['data_dir'], config_file[LOCATION]['subdir'],
                         config_file[LOCATION]['output'])
cice_data = cice.import_output(cice_path, n_layer=20)

# -------------------------------------------------------------------------------------------------------------------- #
# EXPORTATION
# -------------------------------------------------------------------------------------------------------------------- #
cice_pkl = os.path.join(config_file['DEFAULT']['data_dir'], config_file[LOCATION]['subdir'],
                         config_file[LOCATION]['pickle'])

with open(cice_pkl, 'wb') as f:
     pickle.dump([weather_data, cice_data], f)
