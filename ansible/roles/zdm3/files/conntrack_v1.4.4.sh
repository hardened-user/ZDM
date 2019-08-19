#!/bin/bash
# -*- coding: utf-8 -*-
# 16.08.2019
# ----------------------------------------------------------------------------------------------------------------------
set -eu
set -o pipefail
export LC_ALL=""
export LANG="en_US.UTF-8"

##### COMMAND-LINE VERIFICATION #####
DPORT="${1:-}"
STATE="${2:-}"
PROTO="${3:-}"
if [[ -n "${DPORT}" ]]; then
   DPORT="dport=${DPORT} src"
fi
if [[ -n "${PROTO}" ]]; then
   PROTO="-p ${PROTO}"
fi

##### ENVIRONMENT VARIABLES #####
CONNTRACK="sudo /usr/sbin/conntrack"
# Overwrite
source "$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)/zdmcnf/conntrack.sh" &>>/dev/null || { echo "ZBX_ERROR"; exit 2; }

##### BEGINNING OF WORK #####
OUTPUT=$(${CONNTRACK} -L ${PROTO} 2>/dev/null) || { echo "ZBX_ERROR" ; exit 3; }
if [[ -n "${DPORT}" && -n "${STATE}" ]]; then
    echo "${OUTPUT}" | grep "${DPORT}" | grep "${STATE}" | wc -l
elif [[ -n "${DPORT}" ]]; then
    echo "${OUTPUT}" | grep "${DPORT}" | wc -l
elif [[ -n "${STATE}" ]]; then
    echo "${OUTPUT}" | grep "${STATE}" | wc -l
else
    echo "${OUTPUT}" | wc -l
fi
