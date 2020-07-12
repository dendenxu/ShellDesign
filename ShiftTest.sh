#!/bin/sh
while [ $# -gt 0 ]; do
    echo "Current \$1 is: $1"
    shift
done
