# -*- coding: utf-8 -*-
# 18.06.2019
# ----------------------------------------------------------------------------------------------------------------------
import logging
import os
import traceback


# ======================================================================================================================
# Functions
# ======================================================================================================================
def ps_check_pid(pid):
    """
    Check for the existence of a unix pid.
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def ps_kill(pid, signal=9):
    logging.debug("Kill :: pid: {}, signal: {}".format(pid, signal))
    try:
        os.kill(pid, signal)
    except OSError:
        return False
    else:
        return True


def ps_get_pids():
    """
    Returns a list of PIDs currently running on the system.
    """
    try:
        pids = [int(x) for x in os.listdir('/proc') if x.isdigit()]
        return sorted(pids)
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None


def ps_get_ppid(pid):
    try:
        with open("/proc/{}/status".format(pid)) as f:
            for line in f:
                if line.startswith("PPid:"):
                    return int(line.split()[1])
        return None
    except IOError as err:
        logging.error("IOError Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None


def ps_get_children(pid, recursive=False, _pids=None):
    if _pids is None:
        _pids = [(p, ps_get_ppid(p)) for p in ps_get_pids()]
    children = filter(lambda x: pid == x[1], _pids)  # Только прямые потомки
    tree = dict(list(map(lambda x: (x[0], []), children)))
    if recursive:
        for child in tree:
            tree[child] = ps_get_children(child, recursive=True, _pids=_pids)
    # __________________________________________________________________________
    return tree
