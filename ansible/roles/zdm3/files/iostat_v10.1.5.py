#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 23.07.2019
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: discovery
# USAGE: <device> <metric>

import os
import time

from zdmcnf.common import *
from zdmcnf.iostat import *
from zdmlib.common import *
from zdmlib.memcached import memcached_cmd
from zdmlib.shell import shell_exec

_STARTUP_TS = time.time()
_CACHE_TTL = cnf_iostat_cache_ttl
_MODULE_NAME = os.path.basename(sys.argv[0])


def main():
    # __________________________________________________________________________
    # command-line options, arguments
    try:
        parser = MyArgumentParser()
        parser.add_argument("device", action='store', default="",
                            metavar='<DEVICE>|discovery')
        parser.add_argument("metric", action='store', default="", nargs='?',
                            metavar='<METRIC>')
        args = parser.parse_args()
    except SystemExit:
        print_to_zabbix("ZBX_ERROR")
        return False
    # __________________________________________________________________________
    # discovery
    if args.device == "discovery":
        cmd = cnf_iostat_discovery_cmd
        rc, rd = shell_exec(cmd, cnf_common_timeout, 0, True)  # <'list'>
        if rc != 0:
            print_to_zabbix("ZBX_ERROR")
            return False
        if not rd:
            logging.error("Device(s) not found")
            print_to_zabbix("ZBX_ERROR")
            return False
        result = []
        for row in rd:
            row = row.decode('utf-8', 'replace')
            result.append({"{#DEVNAME}": "{}".format(row)})
        print_to_zabbix(result)
        return True
    # __________________________________________________________________________
    elif args.device and args.metric in ("kB_read", "kB_wrtn"):
        key_data = "{}_{}_data".format(_MODULE_NAME, "stat")
        key_lock = "{}_{}_lock".format(_MODULE_NAME, "stat")
        cmd = cnf_iostat_stat_cmd
        rd = memcached_cmd(cmd, key_data, key_lock, _CACHE_TTL, _STARTUP_TS, cnf_common_timeout,
                           rc_expect=0, splitlines=True)  # <'list'>
        if rd is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        result = get_stat_metric(rd, args.device, args.metric)
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        print_to_zabbix(result)
        return True
    # __________________________________________________________________________
    elif args.device and args.metric:
        key_data = "{}_{}_data".format(_MODULE_NAME, "util")
        key_lock = "{}_{}_lock".format(_MODULE_NAME, "util")
        cmd = cnf_iostat_util_cmd
        rd = memcached_cmd(cmd, key_data, key_lock, _CACHE_TTL, _STARTUP_TS, cnf_common_timeout,
                           rc_expect=0, splitlines=True)  # <'list'>
        if rd is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        result = get_util_metric(rd, args.device, args.metric)
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
def get_stat_metric(data, device, metric):
    columns = ["Device", "tps", "kB_read_s", "kB_wrtn_s", "kB_read", "kB_wrtn"]
    if metric not in columns:
        logging.error("Unsupported metric :: {}".format(metric))
        return None
    for row in data:
        row = row.decode('utf-8', 'replace')
        _tmp = row.split()
        if len(_tmp) != len(columns):
            continue
        if _tmp[columns.index("Device")] != device:
            continue
        return _tmp[columns.index(metric)]
    # __________________________________________________________________________
    logging.error("Device not found :: {}".format(device))
    return None


def get_util_metric(data, device, metric):
    columns = ['Device', 'rrqm_s', 'wrqm_s', 'r_s', 'w_s', 'rkB_s', 'wkB_s',
               'avgrq-sz', 'avgqu-sz', 'await', 'r_await', 'w_await', 'svctm', 'util']
    if metric not in columns:
        logging.error("Unsupported metric :: {}".format(metric))
        return None
    # WARNING: Чтение данных в обратном порядке
    for row in reversed(data):
        row = row.decode('utf-8', 'replace')
        _tmp = row.split()
        if len(_tmp) != len(columns):
            continue
        if _tmp[columns.index("Device")] != device:
            continue
        return _tmp[columns.index(metric)]
    # __________________________________________________________________________
    logging.error("Device not found :: {}".format(device))
    return None


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    from zdmlib.log import logging_setup

    log_file_path = os.path.join(cnf_common_log_dir, os.path.basename(sys.argv[0]) + ".log")
    logging_setup(filename=log_file_path, level=cnf_common_log_level)
    # logging_setup(level=logging.DEBUG) #### TEST
    logging.info(' '.join(sys.argv))
    # __________________________________________________________________________
    sys.exit(not main())  # Compatible return code
