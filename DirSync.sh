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

# 注意，若被同步目录下有同名文件，但两者类型不同，我们不敢贸然复制，请用户手动选择要保留文件夹还是文件

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
            # echo "We're copying $file to $2"    
            cp $3a $file $2 # 这里的$3可能是-a或者-u，分别进行更新拷贝或全覆盖拷贝
        else
            stripped=${file##*/} # Expanding
            # echo "This is where the recursion starts"
            # echo "The stripped version is: $stripped"
            echo "[RECURSION] Source: $file"
            echo "[RECURSION] Destination: $2/$stripped"
            # 我们假设新的文件夹是不存在的（当然若已经存在我们会转移报错信息）
            mkdir $2/$stripped > /dev/null 2>&1
            # 我们进行一次全脚本的递归调用，以对子目录进行相同选项下的同步操作
            DirSync.sh $file $2/$stripped $3  "DUMMY" # 我们传入DUMMY参数以禁用提示符
        fi
    done
}

syncContent() {
    # 我们调用此函数来进行不同文件夹下的同步
    # 同步的逻辑如文件开头所说，根据目标目录和当前文件的文件的最近修改时间来确定何时删除
    # 因此这一操作是危险的，若用户的改动较为复杂，我们不推荐使用这种方式
    for file in $1/*
    do
        stripped=${file##*/}
        if [ -f $file -o ! -d $2/$stripped ]; then
            # 对于在目标目录不存在的文件，我们进行按照时间的更新
            # 若$file是目录，而目标目录下不存在这一子目录，我们将其当作文件处理
            file_time=$(stat -c %Y $file)
            dir_time=$(stat -c %Y $2)
            # echo "$file is last modified at $file_time"
            # echo "$2 is last modified at $dir_time"
            if [ ! -f $2/$stripped ]; then
                # echo "Careful now, there's a new file or a file to be deleted"
                if [ $file_time -lt $dir_time ]; then
                    echo "[DELETE] I think the file is ought to be deleted since it's not newer than the target dir"
                    rm -rf $file
                else
                    echo "[SYNC] I think we should sync the file since the file is newer than the target dir"
                    cp -ua $file $2
                fi
            else
                # echo "Whatever, we'll still do a -au copy"
                cp -ua $file $2
            fi
        else
            # 我们在目标目录下存在$file对应的子目录的情况下进行递归调用
            echo "[RECURSION] Source: $file"
            echo "[RECURSION] Destination: $2/$stripped"
            # echo "This is where the syncing recursion starts"
            DirSync.sh $file $2/$stripped $3 "DUMMY" # 我们传入DUMMY参数以禁用提示符
        fi
    done
}

testDir() {
    # 检查是否为目录，否则退出整个脚本
    if [ ! -d $1 ]; then
        echo "[FATAL] $1 is not a directory"
        exit 1
    fi
}

promptYN() {
    # 提示用户确认操作
    # 我们通过调用local确定相关regex
    message=$1
    set -- $(locale LC_MESSAGES)
    yesptrn=$1
    noptrn=$2
    # echo $yesptrn
    # echo $noptrn
    while true; do
    read -p "$message(Y/n)? " yn
        case $yn in
            ${yesptrn##^} ) return 0;; # 这里返回零表示True
            ${noptrn##^} ) return 1;; # 这里返回一表示False（我们也很奇怪）
            * ) echo "Please answer (Y/n).";; #用户输入的内容有误
        esac
    done
}

displayHelp()
{
    echo -e "\n-a"
    echo "    Perform an appending backup: files not in dir1 will be retained in dir2"
    echo -e "\n-r"
    echo "    Perform a replacing backup: everything under dir2 will be exact what they were in dir1"
    echo -e "\n-u"
    echo "    Perform a mutual update: files with same names will be updated to the newest versioni"
    echo -e "\n-s"
    echo "    Perform a syncing update: we'll decide that a file is newly created if its timestamp is bigger than the destination dir"
    echo "    and there's no same-named file in the destination dir. And we'll decided that the user deleted the file if otherwise (no same-named and dir newer than file)"
    echo -e "\n-h"
    echo "    Display this help page. This option should be used separatedly: ./DirSync.sh -h"
}

# 程序的主逻辑
if [ $1 = "-h" ]; then
    displayHelp
    exit 0
fi

testDir $1

if [ "$3" = "-a" -o "${#3}" -eq 0 ]; then
    if [ -z $4 ]; then
        echo "[INFO] Are you trying to back up $1 to $2?"
        promptYN || exit 0
    fi
    copyContent $1 $2 "-a"
elif [ $3 = "-r" ]; then
    if [ -z $4 ]; then
        echo "[INFO] Are you trying to do a replace backup from $1 to $2?"
        echo "All the files originally in $2 will be deleted"
        promptYN || exit 0
    fi
    rm -rf $2
    cp -ua $1 $2
elif [ $3 = "-u" ]; then
    if [ -z $4 ]; then
        echo "[INFO] Are you trying to update between $1 and $2?"
        promptYN || exit 0
    fi
    testDir $2
    copyContent $1 $2 $3 
    copyContent $2 $1 $3
elif [ $3 = "-s" ]; then
    if [ -z $4 ]; then
        echo "[INFO] This is the syncing part, aha! And it's DANGEROUS TO USE!"
        echo "[INFO] You'd only want to use this when you've only made DIR CHANGE IN ONE OF THE TWO DIRS"
        promptYN || exit 0
    fi
    testDir $2
    syncContent $1 $2 $3
    syncContent $2 $1 $3
else
    echo "[FATAL] Unrecognized flag, use -a to do appending update, -u to do mutual update, -r to do full replacement and -s to do sync"
    displayHelp
fi

