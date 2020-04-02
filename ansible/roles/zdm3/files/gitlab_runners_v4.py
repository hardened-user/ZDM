#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 02.04.2020
# ----------------------------------------------------------------------------------------------------------------------
# https://docs.gitlab.com/ee/api/runners.html
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: discovery <METRIC>
# USAGE: amount <METRIC>
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
        parser.add_argument("metric", action='store', default="",
                            metavar='<METRIC>')
        args = parser.parse_args()
    except SystemExit:
        print_to_zabbix("ZBX_ERROR")
        return False
    # __________________________________________________________________________
    # discovery
    if args.runner == "discovery" and args.metric:
        _tmp = filter(lambda x: 'name' in x, cnf_gitlab_runners_discovery_params)
        _tmp = list(filter(lambda x: x['name'] == args.metric, _tmp))
        if _tmp:
            discovery_params = _tmp[0]
        else:
            logging.error("Unsupported metric :: {}".format(args.metric))
            print_to_zabbix("ZBX_ERROR")
            return False
        #
        rd = gitlab_runners_list(cnf_gitlab_api_url, cnf_gitlab_private_token,
                                 params=discovery_params, timeout=cnf_common_timeout)
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
    # amount
    if args.runner == "amount" and args.metric:
        _tmp = filter(lambda x: 'name' in x, cnf_gitlab_runners_discovery_params)
        _tmp = list(filter(lambda x: x['name'] == args.metric, _tmp))
        if _tmp:
            discovery_params = _tmp[0]
        else:
            logging.error("Unsupported metric :: {}".format(args.metric))
            print_to_zabbix("ZBX_ERROR")
            return False
        #
        rd = gitlab_runners_list(cnf_gitlab_api_url, cnf_gitlab_private_token,
                                 params=discovery_params, timeout=cnf_common_timeout)
        if rd is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        result = len(rd)
        print_to_zabbix(result)
        return True
    # __________________________________________________________________________
    elif args.runner and args.metric:
        key = "{}_get_{}".format(_MODULE_NAME, args.runner)
        fargs = (cnf_gitlab_api_url, cnf_gitlab_private_token, args.runner, cnf_common_timeout)
        fkwargs = {}
        rd = memcached_fnc(gitlab_runners_get, fargs, fkwargs, key, _CACHE_TTL, _STARTUP_TS, cnf_common_timeout)
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
