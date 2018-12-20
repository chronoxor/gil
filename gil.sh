#!/bin/bash
set -e
curdir=`dirname $0`
python3 $curdir/gil.py $*
