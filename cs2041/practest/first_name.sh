#!/bin/sh

cut -d"|" -f3 $1 | uniq | cut -d" " -f2 | sort | uniq -c | sort -n
