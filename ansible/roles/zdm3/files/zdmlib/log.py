# -*- coding: utf-8 -*-
# 13.05.2019
# ----------------------------------------------------------------------------------------------------------------------
import logging

_FORMAT_DATE = "%Y/%m/%d %H:%M:%S"
_FORMAT_INFO = '%(asctime)s %(process)-5d [%(levelname)s] %(message)s'
_FORMAT_DEBUG = '%(asctime)s %(process)-5d %(module)-18s %(lineno)-3d %(funcName)-20s [%(levelname)s] %(message)s'


def logging_setup(**kwargs):
    if 'level' not in kwargs:
        kwargs['level'] = logging.INFO
    if 'datefmt' not in kwargs:
        kwargs['datefmt'] = _FORMAT_DATE
    if 'format' not in kwargs:
        if kwargs['level'] < logging.INFO:
            kwargs['format'] = _FORMAT_DEBUG
        else:
            kwargs['format'] = _FORMAT_INFO
    # __________________________________________________________________________
    logging.basicConfig(**kwargs)
    logging.addLevelName(logging.DEBUG, 'DEB')
    logging.addLevelName(logging.INFO, 'INF')
    logging.addLevelName(logging.WARNING, 'WAR')
    logging.addLevelName(logging.ERROR, 'ERR')
    logging.addLevelName(logging.CRITICAL, 'CRT')
    # __________________________________________________________________________
    # logging.debug("-> Debug")
    # logging.info("-> Info")
    # logging.warning("-> Warning")
    # logging.error("-> Error")
    # logging.critical("-> Critical")
    # __________________________________________________________________________
    return True
