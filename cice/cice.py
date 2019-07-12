#!/usr/bin/python3.5
# -*- coding: utf-8 -*-
"""
cice.py provides function to handle CICE model input and output.

Require the following python3 library: pandas, numpy
Require the following seaice library: corePanda, available at https://github.com/megavolts/sea_ice.git
"""

import numpy as np
import pandas as pd
import logging

__author__ = "Marc Oggier"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Marc Oggier"
__contact__ = "Marc Oggier"
__email__ = "marc.oggier@gi.alaska.edu"
__status__ = "development"
__date__ = "2014/11/25"


# --------------------------------------------o-------------------------------------------------------------------#
# Import tool
# ---------------------------------------------------------------------------------------------------------------#
def import_input(path, leap=True):
    headers = ['year', 'month', 'day', 'hour', 'cloud', 'Shortwave rad', 'Tair', 'uwind',
               'vwind', 'Specific Humidity', 'precipitation']

    data = pd.read_csv(path, names=headers, delim_whitespace=True)

    # create datetime
    data['hour'] = data['hour'] - 1
    data['datetime'] = pd.to_datetime(data[['year', 'month', 'day', 'hour']])

    return data.reset_index(drop=True)


def import_output(path, n_layer=20):
    headers = ['year', 'month', 'day', 'hi', 'hs'] + ['T_'+str(i) for i in range(0, 20)] + ['S_'+str(i) for i in range(0, 20)]

    data = pd.read_csv(path, names=headers, delim_whitespace=True)

    # create datetime
    data['datetime'] = pd.to_datetime(data[['year', 'month', 'day']])

    # normalise to SI unit
    data['hi'] = data['hi']/100
    data['hs'] = data['hs'] / 100
    return data.reset_index(drop=True)


# ---------------------------------------------------------------------------------------------------------------#
# CICE output tool
# ---------------------------------------------------------------------------------------------------------------#

variable_abv = {'temperature': 'T', 'salinity': 'S'}


def to_leap_year(data, scale_to_thickness = False):
    """
    add interpolated data on February 29 for leap year, if there isn't.

    :param data:

    :return data:

    """

    logger = logging.getLogger(__name__)

    leap_year = [int(y) for y in data.year.unique() if y % 4 == 0 and ((y % 100 != 0) or (y % 400 == 0))]

    data = data.set_index('datetime', drop=True)

    for ly in leap_year:
        index = pd.date_range(str(ly) + '-02-29 00', str(ly) + '-02-29 23', freq='1h')
        ly_data = pd.DataFrame([[np.nan] * len(data.columns)] * len(index), columns=data.columns, index=index)
        if data.index.min() < ly_data.index.min() and ly_data.index.max() < data.index.max():
            data = pd.concat([data, ly_data], sort=False)
    data = data.sort_index()

    # interpolate data over nan
    if scale_to_thickness:
        logger.warning('scale to thickness not implemented')
        # TODO : creat leap year interpolation for output
        # (1) compute hi, Ts, TW
        # (2) scale linear profile Ts, and Tw
        # (3) interpolate linearly
    else:
        data = data.interpolate(method='time')

    # clear nan value
    data = data.reset_index()
    data = data.rename(columns={'index': 'datetime'})
    return data


def extract_core_day(cice_data, days, location=None, run=None, y_ref='top', variables=list(variable_abv.keys())):
    import seaice
    """

    :param cice_data:
    :param days: datetime.datetime or pandas.datetime 
    :param location:
    :param run:
    :return:
    """
    # start logger
    logger = logging.getLogger(__name__)

    # check function parameters
    if not isinstance(days, list):
        days = [days]

    ic_dict = {}
    if days == []:
        return seaice.Core()
    else:
        for day in days:
            if cice_data[cice_data.datetime == day].empty:
                logger.warning('%s Ice thickness is zero. No ice core are extracted' % day)
            else:
                if location is None:
                    name = 'CICE-' + day.strftime('%Y%m%d')
                else:
                    name = 'CICE-' + location + '-' + day.strftime('%Y%m%d')
                coring_day = day
                ice_thickness = cice_data.loc[cice_data.datetime == day, 'hi'].values[0]
                snow_thickness = cice_data.loc[cice_data.datetime == day, 'hs'].values[0]

                if run is not None:
                    comment ='S, T from CICE simulation run ' + run +';'
                else:
                    comment = 'from CICE model simulation;'

                ic = seaice.Core(name, coring_day, location, lat=None, lon=None, ice_thickness=ice_thickness,
                                 snow_depth=snow_thickness, freeboard=np.nan)
                ic.add_comment(comment)

                n_layer = int(cice_data.columns[-1].split('_')[-1])+1  # layer number from 0 to n_layer-1
                y = np.linspace(0, ice_thickness, n_layer+1)
                y_mid = y[:n_layer] + np.diff(y)/2

                profile = pd.DataFrame()
                for var in variables:
                    col = [variable_abv[var] + '_' + str(n) for n in range(0, n_layer)]
                    data = cice_data.loc[cice_data.datetime == day, col].values[0]
                    variable = pd.DataFrame(data.transpose(), columns=[var], index=y_mid)
                    variable['length'] = [ice_thickness]*len(variable.index)
                    variable['variable'] = [var]*len(variable.index)
                    variable['v_ref'] = [y_ref]*len(variable.index)
                    if var not in ['temperature']:
                        variable['y_low'] = y[:n_layer]
                        variable['y_sup'] = y[1:]
                    else:
                        variable['y_low'] = [np.nan]*len(variable.index)
                        variable['y_sup'] = [np.nan]*len(variable.index)
                    variable['y_mid'] = y_mid
                    variable['name'] = [name]*len(variable.index)
                    profile = profile.append(variable, sort=False)
                ic.add_profile(profile)
                ic_dict[name] = ic
        return ic_dict


def extract_freezup_date(cice_data, years=None, hi_freezup=0.05):
    """

    :param input_data:
    :param years:
    :param hi_freezup: minimal ice thickness in m
    :return:
    """
    logger = logging.getLogger(__name__)

    # check function parameters
    if years is None:
        years = cice_data.year.unique().tolist()
    if not isinstance(years, list):
        years = [years]

    birthday = extract_seaice_birthday(cice_data, years=years)

    freezup = {}
    for year in years:
        if year in birthday.keys():
            day_new_ice = birthday[year]
            freezup_days = cice_data.loc[(cice_data.year == year) &
                                         (cice_data['hi'] > hi_freezup) &
                                         (cice_data.datetime > day_new_ice), 'datetime'].values[0]
            freezup[year] = freezup_days
        else:
            logger.warning('No seaice birthday for %s year' % str(year))

    return freezup


def extract_seaice_birthday(cice_data, years=None):
    """
    :param cice_data:
    :param years:
    :return:
    """

    # check function parameters
    if years is None:
        years = cice_data.year.unique().tolist()
    if not isinstance(years, list):
        years = [years]

    d_min = cice_data.groupby(by='year')['hi'].min()

    birthday = {}
    for year in d_min.index:
        if year in years:
            birthday[year] = cice_data.loc[(cice_data.year == year) & (cice_data.hi == d_min[year]), 'datetime'].values[0]

    return birthday
