# -*- coding: utf-8 -*-
# 20.06.2019
# ----------------------------------------------------------------------------------------------------------------------
import logging
import traceback

import requests
import simplejson


# ======================================================================================================================
# Functions
# ======================================================================================================================
def gitlab_runners_list(api_url: str, private_token: str, params=None, timeout=30) -> (None, list):
    url = "{}/runners/all".format(api_url.rstrip('/'))
    headers = {
        'Private-Token': private_token,
        'User-Agent': "Zabbix Data Mining"
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        data = resp.json()  # <'list'> || <'dict'>
    except simplejson.errors.JSONDecodeError:
        logging.error("Invalid JSON :: Failed to parse")
        return None
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    # __________________________________________________________________________
    if resp.status_code != 200 or not isinstance(data, list):
        logging.critical("Failed GET request :: {} {}\n{}\n\n{}".format(
            resp.status_code, resp.reason,
            '\n'.join("{}: {}".format(k, v) for k, v in resp.headers.items()),
            "{}\n".format(resp.text) if resp.text else ''))
        return None
    # __________________________________________________________________________
    try:
        data = list(filter(lambda x: x.get('id'), data))
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    # __________________________________________________________________________
    return data


def gitlab_runners_get(api_url: str, private_token: str, runner_id, timeout=30) -> (None, dict):
    url = "{}/runners/{}".format(api_url.rstrip('/'), runner_id)
    headers = {
        'Private-Token': private_token,
        'User-Agent': "Zabbix Data Mining"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        data = resp.json()  # <'list'> || <'dict'>
    except simplejson.errors.JSONDecodeError:
        logging.error("Invalid JSON :: Failed to parse")
        return None
    except Exception as err:
        logging.critical("Exception :: {}\n{}".format(err, "".join(traceback.format_exc())))
        return None
    # __________________________________________________________________________
    if resp.status_code == 404:
        logging.error("Runner not found :: {}".format(runner_id))
        return None
    elif resp.status_code != 200 or not isinstance(data, dict):
        logging.critical("Failed GET request :: {} {}\n{}\n\n{}".format(
            resp.status_code, resp.reason,
            '\n'.join("{}: {}".format(k, v) for k, v in resp.headers.items()),
            "{}\n".format(resp.text) if resp.text else ''))
        return None
    # __________________________________________________________________________
    return data
