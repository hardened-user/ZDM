#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 20.08.2019
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: <addr> [<port>] [<hostname>] [<options>]

import datetime
import os
import re
import socket

from OpenSSL import SSL
from zdmcnf.cert import *
from zdmcnf.common import *

from zdmlib.common import *


def main():
    # __________________________________________________________________________
    # command-line options, arguments
    try:
        parser = MyArgumentParser()
        parser.add_argument('addr', action='store',
                            metavar="<ADDR>", help="IP or DNS address")
        parser.add_argument('port', action='store', nargs='?',
                            metavar="<PORT>", help="port (default: 443)")
        parser.add_argument('hostname', action='store', nargs='?',
                            metavar="<HOSTNAME>", help="verified hostname (default: <ADDR>)")
        parser.add_argument('options', action='store', nargs='?',
                            metavar="<OPTIONS>", help="additional options")
        args = parser.parse_args()
    except SystemExit:
        print_to_zabbix("ZBX_ERROR")
        return False
    # port
    if not args.port:
        args.port = 443
    else:
        args.port = int(args.port)
    # hostname
    if not args.hostname:
        args.hostname = args.addr
    # __________________________________________________________________________
    if args.addr:
        result = get_result(args.addr, args.port, args.hostname, args.options, cnf_common_timeout)
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
def get_result(addr, port, hostname, options, timeout):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(timeout)
        sock.settimeout(timeout)
        sock.connect((addr, port))
        ctx = SSL.Context(SSL.TLSv1_METHOD)
        ctx.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_callback)
        ctx.load_verify_locations(cnf_cert_ca_file)
        ssl_sock = SSL.Connection(ctx, sock)
        ssl_sock.set_connect_state()
        ssl_sock.set_tlsext_host_name(hostname.encode('utf-8', 'replace'))  # name must be a byte string
        sock.settimeout(None)  # WARNING: OpenSSL.SSL.WantReadError if set timeout before do_handshake()
        ssl_sock.do_handshake()
        ssl_sock.shutdown()
    except socket.timeout as err:
        # Response timeout
        logging.error("Socket Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return 11
    except socket.error as err:
        logging.error("Socket Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        if err.errno == 104:
            # Connection reset by peer
            return 12
        elif err.errno == -2:
            # Name or service not known
            return 13
        else:
            # Socket error
            return 10
    except SSL.Error as err:
        logging.error("SSL Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return 99
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return 99
    # __________________________________________________________________________
    # verification
    return verify_cert(hostname, options)


# noinspection PyUnusedLocal
def verify_callback(connection, cert, error_number, error_depth, ok):
    """
    Verify callback function.
    """
    # print(connection)  # <OpenSSL.SSL.Connection object at 0x7fae6244d2b0>
    # print(cert)  # <OpenSSL.crypto.X509 object at 0x7f5da7bd72e8>
    # print(cert.get_issuer())
    # print("error_number: {}".format(error_number))  # <class 'int'>
    # print("error_depth: {}".format(error_depth))  # <class 'int'>
    # print("ok: {}".format(ok))  # <class 'int'>  0 - Bad, 1 - Good
    # WARNING: Если вернуть 1, когда 'ok' == 0 (Bad), то функция выполниться еще раз.
    #          Если вернуть 0, то произойдет raise OpenSSL.SSL.Error: 'certificate verify failed'.
    # WARNING: Всегда возвращаем 1. Валидацию проводит функция verify_cert().
    # __________________________________________________________________________
    # Последний сертификат в цепочке
    if error_depth == 0:
        if not CERT_DICT:
            CERT_DICT['verify'] = ok  # <class 'int'>
            CERT_DICT['subject'] = "{}".format(cert.get_subject()).replace("X509Name object ", '')  # <class 'str'>
            CERT_DICT['commonName'] = cert.get_subject().commonName  # <class 'str'>
            CERT_DICT['notBefore'] = cert.get_notBefore().decode('utf-8', 'replace')  # <class 'bytes'> -> <class 'str'>
            CERT_DICT['notAfter'] = cert.get_notAfter().decode('utf-8', 'replace')  # <class 'bytes'> -> <class 'str'>
            CERT_DICT['expired'] = cert.has_expired()  # <class 'bool'>
    # __________________________________________________________________________
    return 1


def verify_cert(hostname, options):
    # __________________________________________________________________________
    if not CERT_DICT:
        logging.error("Internal Error :: Empty dict")
        return 99
    # __________________________________________________________________________
    if options and 's' in options:
        allow_self_singed = True
    else:
        allow_self_singed = False
    # __________________________________________________________________________
    if CERT_DICT['verify'] == 1 or allow_self_singed:
        if CERT_DICT['verify'] == 0 and allow_self_singed:
            logging.info("x509 subject :: {} (Self-Signed)".format(CERT_DICT['subject']))
        else:
            logging.info("x509 subject :: {}".format(CERT_DICT['subject']))
        logging.info("x509 expired :: {} - {}".format(CERT_DICT['notBefore'], CERT_DICT['notAfter']))
        logging.info("x509 commonName :: {}".format(CERT_DICT['commonName']))
        # expired
        if CERT_DICT['expired']:
            logging.info("Certificate verify failed :: expired")
            return 2
        # commonName
        # TODO : alt names
        regex_name = CERT_DICT['commonName'].replace('.', r'\.').replace('*', r'.+') + '$'
        re_hostname = re.compile(regex_name)
        if not re_hostname.search(hostname):
            logging.info("Certificate verify failed :: commonName")
            return 2
        # expired soon
        dt = datetime.datetime.now().utcnow()
        # WARNING: Timezone UTC. Z - Zulu, UTC/GMT+0
        x509_not_after = datetime.datetime.strptime(CERT_DICT['notAfter'], "%Y%m%d%H%M%SZ")
        if (x509_not_after - dt).total_seconds() < cnf_cert_warn_days_before_expiry * 24 * 60 * 60:
            logging.info("Certificate verify succeeded, but will expire soon")
            return 1
    else:
        logging.info("x509 subject :: {}".format(CERT_DICT['subject']))
        logging.info("x509 expired :: {} - {}".format(CERT_DICT['notBefore'], CERT_DICT['notAfter']))
        logging.info("x509 commonName :: {}".format(CERT_DICT['commonName']))
        logging.info("Certificate verify failed")
        return 2
    # __________________________________________________________________________
    logging.info("Certificate verify succeeded")
    return 0


# ======================================================================================================================
# Objects
# ======================================================================================================================
CERT_DICT = {}

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if __name__ == '__main__':
    from zdmlib.log import logging_setup

    log_file_path = os.path.join(cnf_common_log_dir, os.path.basename(sys.argv[0]) + ".log")
    logging_setup(filename=log_file_path, level=cnf_common_log_level)
    # logging_setup(level=logging.DEBUG)  #### TEST
    logging.info(' '.join(sys.argv))
    # __________________________________________________________________________
    sys.exit(not main())  # Compatible return code
