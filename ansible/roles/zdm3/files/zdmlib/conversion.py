# -*- coding: utf-8 -*-
# 20.06.2019
# ----------------------------------------------------------------------------------------------------------------------
import datetime


# ======================================================================================================================
# Functions
# ======================================================================================================================
def text_to_bool(text: str) -> (bool, str):
    text = text.lower()
    if text in ['on', 'online', 'true']:
        return True
    elif text in ['off', 'offline', 'false']:
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
