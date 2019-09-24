# -*- coding: utf-8 -*-
# 20.09.2019
# ----------------------------------------------------------------------------------------------------------------------
import datetime


# ======================================================================================================================
# Functions
# ======================================================================================================================
def text_to_bool(text: str) -> (bool, str):
    text = text.lower()
    if text in ['on', 'online', 'true', 'yes']:
        return True
    elif text in ['off', 'offline', 'false', 'no']:
        return False
    # __________________________________________________________________________
    return text


def text_to_timestamp(text: str, unsigned=False) -> (int, None):
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO8601 (2019-06-20T13:59:45.659Z)
        "%Y-%m-%d %H:%M:%S"
    ]
    for rmt in formats:
        # noinspection PyBroadException
        try:
            ts = datetime.datetime.strptime(text, rmt).timestamp()
            if unsigned:
                ts = int(ts)
            return ts
        except Exception:
            pass
    # __________________________________________________________________________
    return None


def text_to_int(text: str, kind: str) -> (bool, str):
    text = text.lower()
    # TODO
    catalog = {
        'zdx_level': {'ok': 0, 'information': 1, 'warning': 2, 'average': 3, 'high': 4, 'disaster': 5}
    }
    if kind in catalog:
        # TODO
        pass
    elif kind == "all":
        # TODO
        pass
    # __________________________________________________________________________
    return text
