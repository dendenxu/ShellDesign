#!/bin/bash
# DirSync
# echo "\$1 is $1"
# echo "\$2 is $2"
# echo "\$3 is $3"

# 我们实现了目录备份：
#     1. 增添型备份（-a：append）   ：目标目录中的非重名文件会得到保留
#     2. 覆盖型备份（-r：replace）  ：目标目录中的非重名文件不会得到保留
# 与目录同步：
#     1. 保守型同步（-u：update）   ：所有的文件都会得到保留，旧文件会被替换为新文件
#     2. 激进型同步（-s：sync）     ：我们根据文件夹和文件的修改时间戳判断文件是否应得到保留：
#                                     修改时间（dir1中文件（夹））晚于目标文件夹（dir2）的文件

# 对于两个文件夹的同步功能，我们必须认识到的一点是：
# 若要完全保证所有修改都按照时间顺序进行，我们就不得不进行log记录
# 作为一个普通shell脚本而非Microsoft OneDrive这种具有自我储存的文件同步程序
# 我们无法在不使用外部储存的方式进行完全按照时间戳的文件同步，但我们可以尽量模拟这一过程

# 我们采取这样一种模拟操作，在进行同步（-s：sync）过程中（非-u：update，update会保留全部文件）
# 我们只保留修改日期最新的文件
# 对于文件夹，我们以文件夹的修改日期和文件的修改日期为标准判断用户是否删除了某一文件，例如：
# 在dir1中，用户有file1，file2（修改时间为500），在dir2中也有file1，和file2（修改时间为500）
# 用户在时间点1000删除了目录一的file1，因此dir1的最后修改时间变为1000，接着，用户在dir2创建了file3，时间点为2000
# 我们发现500<1000而1000<2000，因此在同步过程中会删除dir2中的file1，而保留并复制file3

# 当然这种操作有删除不必要文件的风险（某些新文件可能不会得到同步）
# 若用户希望保留所有文件，他/她应使用-u（update）而非-s（sync）

export PATH="$PATH:."

copyContent() {
    # 本函数的功能是进行不检查时间的文件与目录同步
    # 我们会默认$2所示的目录不存在
    # 创建相关文件夹后我们会对文件进行拷贝，对目录进行递归调用操作
    mkdir $2 > /dev/null 2>&1 # SILENCE
    for file in $1/*
    do
        if [ -f $file ]; then
            echo "We're copying $file to $2"    
            cp $3a $file $2 # 这里的$3可能是-a或者-u，分别进行更新拷贝或全覆盖拷贝
        else
            stripped=${file##*/} # Expanding
            echo "This is where the recursion starts"
            echo "The stripped version is: $stripped"
            echo "Source: $file"
            echo "Destination: $2/$stripped"
            # 我们假设新的文件夹是不存在的（当然若已经存在我们会转移报错信息）
            mkdir $2/$stripped > /dev/null 2>&1
            # 我们进行一次全脚本的递归调用，以对子目录进行相同选项下的同步操作
            DirSync.sh $file $2/$stripped $3 
        fi
    done
}

syncContent() {
    for file in $1/*
    do
        stripped=${file##*/}
        if [ -f $file -o ! -d $2/$stripped ]; then
            file_time=$(stat -c %Y $file)
            dir_time=$(stat -c %Y $2)
            echo "$file is last modified at $file_time"
            echo "$2 is last modified at $dir_time"
            if [ ! -f $2/$stripped ]; then
                echo "Careful now, there's a new file or a file to be deleted"
                if [ $file_time -gt $dir_time ]; then
                    echo "[SYNC] I think we should sync the file since the file is newer than the target dir"
                    cp -ua $file $2
                else
                    echo "[DELETE] I think the file is ought to be deleted since it's not newer than the target dir"
                    rm -rf $file
                fi
            else
                echo "Whatever, we'll still do a -au copy"
                cp -ua $file $2
            fi
        else
            echo "This is where the syncing recursion starts"
            DirSync.sh $file $2/$stripped $3
        fi
    done
}

testDir() {
    if [ ! -d $1 ]; then
        echo "$1 is not a directory"
        exit 1
    fi
}

if [ ! -d $1 ] ; then 
    echo "$1 is not a directory"
    exit 1
fi

if [ "$3" = "-a" -o "${#3}" -eq 0 ]; then
    echo "Are you trying to back up a directory?"
    copyContent $1 $2 "-a"
elif [ $3 = "-r" ]; then
    echo "Are you trying to do a replace backup? All the files originally in $2 will be deleted"
    rm -rf $2
    # copyContent $1 $2 "-a"
    cp -ua $1 $2
elif [ $3 = "-u" ]; then
    echo "Are you trying to update between these directories?"
    testDir $2
    copyContent $1 $2 $3 
    copyContent $2 $1 $3
elif [ $3 = "-s" ]; then
    echo "This is the syncing part, aha! And it's DANGEROUS TO USE!"
    echo "You'd only want to use this when you've only made DIR CHANGE IN ONE OF THE TWO DIRS"
    testDir $2
    syncContent $1 $2 $3
    syncContent $2 $1 $3
else
    echo "Unrecognized flag, you can use -u to do updates between two dirs and -a to make appending backups"
fi

