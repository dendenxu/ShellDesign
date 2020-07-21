#!/bin/bash
# WordCount
# Author: Xu Zhen 徐震 3180105504

# 统计目录文件个数
dir_num="$(ls -l $1|grep ^d|wc -l|xargs)"
regular_num="$(ls -l $1|grep ^-|wc -l|xargs)"
exec_num="$(find $1 -type f -perm /111 -not \( -path "*/\.*" -o -path "\." \) | wc -l | xargs)"
regular_sum="$(find $1 -type f -not \( -path "*/\.*" -o -path "\." \) -exec du -cb {} + | grep total | tr -d -c 0-9)"
echo "Number of directories: $dir_num"
echo "Number of regular files: $regular_num"
echo "Number of executable files: $exec_num"
echo "Total size of regular files: ${regular_sum} Byte(s)"
