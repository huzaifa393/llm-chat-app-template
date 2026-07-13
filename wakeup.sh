#!/bin/bash
if ! systemctl is-active --quiet islamicrag; then
    sudo systemctl start islamicrag
    sleep 8
fi
touch /tmp/last_request
