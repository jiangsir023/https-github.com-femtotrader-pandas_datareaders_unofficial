#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pandas_datareaders_unofficial.datareaders.base import DataReaderBase
from pandas_datareaders_unofficial.tools import COL, _get_dates, to_float, to_int

import pandas as pd
#from pandas.tseries.frequencies import to_offset
from pandas.compat import StringIO
import logging
import traceback

class DataReaderGoogleFinanceIntraday(DataReaderBase):
    """
    DataReader to fetch data from Google Finance Intraday
    """

    def init(self, *args, **kwargs):
        self._get_multi = self._get_multi_topanel

    def _get_one(self, name, *args, **kwargs):
        interval_seconds = kwargs['interval_seconds']

        try:
            num_days = kwargs['num_days']
        except:
            num_days = 1

        period = "%dd" % num_days

        try:
            exchange = kwargs['exchange']
        except:
            exchange = 'ETR'

        return(self._get_one_raw(name, exchange, interval_seconds, period, 'd,c,h,l,o,v'))

    def _get_one_raw(self, query, exchange, interval_seconds, period, format_data, df='', auto='', ei='', ts=''):
        """
        From Google Undocumented Finance API
        http://www.networkerror.org/component/content/article/1-technical-wootness/44-googles-undocumented-finance-api.html
        """

        url = 'https://www.google.com/finance/getprices'
        params = {
            'q': query, # Stock symbol
            'x': exchange, # Stock exchange symbol on which stock is traded (ex: NASD)
            'i': interval_seconds, # Interval size in seconds (86400 = 1 day intervals)
            'p': period, # Period. (A number followed by a "d" or "Y", eg. Days or years. Ex: 40Y = 40 years.)
            'f': format_data, # What data do you want? d (date - timestamp/interval, c - close, v - volume, etc...) Note: Column order may not match what you specify here
            'df': df,
            'auto': auto,
            'ei': ei,
            'ts': ts # Starting timestamp (Unix format). If blank, it uses today.
        }

        #period = to_offset(s_period)
        #period_s = period.delta.total_seconds() # 1H=3600s - number of seconds

        response = self.session.get(url, params=params)
        data = response.text

        df = pd.read_csv(StringIO(data), sep=',', skiprows=7, header=None, names=COL.LST_ALL())
        b_dateround = df[COL.DATE].map(lambda dt: dt[0]=='a')
        ts_dateround = df[b_dateround][COL.DATE].map(lambda dt: int(dt[1:]))
        ts_dateround = ts_dateround.align(df[COL.DATE])[0]
        ts_dateround = ts_dateround.fillna(method='ffill')
        ts_seconds = df[~b_dateround][COL.DATE].astype(int)*interval_seconds
        ts_seconds = ts_seconds.align(df[COL.DATE])[0].fillna(0)
        df[COL.DATE] = ts_dateround + ts_seconds
        df[COL.DATE] = pd.to_datetime(df[COL.DATE]*1000000000)

        df = df.set_index(COL.DATE)

        return(df[COL.LST()])
