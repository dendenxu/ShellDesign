#!/bin/bash
read word
word="$(echo $word | tr -d -c a-zA-Z)"
reve="$(echo $word | rev)"
# echo $word
# echo $reve
[ $word = $reve ] && echo "True" || echo "False"
