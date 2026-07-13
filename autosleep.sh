#!/bin/bash
LAST=$(stat -c %Y /tmp/last_request 2>/dev/null || echo 0)
NOW=$(date +%s)
DIFF=$((NOW - LAST))
if [ $DIFF -gt 1800 ]; then
    sudo systemctl stop islamicrag
fi
