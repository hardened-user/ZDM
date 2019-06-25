# -*- coding: utf-8 -*-
# 18.06.2019
# ----------------------------------------------------------------------------------------------------------------------
import logging
import subprocess
from threading import Timer

from .ps import ps_get_children, ps_kill


# ======================================================================================================================
# Functions
# ======================================================================================================================
def shell_exec(cmd, timeout=None, rc_expect=None, splitlines=False):
    if not cmd:
        logging.error("Empty shell command")
        return 1, None
    # __________________________________________________________________________
    trg_timeout = {'value': False}
    _cmd = '''export LC_ALL="C"; export LANG="en_US.UTF-8"; {}'''.format(cmd)
    logging.debug("Shell command running :: ...")
    child = subprocess.Popen(_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, executable='/bin/bash')
    # __________________________________________________________________________
    if timeout:
        def killer(subproc, trigger, _tree=None):
            # NOTE: Оболочка bash ждет завершения процессов, сперва надо убить потомков.
            if _tree is None:
                trigger['value'] = True
                _tree = ps_get_children(subproc.pid, recursive=True)
            if subproc.returncode is not None:
                return
            for pid in _tree:
                # WARNING: Защита от убийства процессов с pid <= 255.
                if pid <= 255:
                    return
                if _tree[pid]:
                    killer(subproc, trigger, _tree[pid])
                if subproc.returncode is not None:
                    return
                ps_kill(pid)
            return

        timer = Timer(timeout, killer, [child, trg_timeout])
        timer.start()
        stdout = child.communicate()[0]
        rc = child.returncode
        timer.cancel()
        del timer
    else:
        stdout = child.communicate()[0]
        rc = child.returncode
    # __________________________________________________________________________
    if trg_timeout['value']:
        logging.error("Shell command timeout :: exit_code: {0}\n{1}\n{2}\n{3}\n{2}".format(
            rc, cmd, "  -" * 33, stdout.decode('utf-8')))
    elif (isinstance(rc_expect, int) and rc != rc_expect) or \
            (isinstance(rc_expect, (list, tuple)) and rc not in rc_expect):
        logging.error("Shell command executed :: exit_code: {0}\n{1}\n{2}\n{3}\n{2}".format(
            rc, cmd, "  -" * 33, stdout.decode('utf-8')))
    else:
        logging.debug("Shell command executed :: exit_code: {0}\n{1}\n{2}\n{3}\n{2}".format(
            rc, cmd, "  -" * 33, stdout.decode('utf-8')))
    # __________________________________________________________________________
    if splitlines:
        return rc, list(filter(lambda x: x, [x.strip() for x in stdout.splitlines()]))
    else:
        return rc, stdout
