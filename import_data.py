#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
2019-02-04
Paper: property variability in sea ice

Import input and output data from CICE run
"""

import configparser
import os
import cice
import pandas as pd
import numpy as np
import pickle


DEBUG = 1
LOCATION = 'BRW'

if os.uname()[1] == 'adak':
    config = '/home/megavolts/git/CICEanalysis/cice.conf'
else:
    print('No directory defined for this machine')

# -------------------------------------------------------------------------------------------------------------------- #
# LOAD CONFIG
# -------------------------------------------------------------------------------------------------------------------- #
config_file = configparser.ConfigParser()
config_file.read(config)

# -------------------------------------------------------------------------------------------------------------------- #
# IMPORTATION
# -------------------------------------------------------------------------------------------------------------------- #
print('Run: %s' % config_file[LOCATION]['subdir'].split('/')[-1])

# import input
weather_path = os.path.join(config_file['CICE']['dir'],
                            config_file[LOCATION]['subdir'],
                            config_file[LOCATION]['input'])
weather_data = cice.import_input(weather_path)

# import output
cice_path = os.path.join(config_file['CICE']['dir'],
                            config_file[LOCATION]['subdir'],
                            config_file[LOCATION]['output'])
cice_data = cice.import_output(cice_path, n_layer=20)

# -------------------------------------------------------------------------------------------------------------------- #
# EXPORTATION
# -------------------------------------------------------------------------------------------------------------------- #
cice_pkl = os.path.join(config_file['CICE']['dir'],
                            config_file[LOCATION]['subdir'],
                            config_file[LOCATION]['pickle'])
with open(cice_pkl, 'wb') as f:
     pickle.dump([weather_data, cice_data], f)
