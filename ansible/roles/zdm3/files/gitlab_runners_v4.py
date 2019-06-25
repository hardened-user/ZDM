#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 21.06.2019
# ----------------------------------------------------------------------------------------------------------------------
# https://docs.gitlab.com/ee/api/runners.html
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: discovery
# USAGE: <RUNNER> <METRIC>

import os
import time

from zdmcnf.common import *
from zdmcnf.gitlab import *

from zdmlib.common import *
from zdmlib.gitlab_v4 import *
from zdmlib.memcached import memcached_fnc

_STARTUP_TS = time.time()
_CACHE_TTL = cnf_gitlab_cache_ttl
_MODULE_NAME = os.path.basename(sys.argv[0])


def main():
    # __________________________________________________________________________
    # command-line options, arguments
    try:
        parser = MyArgumentParser()
        parser.add_argument("runner", action='store', default="",
                            metavar='<RUNNER>|discovery')
        parser.add_argument("metric", action='store', default="", nargs='?',
                            metavar='<METRIC>')
        args = parser.parse_args()
    except SystemExit:
        print_to_zabbix("ZBX_ERROR")
        return False
    # __________________________________________________________________________
    # discovery
    if args.runner == "discovery":
        rd = gitlab_runners_list(cnf_gitlab_api_url, cnf_gitlab_private_token,
                                 params=cnf_gitlab_runners_discovery_params, timeout=cnf_common_timeout)
        if rd is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        if not rd:
            logging.error("Runners not found")
            print_to_zabbix("ZBX_ERROR")
            return False
        result = []
        for x in rd:
            result.append({
                "{#RUNNER_ID}": "{}".format(x['id']),
                "{#RUNNER_DESCRIPTION}": "{}".format(x['description'])
            })
        print_to_zabbix(result)
        return True
    # __________________________________________________________________________
    elif args.runner and args.metric:
        key_data = "{}_get_{}_data".format(_MODULE_NAME, args.runner)
        key_lock = "{}_get_{}_lock".format(_MODULE_NAME, args.runner)
        fargs = (cnf_gitlab_api_url, cnf_gitlab_private_token, args.runner, cnf_common_timeout)
        rd = memcached_fnc(gitlab_runners_get, fargs, key_data, key_lock, _STARTUP_TS, _CACHE_TTL, cnf_common_timeout)
        if rd is None or not isinstance(rd, dict):
            print_to_zabbix("ZBX_ERROR")
            return False
        result = get_runner_metric(rd, args.metric)
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        print_to_zabbix(result, t2bool=True, t2timestamp=True)
        return True
    # __________________________________________________________________________
    logging.error("Invalid arguments")
    print_to_zabbix("ZBX_ERROR")
    return False


# ======================================================================================================================
# Functions
# ======================================================================================================================
def get_runner_metric(runner: dict, metric: str):
    if metric not in runner:
        logging.error("Unsupported metric :: {}".format(metric))
        return None
    # __________________________________________________________________________
    return runner[metric]


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    from zdmlib.log import logging_setup

    log_file_path = os.path.join(cnf_common_log_dir, os.path.basename(sys.argv[0]) + ".log")
    logging_setup(filename=log_file_path, level=cnf_common_log_level)
    # logging_setup(level=logging.DEBUG)  #### TEST
    logging.info(' '.join(sys.argv))
    # __________________________________________________________________________
    sys.exit(not main())  # Compatible return code
