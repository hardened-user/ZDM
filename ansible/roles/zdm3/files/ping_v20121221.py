#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 14.08.2019
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: <addr> <metric> [<ttl>]

import os
import re
import time

from zdmcnf.common import *
from zdmcnf.ping import *

from zdmlib.common import *
from zdmlib.memcached import memcached_cmd

_STARTUP_TS = time.time()
_MODULE_NAME = os.path.basename(sys.argv[0])


def main():
    # __________________________________________________________________________
    # command-line options, arguments
    try:
        parser = MyArgumentParser()
        parser.add_argument('addr', action='store', nargs='?',
                            metavar="<ADDR>", help="IP or DNS address")
        parser.add_argument('metric', action='store',
                            metavar="<METRIC>", help="requested metric")
        parser.add_argument('ttl', action='store', nargs='?',
                            metavar="<TTL>", help="result cache ttl")
        args = parser.parse_args()
    except SystemExit:
        print_to_zabbix("ZBX_ERROR")
        return False
    # metric
    if args.metric:
        args.metric = args.metric.lower()
    # ttl
    if not args.ttl:
        args.ttl = cnf_ping_cache_ttl
    else:
        args.ttl = int(args.ttl)
    # __________________________________________________________________________
    if args.metric and args.addr and args.ttl:
        key_data = "{}_{}_data".format(_MODULE_NAME, args.addr)
        key_lock = "{}_{}_lock".format(_MODULE_NAME, args.addr)
        try:
            cmd = cnf_ping_cmd.format_map(SafeFormatDict(ADDR=args.addr))
        except Exception as err:
            logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
            print_to_zabbix("ZBX_ERROR")
            return False
        rd = memcached_cmd(cmd, key_data, key_lock, args.ttl, _STARTUP_TS, cnf_common_timeout,
                           rc_expect=0, splitlines=True)  # <'list'>
        if rd is None:
            # NOTE: continue even if there is an error
            rd = ""
        result = get_ping_metric(rd, args.metric)
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
def get_ping_metric(data, metric):
    if metric == "time":
        re_time = re.compile(r"rtt\smin/avg/max/mdev\s=\s([0-9][0-9.]+)/([0-9][0-9.]+)/([0-9][0-9.]+)/([0-9][0-9.]+)",
                             re.UNICODE | re.IGNORECASE)
        for x in data:
            x = x.decode('utf-8', 'replace')
            tmp = re_time.search(x)
            if tmp:
                return tmp.group(2)
        return "0"
    elif metric == "loss":
        re_lost = re.compile(r"\s(\d+)%\spacket loss", re.UNICODE | re.IGNORECASE)
        for x in data:
            x = x.decode('utf-8', 'replace')
            tmp = re_lost.search(x)
            if tmp:
                return tmp.group(1)
        return "100"
    # __________________________________________________________________________
    logging.error("Unsupported metric :: {}".format(metric))
    return None


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    from zdmlib.log import logging_setup

    log_file_path = os.path.join(cnf_common_log_dir, os.path.basename(sys.argv[0]) + ".log")
    logging_setup(filename=log_file_path, level=cnf_common_log_level)
    # logging_setup(level=logging.INFO)  #### TEST
    logging.info(' '.join(sys.argv))
    # __________________________________________________________________________
    sys.exit(not main())  # Compatible return code
