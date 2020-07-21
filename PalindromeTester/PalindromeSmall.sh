#!/bin/bash
# PalindromeSmall
# Author: Xu Zhen 徐震 3180105504
# 在本实现中，我们直接调用了tr命令来剔除不合要求的字符串

# 本语句读入一行用户输入内容并删除非字母内容，复制给word变量
word="$(read word; echo $word | tr -d -c a-zA-Z)"
# 本语句反转word变量，赋值给reve变量
reve="$(echo $word | rev)"

# DEBUG INFO
# echo $word
# echo $reve

# 本语句进行回文测试并打印测试结果
[ $word = $reve ] && echo "True" || echo "False"
