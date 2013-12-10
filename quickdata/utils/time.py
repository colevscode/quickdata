# division import is for td_seconds. It is required to get 
# floating point division between integers
from __future__ import division

import datetime
import time
import re

## TIMEZONE STUFF -------------------------------------------------------------

class UTCTimezone(datetime.tzinfo):

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)

utc_timezone = UTCTimezone()

# A class capturing the platform's idea of local time.

class LocalTimezone(datetime.tzinfo):

    def __init__(self):
        self._std_offset = datetime.timedelta(seconds = -time.timezone)
        if time.daylight:
            self._dst_offset = datetime.timedelta(seconds = -time.altzone)
        else:
            self._dst_offset = self._std_offset
        self._dst_diff = self._dst_offset - self._std_offset

    def utcoffset(self, dt):
        if self._isdst(dt):
            return self._dst_offset
        else:
            return self._std_offset

    def dst(self, dt):
        if self._isdst(dt):
            return self._dst_diff
        else:
            return datetime.timedelta(0)

    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0

local_timezone = LocalTimezone()


class UTCRequiredException(Exception):
    def __str__(self):
        return "datetime string must be in UTC time. (trailing 'Z' required)"


def parse_iso_datetime(dtstring, tzinfo=local_timezone):
    """ Expects an UTC timezone string in iso format (with a trailing 'Z'). 
        Returns a naive datetime object after first converting to tzinfo. 
        Similar to what you'd get from datetime.now() """
    if dtstring[-1] != 'Z':
        raise UTCRequiredException()
    dt = datetime.datetime(*map(int, re.split('[^\d]',dtstring)[:-1]), 
                           tzinfo=utc_timezone)
    return dt.astimezone(tzinfo).replace(tzinfo=None)


def format_iso_now():
    """ Returns the current time as an UTC timezone string in iso format (with
        trailing 'Z') """
    return datetime.datetime.utcnow().isoformat()+'Z'


def format_iso(dt, default_tzinfo=local_timezone):
    """ Creates an UTC timezone string in iso format from the given datetime
        (with trailing 'Z'). If no tzinfo is set on the passed datetime,
        the default_tzinfo is applied. """
    dt = dt if dt.tzinfo else dt.replace(tzinfo=default_tzinfo)
    return dt.astimezone(utc_timezone).replace(tzinfo=None).isoformat()+'Z'


def format_timesince(when, default_tzinfo=local_timezone):
    when = when if when.tzinfo else when.replace(tzinfo=default_tzinfo)
    delta = datetime.datetime.now(local_timezone)-when
    secs = delta.days*3600*24+delta.seconds
    days = secs // (3600*24)
    hrs = secs // 3600
    mins = secs // 60
    if days:
        since = "%dd"%days
    elif hrs:
        since = "%dh"%hrs
    elif mins:
        since = "%dm"%mins
    else:
        since = "%ds"%secs
    return since


def td_seconds(td):
    '''
    converts a timedelta into seconds
    '''
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


