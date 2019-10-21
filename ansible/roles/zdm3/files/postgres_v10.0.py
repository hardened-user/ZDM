#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 21.10.2019
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: ls_clusters
# USAGE: ls_databases
# USAGE: ls_tables
# USAGE: ls_top_tables
# USAGE: <source> [<metric>] [<host>] [<port>] [<base>] [<ttl>]

import os
import random
import re
import time
from functools import reduce

from zdmcnf.common import *
from zdmcnf.postgres import *

from zdmlib.common import *
from zdmlib.memcached import memcached_fnc
from zdmlib.pg import *
from zdmlib.shell import shell_exec

_STARTUP_TS = time.time()
_MODULE_NAME = os.path.basename(sys.argv[0])


def main():
    # __________________________________________________________________________
    # command-line options, arguments
    try:
        parser = MyArgumentParser()
        parser.add_argument('source', action='store',
                            metavar="<SOURCE>", help="metric data source")
        parser.add_argument('metric', action='store', nargs='?',
                            metavar="<METRIC>", help="requested metric")
        parser.add_argument('host', action='store', nargs='?',
                            metavar='<HOST>', help="database server host (default: localhost)")
        parser.add_argument('port', action='store', nargs='?',
                            metavar='<PORT>', help="database server port number (default: 5432)")
        parser.add_argument('base', action='store', nargs='?',
                            metavar='<BASE>', help="name of the database to connect")
        parser.add_argument('ttl', action='store', nargs='?',
                            metavar="<TTL>", help="result cache ttl")
        args = parser.parse_args()
    except SystemExit:
        print_to_zabbix("ZBX_ERROR")
        return False
    # source
    if args.source:
        args.source = args.source.lower()
    # metric
    if args.metric:
        args.metric = args.metric.lower()
    # host
    if not args.host:
        args.host = "localhost"
    # port
    if args.port:
        args.port = int(args.port)
    else:
        args.port = 5432
    # ttl
    if args.ttl:
        args.ttl = int(args.ttl)
    else:
        args.ttl = cnf_postgres_cache_ttl
    # __________________________________________________________________________
    # DSN (Data Source Name) string
    dsn = PGDSN(host=args.host, port=args.port, user=cnf_postgres_dsn_user, dbname=cnf_postgres_dsn_base,
                password=cnf_postgres_dsn_pass)
    # __________________________________________________________________________
    # LLD Rules
    if args.source in ("ls_clusters", "ls_databases", "ls_tables", "ls_top_tables"):
        # clusters
        clusters = get_clusters(cnf_postgres_ls_clusters_cmd)
        if clusters is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        elif not clusters:
            logging.error("Cluster(s) not found")
            print_to_zabbix("ZBX_ERROR")
            return False
        if args.source == "ls_clusters":
            print_to_zabbix(clusters)
            return True
        # databases
        databases = get_databases(dsn, clusters)
        if databases is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        elif not databases:
            logging.error("Database(s) not found")
            print_to_zabbix("ZBX_ERROR")
            return False
        if args.source == "ls_databases":
            print_to_zabbix(databases)
            return True
        # tables
        if args.source in ("ls_tables", "ls_top_tables"):
            if args.source == "ls_tables":
                tables = get_tables(dsn, databases)
            else:
                tables = get_top_tables(dsn, databases)
            if tables is None:
                print_to_zabbix("ZBX_ERROR")
                return False
            elif not tables:
                logging.error("Table(s) not found")
                print_to_zabbix("ZBX_ERROR")
                return False
            print_to_zabbix(tables)
            return True
    # __________________________________________________________________________
    # generic cluster information (common)
    elif args.source == "available":
        # available
        rnd = random.randint(1000, 9999)
        query = """SELECT {};""".format(rnd)
        cursor = psql(str(dsn), query)  # <class 'psycopg2.extensions.cursor'>
        if cursor is None or cursor.description is None or cursor.fetchone()[0] != rnd:
            print_to_zabbix(0)
            return True
        else:
            print_to_zabbix(1)
            return True

    elif args.source == "uptime":
        # uptime
        query = """SELECT EXTRACT(epoch FROM current_timestamp - pg_postmaster_start_time())::INTEGER;"""
        cursor = psql(str(dsn), query)
        if cursor is None or cursor.description is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(cursor.fetchone()[0])
            return True

    elif args.source == "version":
        # version
        query = """SELECT version();"""
        cursor = psql(str(dsn), query)
        if cursor is None or cursor.description is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(cursor.fetchone()[0])
            return True

    elif args.source == "show" and args.metric and re.compile(r"^([\w\-]+)$", re.UNICODE).search(args.metric):
        # show
        query = """SHOW "{}";""".format(args.metric)
        cursor = psql(str(dsn), query)
        if cursor is None or cursor.description is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(cursor.fetchone()[0], t2bool=True)
            return True

    elif args.source == "pg_stat_activity":
        # pg_stat_activity
        key = "{}_{}_{}_{}".format(_MODULE_NAME, args.host, args.port, args.source)
        query = """SELECT pid, state FROM pg_stat_activity;"""
        fargs = (str(dsn), query,)
        fkwargs = {'fetchall': True, 'headers': True}
        rd = memcached_fnc(psql, fargs, fkwargs, key, args.ttl, _STARTUP_TS, cnf_common_timeout)  # <'list'>
        if rd is None or not isinstance(rd, list):
            print_to_zabbix("ZBX_ERROR")
            return False
        if args.metric:
            result = parse_entitled_table(rd, "pid", "state", args.metric)  # <'list'>
        else:
            result = parse_entitled_table(rd, "pid")  # <'list'>
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(len(result))
            return True

    elif args.source == "pg_stat_database" and args.metric and not args.base:
        # pg_stat_database (summary)
        key = "{}_{}_{}_{}".format(_MODULE_NAME, args.host, args.port, args.source)
        query = """SELECT * FROM pg_stat_database;"""
        fargs = (str(dsn), query,)
        fkwargs = {'fetchall': True, 'headers': True}
        rd = memcached_fnc(psql, fargs, fkwargs, key, args.ttl, _STARTUP_TS, cnf_common_timeout)  # <'list'>
        if rd is None or not isinstance(rd, list):
            print_to_zabbix("ZBX_ERROR")
            return False
        result = parse_entitled_table(rd, args.metric)  # <'list'>
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(reduce(lambda x, y: x + y, result, 0))
            return True

    elif args.source == "pg_stat_bgwriter" and args.metric:
        # pg_stat_bgwriter
        key = "{}_{}_{}_{}".format(_MODULE_NAME, args.host, args.port, args.source)
        query = """SELECT * FROM pg_stat_bgwriter;"""
        fargs = (str(dsn), query,)
        fkwargs = {'fetchall': True, 'headers': True}
        rd = memcached_fnc(psql, fargs, fkwargs, key, args.ttl, _STARTUP_TS, cnf_common_timeout)  # <'list'>
        if rd is None or not isinstance(rd, list):
            print_to_zabbix("ZBX_ERROR")
            return False
        result = parse_entitled_table(rd, args.metric)  # <'list'>
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(result[0])
            return True

    # __________________________________________________________________________
    # generic cluster information (master)
    elif args.source == "replication_clients":
        # replication_clients
        key = "{}_{}_{}_{}".format(_MODULE_NAME, args.host, args.port, args.source)
        query = """SELECT * FROM pg_stat_replication;"""
        fargs = (str(dsn), query,)
        fkwargs = {'fetchall': True, 'headers': True}
        rd = memcached_fnc(psql, fargs, fkwargs, key, args.ttl, _STARTUP_TS, cnf_common_timeout)  # <'list'>
        if rd is None or not isinstance(rd, list):
            print_to_zabbix("ZBX_ERROR")
            return False
        if args.metric:
            result = parse_entitled_table(rd, "pid", "state", args.metric)  # <'list'>
        else:
            result = parse_entitled_table(rd, "pid")  # <'list'>
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(len(result))
            return True
    # __________________________________________________________________________
    # generic cluster information (slave)
    elif args.source == "replication_lag":
        # replication_lag
        query = """SELECT CASE WHEN pg_is_in_recovery() = 'f' THEN -1 ELSE EXTRACT(EPOCH FROM(NOW() - pg_last_xact_replay_timestamp()))::INTEGER END;"""
        cursor = psql(str(dsn), query)
        if cursor is None or cursor.description is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(cursor.fetchone()[0])
            return True
    # __________________________________________________________________________
    # generic database information
    elif args.source in ("pg_database_size", "pg_tablespace_size") and args.metric:
        # pg_database_size, pg_tablespace_size
        stmt_prepare = """PREPARE stmt (VARCHAR) AS SELECT {}($1);""".format(args.source)
        stmt_execute = """EXECUTE stmt (%s);"""
        cursor = psql_prepared(str(dsn), stmt_prepare, stmt_execute, "", [(args.metric,)])
        if cursor is None or cursor.description is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(cursor.fetchone()[0])
            return True

    elif args.source in ("pg_total_relation_size", "pg_relation_size", "pg_indexes_size") and args.metric and args.base:
        # pg_total_relation_size, pg_relation_size, pg_indexes_size
        stmt_prepare = """PREPARE stmt (VARCHAR) AS SELECT {}($1);""".format(args.source)
        stmt_execute = """EXECUTE stmt (%s);"""
        dsn.dbname = args.base
        cursor = psql_prepared(str(dsn), stmt_prepare, stmt_execute, "", [(args.metric,)])
        if cursor is None or cursor.description is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(cursor.fetchone()[0])
            return True

    elif args.source == "pg_stat_database" and args.metric and args.base:
        # pg_stat_database
        key = "{}_{}_{}_{}".format(_MODULE_NAME, args.host, args.port, args.source)
        query = """SELECT * FROM pg_stat_database;"""
        fargs = (str(dsn), query,)
        fkwargs = {'fetchall': True, 'headers': True}
        rd = memcached_fnc(psql, fargs, fkwargs, key, args.ttl, _STARTUP_TS, cnf_common_timeout)  # <'list'>
        if rd is None or not isinstance(rd, list):
            print_to_zabbix("ZBX_ERROR")
            return False
        result = parse_entitled_table(rd, args.metric, "datname", args.base)  # <'list'>
        if result is None:
            print_to_zabbix("ZBX_ERROR")
            return False
        else:
            print_to_zabbix(reduce(lambda x, y: x + y, result, 0))
            return True
    # __________________________________________________________________________
    logging.error("Invalid arguments")
    print_to_zabbix("ZBX_ERROR")
    return False


