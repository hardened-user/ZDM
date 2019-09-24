# -*- coding: utf-8 -*-
# 23.07.2019
# ----------------------------------------------------------------------------------------------------------------------
import hashlib
import os
import time
import traceback
from time import sleep

import memcache
from zdmcnf.common import *

from .shell import shell_exec


# ======================================================================================================================
# Functions
# ======================================================================================================================
def memcached_communicate(action, key, ttl=None, data=None):
    key = hashlib.md5("ZDM3-{}".format(key).encode('utf-8')).hexdigest()
    try:
        mc = memcache.Client([cnf_memcached_addr], socket_timeout=3, debug=0)
        if action == "get":
            # GET
            return_value = mc.get(key)
        elif action == "set":
            # SET
            return_value = mc.set(key, data, time=ttl)  # True/False
        elif action == "lock":
            # LOCK
            return_value = mc.add(key, data, time=ttl)  # True/False/None
            if return_value is False:
                # Блокировка уже установлена, получить данные блокирующей записи
                _tmp = mc.get(key)
                if _tmp is None:
                    return_value = "None"
                else:
                    return_value = _tmp
        elif action == 'unlock':
            # UNLOCK
            return_value = mc.delete(key)
        else:
            logging.error("Unsupported action :: {}".format(action))
            return None
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    # __________________________________________________________________________
    # noinspection PyProtectedMember
    if mc.servers[0]._check_dead():
        logging.error("Memcached is dead")
        return None
    # __________________________________________________________________________
    return return_value


def memcached_cmd(cmd, key_data, key_lock, ttl, timestamp, timeout, rc_expect=None, splitlines=False):
    """
    Выполняет shell команду и заносит STDOUT в memcached в случае успешного выполнения.
    Если результат выполнения команды есть в кеше, то команда не выполняется, а STDOUT отдается из кеша.
    """
    _pid_lock = -1
    while True:
        # ______________________________________________________________________
        # Проверка данных в кеше
        rd = memcached_communicate('get', key_data)
        if rd is not None:
            logging.debug(u"Cache hit :: key: {}".format(key_data))
            return rd
        logging.debug(u"Cache miss :: key: {}".format(key_data))
        # ______________________________________________________________________
        # Заблокируем работу других запросов на время обновления
        pid_lock = memcached_communicate('lock', key_lock, timeout + 1, os.getpid())  # None/True/<'int'>/<'str'>
        if pid_lock is None:
            # Ошибка
            logging.error("Cache lock failed")
            return None
        elif pid_lock is True:
            # Продолжить
            logging.debug("Cache locked")
            break
        else:
            # Ожидать
            if _pid_lock != pid_lock:
                # NOTE: Антиспам. Повторить вывод, только если меняется блокирующий PID
                _pid_lock = pid_lock
                logging.debug(u"Cache waiting unlock :: pid: {}".format(pid_lock))
            if time.time() - timestamp >= timeout:
                logging.error(u"Cache waiting timeout  :: pid: {}".format(pid_lock))
                return None
            else:
                sleep(0.25)
    # __________________________________________________________________________
    # Получить свежие данные
    rc, rd = shell_exec(cmd, timeout, rc_expect, splitlines)
    if (isinstance(rc_expect, int) and rc != rc_expect) or \
            (isinstance(rc_expect, (list, tuple)) and rc not in rc_expect):
        # Error
        rd = None
        pass
    else:
        # Success
        # NOTE: Пересчитываем TTL с учетом времени на выполнение команды
        ttl = timestamp + ttl - time.time()
        if ttl > 1:
            _tmp = memcached_communicate('set', key_data, ttl, rd)  # None/True/False
            if _tmp is None or _tmp is False:
                logging.error("Cache set failed")
            else:
                logging.debug("Cached set successful")
        else:
            logging.error("The cache has expired before it was written")
    # __________________________________________________________________________
    # Разблокировать
    if memcached_communicate('unlock', key_lock):
        logging.debug("Cached unlocked")
    else:
        logging.error("Cached unlock failed")
    # __________________________________________________________________________
    return rd


def memcached_fnc(fnc, fargs, fkwargs, key, ttl, timestamp, timeout):
    """
    Выполняет функцию и заносит результат в memcached в случае успешного выполнения (not None).
    Если результат есть в кеше, то функция не выполняется, а данные отдаются из кеша.
    """
    key_data = key + "_data"
    key_lock = key + "_lock"
    _pid_lock = -1
    while True:
        # ______________________________________________________________________
        # Проверка данных в кеше
        rd = memcached_communicate('get', key_data)
        if rd is not None:
            logging.debug(u"Cache hit :: key: {}".format(key_data))
            return rd
        logging.debug(u"Cache miss :: key: {}".format(key_data))
        # ______________________________________________________________________
        # Заблокируем работу других запросов на время обновления
        pid_lock = memcached_communicate('lock', key_lock, timeout + 1, os.getpid())  # None/True/<'int'>/<'str'>
        if pid_lock is None:
            # Ошибка
            logging.error("Cache lock failed")
            return None
        elif pid_lock is True:
            # Продолжить
            logging.debug("Cache locked")
            break
        else:
            # Ожидать
            if _pid_lock != pid_lock:
                # NOTE: Антиспам. Повторить вывод, только если меняется блокирующий PID
                _pid_lock = pid_lock
                logging.debug(u"Cache waiting unlock :: pid: {}".format(pid_lock))
            if time.time() - timestamp >= timeout:
                logging.error(u"Cache waiting timeout  :: pid: {}".format(pid_lock))
                return None
            else:
                sleep(0.25)
    # __________________________________________________________________________
    # Получить свежие данные
    rd = fnc(*fargs, **fkwargs)
    if rd is None:
        # Error
        pass
    else:
        # Success
        # NOTE: Пересчитываем TTL с учетом времени на выполнение команды
        ttl = timestamp + ttl - time.time()
        if ttl > 1:
            _tmp = memcached_communicate('set', key_data, ttl, rd)  # None/True/False
            if _tmp is None or _tmp is False:
                logging.error("Cache set failed")
            else:
                logging.debug("Cached set successful")
        else:
            logging.error("The cache has expired before it was written")
    # __________________________________________________________________________
    # Разблокировать
    if memcached_communicate('unlock', key_lock):
        logging.debug("Cached unlocked")
    else:
        logging.error("Cached unlock failed")
    # __________________________________________________________________________
    return rd
