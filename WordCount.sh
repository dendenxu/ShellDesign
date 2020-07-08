#!/bin/bash
# WordCount
echo "My name is: $0"
echo "First argument is: $1"
# echo "Second argument is: $2"
dir_num="$(ls -l $1|grep ^d|wc -l|xargs)"
regular_num="$(ls -l $1|grep ^-|wc -l|xargs)"
exec_num="$(find $1 -type f -perm +111 -not \( -path "*/\.*" -o -path "\." \) |wc -l|xargs)"
regular_sum="$(find $1 -type f -exec du -c {} + | grep total | tr -d -c 0-9)"
echo "Number of directories: $dir_num"
echo "Number of regular files: $regular_num"
echo "Number of executable files: $exec_num"
echo "Total size of regular files: ${regular_sum} B"