# ======================================================================================================================
# Functions
# ======================================================================================================================
def get_clusters(cmd):
    rc, rd = shell_exec(cmd, timeout=cnf_common_timeout, rc_expect=0, splitlines=True)  # <'list'>
    if rc != 0:
        return None
    re_cluster = re.compile(r"^(\S+) (\S+) (\d+)$")
    result = []
    for row in rd:
        row = row.decode('utf-8', 'replace')
        _tmp = re_cluster.search(row)
        if _tmp:
            cl_name = _tmp.group(1)
            cl_host = _tmp.group(2)
            cl_port = int(_tmp.group(3))
            result.append({'{#CLNAME}': cl_name, '{#CLHOST}': cl_host, '{#CLPORT}': cl_port})
    # __________________________________________________________________________
    return result


def get_databases(dsn: PGDSN, clusters):
    result = []
    query = """SELECT datname FROM pg_database WHERE datistemplate = 'f' AND datname <> 'postgres';"""
    for x in clusters:
        cl_host = x['{#CLHOST}']
        cl_port = x['{#CLPORT}']
        dsn.host = cl_host
        dsn.port = cl_port
        cursor = psql(str(dsn), query)  # <class 'psycopg2.extensions.cursor'>
        if cursor is None or cursor.description is None:
            return None
        for row in cursor.fetchall():
            # <class 'tuple'>
            _tmp = {'{#DBNAME}': row[0]}
            _tmp.update(x)
            result.append(_tmp)
    # __________________________________________________________________________
    return result


