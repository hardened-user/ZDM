# -*- coding: utf-8 -*-
# 13.05.2019
# ----------------------------------------------------------------------------------------------------------------------
import argparse
import logging
import sys
import traceback


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
def print_to_zabbix(data):
    if isinstance(data, float):
        data = "{0:.6f}".format(data)
    elif isinstance(data, list):
        try:
            data = [str(x) for x in data]
            data = map(lambda x: x.replace("'", '"'), data)
            data = '''{{"data": [{}]}}'''.format(', '.join(data))
        except Exception as err:
            logging.critical("Unexpected Exception: {}\n{}".format(err, "".join(traceback.format_exc())))
            print("ZBX_ERROR", flush=True)  # !!!
            return False
    # __________________________________________________________________________
    logging.info("Response: '{}'".format(data))
    print(data, flush=True)  # !!!
    # __________________________________________________________________________
    return True
