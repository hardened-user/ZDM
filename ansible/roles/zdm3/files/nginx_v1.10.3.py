#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 26.08.2019
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: <metric> [<url>] [<ttl>] [redirects]

import os
import re
import time

import requests
from zdmcnf.common import *
from zdmcnf.nginx import *

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
                            metavar="<URL>", help="nginx stub_status url")
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
        args.url = cnf_nginx_stub_status_url
    # ttl
    if not args.ttl:
        args.ttl = cnf_nginx_cache_ttl
    else:
        args.ttl = int(args.ttl)
    # redirects
    if not args.redirects:
        args.redirects = cnf_nginx_allow_redirects
    elif args.redirects.lower() in ("yes", "true"):
        args.redirects = True
    else:
        args.redirects = False
    # __________________________________________________________________________
    if args.metric and args.url and args.ttl:
        key = "{}_{}".format(_MODULE_NAME, args.url)
        fargs = (args.url, cnf_common_timeout, args.redirects)
        fkwargs = {}
        rd = memcached_fnc(get_stub_status, fargs, fkwargs, key, args.ttl, _STARTUP_TS, cnf_common_timeout)
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
def get_stub_status(url: str, timeout: int, allow_redirects: bool) -> (None, str):
    headers = {
        'User-Agent': "Zabbix Data Mining"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=allow_redirects)
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
    if metric == "active":
        re_metric = re.compile(r"Active connections:\s+(\d+)", re.UNICODE | re.IGNORECASE)
    elif metric == "accepts":
        re_metric = re.compile(r"(\d+)\s+\d+\s+\d+", re.UNICODE | re.IGNORECASE)
    elif metric == "handled":
        re_metric = re.compile(r"\d+\s+(\d+)\s+\d+", re.UNICODE | re.IGNORECASE)
    elif metric == "requests":
        re_metric = re.compile(r"\d+\s+\d+\s+(\d+)", re.UNICODE | re.IGNORECASE)
    elif metric == "reading":
        re_metric = re.compile(r"Reading:\s+(\d+)", re.UNICODE | re.IGNORECASE)
    elif metric == "writing":
        re_metric = re.compile(r"Writing:\s+(\d+)", re.UNICODE | re.IGNORECASE)
    elif metric == "waiting":
        re_metric = re.compile(r"Waiting:\s+(\d+)", re.UNICODE | re.IGNORECASE)
    else:
        logging.error("Unsupported metric :: {}".format(metric))
        return None
    # __________________________________________________________________________
    for x in data.splitlines():
        tmp = re_metric.search(x)
        if tmp:
            return tmp.group(1)
    # __________________________________________________________________________
    logging.error("Metric not found :: {}".format(metric))
    return None


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    from zdmlib.log import logging_setup

    log_file_path = os.path.join(cnf_common_log_dir, os.path.basename(sys.argv[0]) + ".log")
    logging_setup(filename=log_file_path, level=cnf_common_log_level)
    # logging_setup(level=logging.DEBUG)  #### TEST
    logging.info(' '.join(sys.argv))
    # __________________________________________________________________________
    sys.exit(not main())  # Compatible return code