def get_tables(dsn: PGDSN, databases):
    result = []
    query = """SELECT nspname || '.' || relname AS "relation"
    FROM
        pg_class as C
    LEFT JOIN
        pg_namespace as N ON ( N.oid = C.relnamespace )
    WHERE
        nspname NOT IN ( 'pg_catalog', 'information_schema' )
    AND
        C.relkind ='r'
    ORDER BY
        relation ASC"""
    for x in databases:
        cl_host = x['{#CLHOST}']
        cl_port = x['{#CLPORT}']
        db_name = x['{#DBNAME}']
        dsn.host = cl_host
        dsn.port = cl_port
        dsn.dbname = db_name
        cursor = psql(str(dsn), query)  # <class 'psycopg2.extensions.cursor'>
        if cursor is None or cursor.description is None:
            return None
        for row in cursor.fetchall():
            # <class 'tuple'>
            _tmp = {'{#TBNAME}': row[0]}
            _tmp.update(x)
            result.append(_tmp)
    # ______________________________________________________
    return result


def get_top_tables(dsn: PGDSN, databases):
    result = []
    query = """SELECT nspname || '.' || relname AS "relation"
    FROM
        pg_class as C
    LEFT JOIN
        pg_namespace as N ON ( N.oid = C.relnamespace )
    WHERE
        nspname NOT IN ( 'pg_catalog', 'information_schema' )
    AND
        C.relkind ='r'
    ORDER BY
        pg_total_relation_size(C.oid) DESC
    LIMIT {};""".format(cnf_postgres_ls_top_tables_limit)
    for x in databases:
        cl_host = x['{#CLHOST}']
        cl_port = x['{#CLPORT}']
        db_name = x['{#DBNAME}']
        dsn.host = cl_host
        dsn.port = cl_port
        dsn.dbname = db_name
        cursor = psql(str(dsn), query)  # <class 'psycopg2.extensions.cursor'>
        if cursor is None or cursor.description is None:
            return None
        for row in cursor.fetchall():
            # <class 'tuple'>
            _tmp = {'{#TBNAME}': row[0]}
            _tmp.update(x)
            result.append(_tmp)
    # ______________________________________________________
    return result


