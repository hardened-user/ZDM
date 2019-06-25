# -*- coding: utf-8 -*-
# 20.06.2019
# ----------------------------------------------------------------------------------------------------------------------
import argparse
import logging
import sys
import traceback

from .conversion import text_to_bool, text_to_timestamp


# ======================================================================================================================
# Classes
# ======================================================================================================================
class MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        logging.error(message)
        sys.exit(2)


# ======================================================================================================================
# Functions
# ======================================================================================================================
def print_to_zabbix(data, t2bool=False, t2timestamp=False):
    resp = data
    _transformed = False
    if isinstance(data, bool):
        resp = int(data)
    elif isinstance(data, float):
        resp = "{0:.6f}".format(data)
    elif isinstance(data, str):
        if t2bool and not _transformed:
            _tmp = text_to_bool(data)
            if isinstance(_tmp, bool):
                resp = int(_tmp)
                _transformed = True
        if t2timestamp and not _transformed:
            _tmp = text_to_timestamp(data, unsigned=True)
            if isinstance(_tmp, int):
                resp = int(_tmp)
                _transformed = True
    elif isinstance(data, list):
        try:
            _tmp = [str(x) for x in data]
            _tmp = map(lambda x: x.replace("'", '"'), _tmp)
            resp = '''{{"data": [{}]}}'''.format(', '.join(_tmp))
        except Exception as err:
            logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
            print("ZBX_ERROR", flush=True)  # !!!
            return False
    # __________________________________________________________________________
    if _transformed:
        logging.info("Response :: {} ({})".format(resp, data))
    else:
        logging.info("Response :: {}".format(resp))
    print(resp, flush=True)  # !!!
    # __________________________________________________________________________
    return True
