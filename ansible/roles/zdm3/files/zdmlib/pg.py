# -*- coding: utf-8 -*-
# 24.09.2019
# ----------------------------------------------------------------------------------------------------------------------
import logging
import traceback

import psycopg2
import psycopg2.extras


# ======================================================================================================================
# Functions
# ======================================================================================================================
def pg_connect(dsn: str):
    """
    Create a new database session and return a new connection object.
    """
    try:
        conn = psycopg2.connect(dsn)
    except (psycopg2.OperationalError, psycopg2.ProgrammingError) as err:
        logging.error("Postgres Exception :: {}".format(err).strip())
        return None
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    # __________________________________________________________________________
    return conn  # <class 'psycopg2.extensions.connection'>


def pg_query(conn, query: str):
    """
    Execute a database operation (query or command).
    """
    cursor = conn.cursor()
    try:
        cursor.execute(query.strip())
    except (psycopg2.DataError, psycopg2.ProgrammingError) as err:
        logging.error("Postgres Exception :: {}".format(err).strip())
        conn.rollback()
        cursor.close()
        return None
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    else:
        conn.commit()
    # __________________________________________________________________________
    return cursor  # <class 'psycopg2.extensions.cursor'>


def pg_prepared(conn, stmt_prepare, stmt_execute, stmt_finally, argslist):
    """
    Execute query in prepared statement loop.

    :param conn:
    :param stmt_prepare:
    :param stmt_execute:
    :param stmt_finally:
    :param argslist: sequence of sequences or dictionaries with the arguments to send to the query.
                     The type and content must be consistent with template.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(stmt_prepare)
        psycopg2.extras.execute_batch(cursor, stmt_execute, argslist)
        if stmt_finally:
            cursor.execute(stmt_finally)
    except (psycopg2.DataError, psycopg2.ProgrammingError) as err:
        logging.error("Postgres Exception :: {}".format(err).strip())
        conn.rollback()
        cursor.close()
        return None
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    else:
        conn.commit()
    # __________________________________________________________________________
    return cursor  # <class 'psycopg2.extensions.cursor'>


def psql(dsn: str, query: str, fetchall=False, headers=False):
    conn = pg_connect(dsn)
    if conn:
        if fetchall:
            cursor = pg_query(conn, query)
            if cursor is not None and cursor.description is not None:
                if headers:
                    columns = tuple(x[0] for x in cursor.description)
                    _tmp = list()
                    _tmp.append(columns)
                    _tmp.extend(cursor.fetchall())
                    return _tmp  # <class 'list'>
                else:
                    return cursor.fetchall()  # <class 'list'>
        else:
            return pg_query(conn, query)  # <class 'psycopg2.extensions.cursor'>
    # __________________________________________________________________________
    return None


def psql_prepared(dsn: str, stmt_prepare, stmt_execute, stmt_finally, argslist, fetchall=False, headers=False):
    conn = pg_connect(dsn)
    if conn:
        if fetchall:
            cursor = pg_prepared(conn, stmt_prepare, stmt_execute, stmt_finally, argslist)
            if cursor is not None and cursor.description is not None:
                if headers:
                    columns = tuple(x[0] for x in cursor.description)
                    _tmp = list()
                    _tmp.append(columns)
                    _tmp.extend(cursor.fetchall())
                    return _tmp  # <class 'list'>
                else:
                    return cursor.fetchall()  # <class 'list'>
        else:
            return pg_prepared(conn, stmt_prepare, stmt_execute, stmt_finally, argslist)
    # __________________________________________________________________________
    return None


# ======================================================================================================================
# Classes
# ======================================================================================================================
class PGDSN(object):
    def __init__(self, **kwargs):
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 5432)
        self.user = kwargs.get('user', 'postgres')
        self.dbname = kwargs.get('dbname', 'postgres')
        self.password = kwargs.get('password', '')

    def __str__(self):
        return "host='{}' port='{}' user='{}' dbname='{}' password='{}'".format(
            self.host, self.port, self.user, self.dbname, self.password)