def parse_entitled_table(table, metric_column_name, filter_column_name=None, filter_column_value=None):
    """
    :param table: [('', '', ...), (), ...]
    :param metric_column_name: имя столбца откуда брать данные
    :param filter_column_name: имя стоблца по которому произвести фильтрацию, используется вместе с filter_column_value
    :param filter_column_value: параметры фильра, точное совпадение, используется вместе с filter_column_name
    """
    result = []
    if len(table) > 1:
        columns = list(table[0])  # <class 'tuple'> -> <class 'list'>
        if metric_column_name not in columns:
            logging.error("Column not found :: {}".format(metric_column_name))
            return None
        metric_column_index = columns.index(metric_column_name)
        if filter_column_name and filter_column_value:
            if filter_column_name not in columns:
                logging.error("Column not found :: {}".format(filter_column_name))
                return None
            filter_column_index = columns.index(filter_column_name)
        else:
            filter_column_index = None
        # ______________________________________________________________________
        for row in table[1:]:
            if filter_column_name and filter_column_value:
                # NOTE: Special characters are not allowed in the parameters.
                #       \, ', ", `, *, ?, [, ], {, }, ~, $, !, &, ;, (, ), <, >, |, #, @, 0x0a
                if re.sub('[()<>]', '', str(row[filter_column_index])) == filter_column_value:
                    result.append(row[metric_column_index])
            else:
                result.append(row[metric_column_index])
    else:
        logging.warning("Parsing table is empty")
    # __________________________________________________________________________
    return result


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    from zdmlib.log import logging_setup

    log_file_path = os.path.join(cnf_common_log_dir, os.path.basename(sys.argv[0]) + ".log")
    logging_setup(filename=log_file_path, level=cnf_common_log_level)
    # logging_setup(level=logging.DEBUG)  #### TEST
    logging.info(' '.join(sys.argv))
    # __________________________________________________________________________
    sys.exit(not main())  # Compatible return code
