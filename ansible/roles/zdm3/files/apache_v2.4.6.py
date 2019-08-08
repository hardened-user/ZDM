#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 08.08.2019
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: <metric> [<url>] [<ttl>] [redirects]

import os
import re
import time

import requests
from zdmcnf.common import *
from zdmcnf.apache import *

from zdmlib.common import *
from zdmlib.memcached import memcached_fnc

_STARTUP_TS = time.time()
_MODULE_NAME = os.path.basename(sys.argv[0])


def main():
    # __________________________________________________________________________
    # command-line options, arguments
    try:
        parser = MyArgumentParser()
        parser.add_argument('metric', action='store',
                            metavar="<METRIC>", help="requested metric")
        parser.add_argument('url', action='store', nargs='?',
                            metavar="<URL>", help="apache mod_status url")
        parser.add_argument('ttl', action='store', nargs='?',
                            metavar="<TTL>", help="result cache ttl")
        parser.add_argument('redirects', action='store', nargs='?',
                            metavar="<REDIRECTS>", help="enable/disable redirection")
        args = parser.parse_args()
    except SystemExit:
        print_to_zabbix("ZBX_ERROR")
        return False
    # metric
    if args.metric:
        args.metric = args.metric.lower()
    # url
    if not args.url:
        args.url = cnf_apache_server_status_url
    # ttl
    if not args.ttl:
        args.ttl = cnf_apache_cache_ttl
    else:
        args.ttl = int(args.ttl)
    # redirects
    if not args.redirects:
        args.redirects = cnf_apache_allow_redirects
    elif args.redirects.lower() in ("yes", "true"):
        args.redirects = True
    else:
        args.redirects = False
    # __________________________________________________________________________
    if args.metric and args.url and args.ttl:
        key_data = "{}_{}_data".format(_MODULE_NAME, args.url)
        key_lock = "{}_{}_lock".format(_MODULE_NAME, args.url)
        fargs = (args.url, cnf_common_timeout, args.redirects)
        rd = memcached_fnc(get_mod_status, fargs, key_data, key_lock, args.ttl, _STARTUP_TS, cnf_common_timeout)
        if rd is None or not isinstance(rd, str):
            print_to_zabbix("ZBX_ERROR")
            return False
        result = get_status_metric(rd, args.metric)
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        print_to_zabbix(result)
        return True
    # __________________________________________________________________________
    logging.error("Invalid arguments")
    print_to_zabbix("ZBX_ERROR")
    return False


# ======================================================================================================================
# Functions
# ======================================================================================================================
def get_mod_status(url: str, timeout: int, allow_redirects: bool) -> (None, str):
    headers = {
        'User-Agent': "Zabbix Data Mining"
    }
    params = "auto"
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout, allow_redirects=allow_redirects)
        data = resp.content  # <class 'bytes'>
        data = data.decode('utf-8', 'replace')
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    # __________________________________________________________________________
    if resp.status_code != 200 or not isinstance(data, str):
        logging.critical("HTTP failure response :: {} {}\n{}\n\n{}".format(
            resp.status_code, resp.reason,
            '\n'.join("{}: {}".format(k, v) for k, v in resp.headers.items()),
            "{}\n".format(resp.text) if resp.text else ''))
        return None
    else:
        logging.debug("HTTP received response :: {} {}\n{}\n\n{}".format(
            resp.status_code, resp.reason,
            '\n'.join("{}: {}".format(k, v) for k, v in resp.headers.items()),
            "{}\n".format(resp.text) if resp.text else ''))
    # __________________________________________________________________________
    return data


def get_status_metric(data: str, metric: str) -> (None, str):
    if metric == "accesses":
        re_metric = re.compile(r"Total Accesses:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "kbytes":
        re_metric = re.compile(r"Total kBytes:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "cpuload":
        re_metric = re.compile(r"CPULoad:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "uptime":
        re_metric = re.compile(r"Uptime:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "avgreq":
        re_metric = re.compile(r"ReqPerSec:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "avgreqbytes":
        re_metric = re.compile(r"BytesPerReq:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "avgbytes":
        re_metric = re.compile(r"BytesPerSec:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "busyworkers":
        re_metric = re.compile(r"BusyWorkers:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "idleworkers":
        re_metric = re.compile(r"IdleWorkers:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    elif metric == "totalslots":
        re_metric = re.compile(r"Scoreboard:\s*(\S+)", re.UNICODE | re.IGNORECASE)
    else:
        logging.error("Unsupported metric :: {}".format(metric))
        return None
    # __________________________________________________________________________
    for x in data.splitlines():
        tmp = re_metric.search(x)
        if tmp:
            if metric == "totalslots":
                return len(tmp.group(1))
            else:
                return tmp.group(1)
    # __________________________________________________________________________
    logging.error("Metric not found :: {}".format(metric))
    return None


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    from zdmlib.log import logging_setup

    log_file_path = os.path.join(cnf_common_log_dir, os.path.basename(sys.argv[0]) + ".log")
    logging_setup(filename=log_file_path, level=cnf_common_log_level)
    # logging_setup(level=logging.DEBUG)  # TEST
    logging.info(' '.join(sys.argv))
    # __________________________________________________________________________
    sys.exit(not main())  # Compatible return code
