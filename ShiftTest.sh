#!/bin/bash
# while [ $# -gt 0 ]; do
#     echo "Current \$1 is: $1"
#     shift
# done

full_string=""

while read -r temp; do
    # echo "$full_string"
    full_string+="$temp"$'\n'
done
echo "$full_string"
echo "Done"