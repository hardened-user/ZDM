#!/bin/bash
# 08.05.2019
# ----------------------------------------------------------------------------------------------------------------------
# USAGE: <metric>

set -eu
set -o pipefail
export LC_ALL=""
export LANG="en_US.UTF-8"

##### COMMAND-LINE VERIFICATION #####
METRIC="${1:-}"
if [[ -z "${METRIC}" ]]; then
  echo "ZBX_ERROR"
  exit 1
fi

##### ENVIRONMENT VARIABLES #####
# Default
MEMCACHED_TOOL="memcached-tool"
MEMCACHED_ADDR="127.0.0.1:11211"
# Overwrite
source "$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)/zdmcnf/memcached.sh" &>>/dev/null || { echo "ZBX_ERROR"; exit 2; }

##### BEGINNING OF WORK #####
OUTPUT=$(${MEMCACHED_TOOL} "${MEMCACHED_ADDR}" "${METRIC}" 2>&1) || { echo "ZBX_ERROR"; exit 3; }
echo "${OUTPUT}" | sed 's/[[:blank:]]\+/ /g;s/^[[:blank:]]*//;s/[[:blank:]]*$//'
