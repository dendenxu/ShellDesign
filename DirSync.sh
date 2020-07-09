#!/bin/bash
# DirSync
if [ ! -d $1 ] ; then 
    echo "$1 is not a directory"
    exit 1
fi
echo "\$1 is $1"
echo "\$2 is $2"
echo "\$3 is $3"

copyContent() {
    mkdir $2 > /dev/null 2>&1
    for file in $1/*
    do
        if [[ -f $file ]]; then
            if [ "$3" = "-a" -o "${#3}" -eq 0 ]; then
                cp -a $file $2
            elif [ "$3" = "-s" ]; then
                cp -u $file $2
            fi
            echo "We're copying $file to $2"    
        else
            echo "This is where the recursion starts"
            stripped=${file##*/} # Expanding
            echo "The stripped version is: $stripped"
            echo "Source: $file"
            echo "Destination: $2/$stripped"
            mkdir $2/$stripped > /dev/null 2>&1
            ./DirSync.sh $file $2/$stripped $3 
        fi
    done
}

if [ "$3" = "-a" -o "${#3}" -eq 0 ]; then
    copyContent $1 $2
elif [ $3 = "-s" ]; then
    echo "Are you trying to sync these directories?"
    if [ ! -d $1 ]; then
        echo "$2 is not a directory"
        exit 1
    fi
fi


