#!/bin/bash
# 这是一个现代教务管理系统，主要面向作业管理
# 我们通过编写Shell程序来管理作业数据库

function DefineColor() {
    # 我们使用tput命令来定义颜色信息
    # 各类颜色常数，通过echo调用可以改变Shell的输出样式
    # 例如echo "${Red}Hello${NoColor}, world."会打印红色的Hello和原色的World
    # 上述例子会展开成echo "$(tput setaf 1)Hello$(tput sgr0), world."
    # ! consider more about this colorization
    Red=$(tput setaf 1)
    Green=$(tput setaf 2)
    Yellow=$(tput setaf 3)
    Blue=$(tput setaf 4)
    Magenta=$(tput setaf 5)
    Cyan=$(tput setaf 6)
    NoColor=$(tput sgr0)
}

function DefineMySQL() {
    # 我们通过mysql命令来直接执行数据库操作，这也是本实验的核心内容
    # 我们通过设置文件的方式使得MySQL不会抱怨直接在命令行输入密码不安全
    # * 注意：您可以修改程序运行目录下的.mysql.cnf文件来设置自己的数据库样式
    # ! 请保证MySQL已经在本机正确安装，且.mysql.cnf已经被正确配置
    # 您需要在.mysql.cnf中设置您的登录名/密码/服务器，并设置数据库名称(和您在MySQL中使用的相同)
    # 例如您在MySQL中创建了ShellDesigner这个用户，密码为ShellDesigner，并打算使用ShellDesign这个数据库来管理本软件涉及到的内容
    # .mysql.cnf就将有类似如下的内容
    # [client]
    # user=ShellDesigner
    # password=ShellDesigner
    # host=localhost
    # database=ShellDesign

    # ! 第一次使用本软件时请运行当前目录下的table.sql来初始化数据库中的表
    # 必须运行的部分是所有的create table
    # 后面的insert内容是可选的，但是至少要有一个管理员账户，否则本软件没有什么意义
    
    mysql_u_default="ShellDesigner"
    mysql_p_default="ShellDesigner"
    mysql_h_default="localhost"
    mysql_d_default="ShellDesign"
    mysql_f=".mysql.cnf"
    if [ ! -f "$mysql_f" ]; then
        echo "Automatically generating configuration file..." >&2
        echo "[client]" >$mysql_f
        echo "user=$mysql_u_default" >>$mysql_f
        echo "password=$mysql_p_default" >>$mysql_f
        echo "host=$mysql_h_default" >>$mysql_f
        echo "database=$mysql_d_default" >>$mysql_f
    fi

    mysql_prefix="mysql --defaults-extra-file=$mysql_f"
}

function PrintBanner() {
    # line="##################################################################################################################################"
    # echo "$Yellow$line"
    # echo ""
    clear
    cat <<"EOF"
   _________                                                       __        _____                                                  
   \_   ___ \  ____  __ _________  ______ ______  _  _____________|  | __   /     \ _____    ____ _____     ____   ___________      
   /    \  \/ /  _ \|  |  \_  __ \/  ___// __ \ \/ \/ /  _ \_  __ \  |/ /  /  \ /  \\__  \  /    \\__  \   / ___\_/ __ \_  __ \     
   \     \___(  <_> )  |  /|  | \/\___ \\  ___/\     (  <_> )  | \/    <  /    Y    \/ __ \|   |  \/ __ \_/ /_/  >  ___/|  | \/     
    \______  /\____/|____/ |__|  /____  >\___  >\/\_/ \____/|__|  |__|_ \ \____|__  (____  /___|  (____  /\___  / \___  >__|        
           \/                         \/     \/                        \/         \/     \/     \/     \//_____/      \/            
EOF
    # echo ""
    # echo "$line$NoColor"
}

function PrintDelimiter() {
    clear
    line="###########################################################################"
    echo "$line"
    cat <<"EOF"
   ______     ______     ______     ______   __     ______     __   __     
  /\  ___\   /\  ___\   /\  ___\   /\__  _\ /\ \   /\  __ \   /\ "-.\ \    
  \ \___  \  \ \  __\   \ \ \____  \/_/\ \/ \ \ \  \ \ \/\ \  \ \ \-.  \   
   \/\_____\  \ \_____\  \ \_____\    \ \_\  \ \_\  \ \_____\  \ \_\\"\_\  
    \/_____/   \/_____/   \/_____/     \/_/   \/_/   \/_____/   \/_/ \/_/  
                                                                           
EOF
    echo "$line"
}

function PrintTeacher() {
    clear

    line="##############################################################################"
    echo "$line"
    cat <<"EOF"
   ______   ______     ______     ______     __  __     ______     ______    
  /\__  _\ /\  ___\   /\  __ \   /\  ___\   /\ \_\ \   /\  ___\   /\  == \   
  \/_/\ \/ \ \  __\   \ \  __ \  \ \ \____  \ \  __ \  \ \  __\   \ \  __<   
     \ \_\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_\ \_\ 
      \/_/   \/_____/   \/_/\/_/   \/_____/   \/_/\/_/   \/_____/   \/_/ /_/ 
                                                                             
EOF
    echo "$line"
}

function PrintStudent() {
    clear

    line="#############################################################################"
    echo "$line"
    cat <<"EOF"
   ______     ______   __  __     _____     ______     __   __     ______  
  /\  ___\   /\__  _\ /\ \/\ \   /\  __-.  /\  ___\   /\ "-.\ \   /\__  _\ 
  \ \___  \  \/_/\ \/ \ \ \_\ \  \ \ \/\ \ \ \  __\   \ \ \-.  \  \/_/\ \/ 
   \/\_____\    \ \_\  \ \_____\  \ \____-  \ \_____\  \ \_\\"\_\    \ \_\ 
    \/_____/     \/_/   \/_____/   \/____/   \/_____/   \/_/ \/_/     \/_/ 
                                                                           
EOF
    echo "$line"
}

function PrintAdmin() {
    clear

    line="#########################################################"
    echo "$line"
    cat <<"EOF"
   ______     _____     __    __     __     __   __    
  /\  __ \   /\  __-.  /\ "-./  \   /\ \   /\ "-.\ \   
  \ \  __ \  \ \ \/\ \ \ \ \-./\ \  \ \ \  \ \ \-.  \  
   \ \_\ \_\  \ \____-  \ \_\ \ \_\  \ \_\  \ \_\\"\_\ 
    \/_/\/_/   \/____/   \/_/  \/_/   \/_/   \/_/ \/_/ 
                                                       
EOF
    echo "$line"
}

function StudentUI() {
    # login informations
    [ -z $1 ] && sid=1 || sid=$1
    [ -z $2 ] && name="st1" || name=$2
    while :; do # student main UI event loop
        PrintStudent

        query_id="select cid from take where sid=$sid"
        query_course="select id 课程号, name_zh 中文名称, name_en 英文名称 from course where id in ($query_id)"
        cids=($($mysql_prefix -se "$query_id;"))
        echo "$name同学您好，欢迎来到现代作业管理系统（Modern Coursework Manage System）"
        echo "您可以进行的操作有："
        echo "1. 管理课程"
        echo "0. 返回上一级"
        while :; do # 操作循环UI，直到获得正确的输入
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了管理课程"
                if [ ${#cids[@]} -eq 0 ]; then
                    echo "您本学期没有课程"
                    exit 0
                fi
                echo "您本学期共${#cids[@]}有门课程，它们分别为："
                $mysql_prefix -e "$query_course;"
                while :; do
                    read -rp "请输入您想要管理的课程号：" cid
                    [[ "${cids[@]}" =~ "${cid}" ]] && break
                    echo "您输入的课程号$cid有误，请输入上表中列举出的某个课程号"
                done

                StudentOPCourse
                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function StudentOPCourse() {
    while :; do
        PrintStudent

        target="$Green课程实验/作业$NoColor"
        query_tid="select tid from teach where cid=$cid"
        query_teacher="select id 教师工号, name 教师姓名 from teacher where id in ($query_tid)"
        echo "您选择的课程为："
        $mysql_prefix -e "select id 课程号, name_zh 中文名称, name_en 英文名称 from course where id=$cid;"

        echo "教这门课的老师有："
        $mysql_prefix -e "$query_teacher;"

        # ops=(1 2 3)
        echo "您可以进行的操作有："
        echo "1. 管理${target}"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了管理本课程的${target}"
                query_hid="select id from homework where cid=$cid"
                query_hw="select id 作业ID, intro 作业简介, creation_time 作业发布时间, end_time 作业截止时间 from homework where cid=$cid"

                hids=($($mysql_prefix -e "$query_hid;"))
                if [ ${#hids[@]} -gt 0 ]; then
                    echo "本课程已有的${target}如下图所示"
                    $mysql_prefix -e "$query_hw;"
                else
                    echo "本课程还没有已发布的${target}"
                    return 0
                fi
                echo "您选择了管理${target}"
                while :; do
                    read -rp "请输入您想要管理的${target}ID：" hid
                    [[ "${hids[@]}" =~ "${hid}" ]] && break
                    echo "您输入的${target}ID$hid有误，请输入上表中列举出的某个${target}ID"
                done

                StudentManageSubmission

                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function PrintAttachment() {
    if [ "$attachment_count" -gt 0 ]; then
        echo "本${target}的附件包括："
        $mysql_prefix -e "$query_attachment;"
    else
        echo "$Red本${target}$Red还没有附件$NoColor"
    fi
}

function StudentManageSubmission() {
    while :; do
        PrintStudent

        upper="$Green课程作业/实验$NoColor"
        target="$upper$Green提交$NoColor"
        echo "您选择了修改以下的$upper："
        query_course_homework="select id \`作业/实验ID\`, intro \`作业/实验简介\`, creation_time 创建时间, end_time 截止时间 from homework where id=$hid"
        query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$hid"
        query_count_attachment="select count(1) from attachment join attach_to on id=aid where uid=$hid"
        $mysql_prefix -e "$query_course_homework;"
        attachment_count=$($mysql_prefix -se "$query_count_attachment")
        temp=${target}
        target=$upper
        PrintAttachment
        target=$temp

        query_subids="select id from submission where sid=$sid and hid=$hid"
        subids=($($mysql_prefix -se "$query_subids;"))
        query_subs="select id 提交ID, submission_text 提交内容, creation_time 创建时间, latest_modification_time 最近修改时间 from submission where id in ($query_subids)"

        if [ ${#subids[@]} -gt 0 ]; then
            echo "您在本$upper创建的${target}如下所示"
            $mysql_prefix -e "$query_subs;"
        else
            echo "您在本$upper下还没有${target}"
        fi

        echo "您可以进行的操作有："
        echo "1. 发布新的${target}"
        echo "2. 删除已发布的${target}"
        echo "3. 修改已发布的${target}"
        echo "4. 查看已发布的${target}"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了发布新的${target}"
                echo "请输入${target}的简介内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的${target}的简介内容为\n$full_string"

                # 由于我们需要保证在Content中与其他具体类型中的标号相同，我们使用Commit
                query_insert_content="insert into content value ()"
                query_insert_submission="insert into submission value (last_insert_id(), $sid, $hid, \"$full_string\", now(), now())"

                subid=$($mysql_prefix -se "set autocommit=0;$query_insert_content;select last_insert_id();$query_insert_submission;commit;set autocommit=1;")

                echo "您刚刚添加的${target}ID为：$subid"
                attachment_count=0
                while :; do
                    read -rp "请输入您是否需要为${target}添加附件（Y/n）：" need_attach
                    if [[ $need_attach =~ ^[1Yy] ]]; then
                        attachment_count+=1
                        echo "您选择了添加附件"
                        read -rp "请输入您想要添加的附件名称：" attach_name
                        attach_name=$(RemoveDanger "$attach_name")
                        echo "您的附件名称为：$attach_name"
                        read -rp "请输入您想要添加的附件URL：" attach_url
                        # 对于URL，我们使用不同的转义策略
                        attach_url=$(RemoveDanger "$attach_url" "[\"'\.\*;]")
                        echo "您的附件URL为：$attach_url"
                        query_insert_attach="insert into attachment(name, url) value (\"$attach_name\", \"$attach_url\")"
                        query_insert_attach_to="insert into attach_to(aid, uid) value (last_insert_id(), $subid)"
                        attach_id=$($mysql_prefix -se "set autocommit=0;$query_insert_attach;select last_insert_id();$query_insert_attach_to;commit;set autocommit=1;")
                        echo "您刚刚添加的附件ID为：$attach_id"
                    else
                        break
                    fi
                done

                echo "您刚刚对课程号为$cid的课程的ID为$hid的$upper发布了如下的${target}："
                query_course_submission="select id 提交ID, submission_text 提交内容, creation_time 创建时间, latest_modification_time 最近修改时间 from submission where id=$subid"
                query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$subid"
                $mysql_prefix -e "$query_course_submission;"

                PrintAttachment
                break
                ;;
            2)
                echo "您选择了删除已发布的${target}"
                if [ ${#subids[@]} -eq 0 ]; then
                    echo "您在本$upper下还没有${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要删除的${target}ID：" subid
                    [[ "${subids[@]}" =~ "${subid}" ]] && break
                    echo "您输入的${target}ID$subid有误，请输入上表中列举出的某个${target}ID"
                done
                # query_delete_attach_to="delete from attach_to where uid=$subid"
                # query_delete_submission="delete from submission where id=$subid"
                query_delete_content="delete from content where id=$subid"
                # $mysql_prefix -e "set autocommit=0;$query_delete_attach_to;$query_delete_submission;$query_delete_content;commit;set autocommit=1;"
                $mysql_prefix -e "$query_delete_content;"
                break
                ;;
            3)
                echo "您选择了修改已发布的${target}"
                if [ ${#subids[@]} -eq 0 ]; then
                    echo "您在本$upper下还没有${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要修改的${target}ID：" subid
                    [[ "${subids[@]}" =~ "${subid}" ]] && break
                    echo "您输入的${target}ID$subid有误，请输入上表中列举出的某个${target}ID"
                done

                echo "您选择修改的${target}为："
                query_course_submission="select id 提交ID, submission_text 提交内容, creation_time 创建时间, latest_modification_time 最近修改时间 from submission where id=$subid"
                query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$subid"
                $mysql_prefix -e "$query_course_submission;"
                query_count_attachment="select count(1) from attachment join attach_to on id=aid where uid=$subid"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")

                PrintAttachment

                echo "请输入${target}的简介内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的${target}的简介内容为\n$full_string"

                # 由于我们需要保证在Content中与其他具体类型中的标号相同，我们使用Commit
                query_modify_submission="update submission set submission_text=\"$full_string\", latest_modification_time=now() where id=$subid"
                $mysql_prefix -e "$query_modify_submission;"
                echo "您刚刚修改的${target}ID为：$subid"
                while :; do
                    read -rp "请输入您是否需要为${target}添加附件（Y/n）：" need_attach
                    if [[ $need_attach =~ ^[1Yy] ]]; then
                        echo "您选择了添加附件"
                        read -rp "请输入您想要添加的附件名称：" attach_name
                        attach_name=$(RemoveDanger "$attach_name")
                        echo "您的附件名称为：$attach_name"
                        read -rp "请输入您想要添加的附件URL：" attach_url
                        # 对于URL，我们使用不同的转义策略
                        attach_url=$(RemoveDanger "$attach_url" "[\"'\.\*;]")
                        echo "您的附件URL为：$attach_url"
                        query_insert_attach="insert into attachment(name, url) value (\"$attach_name\", \"$attach_url\")"
                        query_insert_attach_to="insert into attach_to(aid, uid) value (last_insert_id(), $subid)"
                        attach_id=$($mysql_prefix -se "set autocommit=0;$query_insert_attach;select last_insert_id();$query_insert_attach_to;commit;set autocommit=1;")
                        echo "您刚刚添加的附件ID为：$attach_id"
                    else
                        break
                    fi
                done

                echo "您刚刚对课程号为$cid的课程的ID为$hid的$upper修改了如下的${target}："
                $mysql_prefix -e "$query_course_submission;"

                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                PrintAttachment
                break
                ;;
            4)
                echo "您选择了查询已发布的${target}"
                if [ ${#subids[@]} -eq 0 ]; then
                    echo "您在本$upper下还没有${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要查询的作业/实验提交ID：" subid
                    [[ "${subids[@]}" =~ "${subid}" ]] && break
                    echo "您输入的提交ID$subid有误，请输入上表中列举出的某个提交ID"
                done

                echo "您选择查询的提交为："
                query_course_submission="select id 提交ID, submission_text 提交内容, creation_time 创建时间, latest_modification_time 最近修改时间 from submission where id=$subid"
                query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$subid"
                $mysql_prefix -e "$query_course_submission;"
                query_count_attachment="select count(1) from attachment join attach_to on id=aid where uid=$subid"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")

                PrintAttachment
                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function TeacherUI() {
    # login informations
    [ -z "$1" ] && tid=1 || tid=$1
    [ -z "$2" ] && name="zy" || name=$2

    while :; do
        PrintTeacher

        query_id="select cid from teach where tid=$tid"
        query_course="select id 课程号, name_zh 中文名称, name_en 英文名称 from course where id in ($query_id)"
        cids=($($mysql_prefix -se "$query_id;"))

        echo "$name老师您好，欢迎来到现代作业管理系统（Modern Coursework Manage System）"
        echo "您可以进行的操作有："
        echo "1. 管理课程"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            # [[ "${ops[@]}" =~ "${op}" ]] && break
            # echo "您选择了操作：$op"
            case $op in
            1)
                echo "您选择了管理课程"
                if [ ${#cids[@]} -eq 0 ]; then
                    echo "您本学期没有课程"
                    break
                fi
                echo "您本学期共${#cids[@]}有门课程，它们分别为："
                $mysql_prefix -e "$query_course;"
                while :; do
                    read -rp "请输入您想要管理的课程号：" cid
                    [[ "${cids[@]}" =~ "${cid}" ]] && break
                    echo "您输入的课程号$cid有误，请输入上表中列举出的某个课程号"
                done

                TeacherOPCourse
                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function TeacherOPCourse() {
    while :; do
        PrintTeacher

        target="$Green课程$NoColor"
        query_tid="select tid from teach where cid=$cid"
        query_teacher="select id 教师工号, name 教师姓名 from teacher where id in ($query_tid)"

        echo "您选择的${target}为："
        $mysql_prefix -e "select id 课程号, name_zh 中文名称, name_en 英文名称 from course where id=$cid;"

        tids=($($mysql_prefix -e "$query_tid and tid <> $tid;"))
        if [ ${#tids[@]} -gt 0 ]; then
            echo "与您一同教这门课的老师有："
            $mysql_prefix -e "$query_teacher and id <> $tid;"
        else
            echo "这门${target}只有您自己在教"
        fi

        # ops=(1 2 3)
        echo "您可以进行的操作有："
        echo "1. 管理修读${target}的学生"
        echo "2. 管理${target}作业/实验"
        echo "3. 管理本${target}信息（管理公告/简介等）"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            # [[ "${ops[@]}" =~ "${op}" ]] && break
            # echo "您选择了操作：$op"
            case $op in
            1)
                echo "您选择了管理修读该${target}的学生"
                TeacherManageStudent
                break
                ;;
            2)
                echo "您选择了管理本${target}的实验和作业"
                TeacherManageHomework
                break
                ;;
            3)
                echo "您选择了管理本${target}的公告/信息"
                TeacherManageCourse
                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function TeacherManageCourse() {
    # ops=(1 2)
    while :; do
        PrintTeacher

        target1="$Green课程公告$NoColor"
        target2="$Green课程简介$NoColor"
        echo "您可以进行的操作有："
        echo "1. 管理课程$target1"
        echo "2. 修改课程$target2"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            # [[ "${ops[@]}" =~ "${op}" ]] && break
            # echo "您选择了操作：$op"
            case $op in
            1)
                echo "您选择了管理$target1"
                TeacherManageCourseInfo
                break
                ;;
            2)
                echo "您选择了修改$target2"
                TeacherManageCourseBrief
                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function TeacherManageCourseBrief() {
    target="$Green课程简介$NoColor"
    echo "${target}的原内容为"
    $mysql_prefix -e "select brief 课程简介 from course where id=$cid"
    echo "请输入${target}的新内容，以EOF结尾（换行后Ctrl+D）"
    full_string=""
    while read -r temp; do
        full_string+="$temp"$'\n'
    done

    full_string=$(RemoveDanger "$full_string")

    echo -e "您的新${target}内容为\n$full_string"
    query_brief_update="update course set brief = \"$full_string\" where id=$cid"
    # 我们增加了字符串处理函数以减少受到SQL注入攻击的可能性。
    # we can easily perfomr SQL injection if the string is not carefully treated
    # update course set brief = "Hello, world.";select * from admin;\" where id=$cid
    $mysql_prefix -e "$query_brief_update;"
}

function TeacherManageCourseInfo() {
    while :; do
        PrintTeacher

        target="$Green课程公告$NoColor"
        query_iid="select id from info where cid=$cid"
        query_info="select id 公告ID, release_time 公告发布时间, content 公告内容 from info where cid=$cid"

        iids=($($mysql_prefix -e "$query_iid;"))
        if [ ${#iids[@]} -gt 0 ]; then
            echo "本课程已有的${target}如下图所示"
            $mysql_prefix -e "$query_info;"
        else
            echo "本课程没有已发布的${target}"
        fi

        echo "您可以进行的操作有："
        echo "1. 发布新的${target}"
        echo "2. 删除已发布的${target}"
        echo "3. 修改已发布的${target}"
        echo "0. 返回上一级"

        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了发布新的${target}"
                echo "请输入${target}的新内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的新${target}内容为\n$full_string"

                # 由于我们需要保证在Content中与其他具体类型中的标号相同，我们使用Commit
                query_insert_content="insert into content value ()"
                query_insert_info="insert into info(id, content, cid, release_time) value (last_insert_id(), \"$full_string\", $cid, now())"

                iid=$($mysql_prefix -se "set autocommit=0;$query_insert_content;select last_insert_id();$query_insert_info;commit;set autocommit=1;")

                echo "您刚刚发布的${target}ID为：$iid"
                attachment_count=0
                while :; do
                    read -rp "请输入您是否需要为${target}添加附件（Y/n）：" need_attach
                    if [[ $need_attach =~ ^[1Yy] ]]; then
                        attachment_count+=1
                        echo "您选择了添加附件"
                        read -rp "请输入您想要添加的附件名称：" attach_name
                        attach_name=$(RemoveDanger "$attach_name")
                        echo "您的附件名称为：$attach_name"
                        read -rp "请输入您想要添加的附件URL：" attach_url
                        # 对于URL，我们使用不同的转义策略
                        attach_url=$(RemoveDanger "$attach_url" "[\"'\.\*;]")
                        echo "您的附件URL为：$attach_url"
                        query_insert_attach="insert into attachment(name, url) value (\"$attach_name\", \"$attach_url\")"
                        query_insert_attach_to="insert into attach_to(aid, uid) value (last_insert_id(), $iid)"
                        attach_id=$($mysql_prefix -se "set autocommit=0;$query_insert_attach;select last_insert_id();$query_insert_attach_to;commit;set autocommit=1;")
                        echo "您刚刚添加的附件ID为：$attach_id"
                    else
                        break
                    fi
                done

                echo "您刚刚对课程号为$cid的课程发布了如下的${target}："
                query_course_info="select I.id 公告ID, I.content 公告内容, I.release_time 公告发布时间 from (info I join course C on I.cid=C.id) where I.id=$iid;"
                query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$iid"
                $mysql_prefix -e "$query_course_info;"

                PrintAttachment

                break
                ;;
            2)
                echo "您选择了删除已发布的${target}"
                if [ ${#iids[@]} -eq 0 ]; then
                    echo "本门课程还没有已发布的${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要删除的${target}ID：" iid
                    [[ "${iids[@]}" =~ "${iid}" ]] && break
                    echo "您输入的${target}ID$iid有误，请输入上表中列举出的某个${target}ID"
                done
                query_delete_content="delete from content where id=$iid"
                $mysql_prefix -e "$query_delete_content;"
                break
                ;;
            3)
                echo "您选择了修改已发布的${target}"
                if [ ${#iids[@]} -eq 0 ]; then
                    echo "本门课程还没有已发布的${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要修改的${target}ID：" iid
                    [[ "${iids[@]}" =~ "${iid}" ]] && break
                    echo "您输入的${target}ID$iid有误，请输入上表中列举出的某个${target}ID"
                done

                echo "您选择了修改以下的${target}："
                query_course_info="select I.id 公告ID, I.content 公告内容, I.release_time 公告发布时间 from (info I join course C on I.cid=C.id) where I.id=$iid;"
                query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$iid"
                query_count_attachment="select count(1) from attachment join attach_to on id=aid where uid=$iid"
                $mysql_prefix -e "$query_course_info;"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                PrintAttachment

                echo "请输入${target}的新内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的新${target}内容为\n$full_string"

                query_insert_info="update info set content=\"$full_string\" where id=$iid"

                $mysql_prefix -se "$query_insert_info;"

                echo "您刚刚修改的${target}ID为：$iid"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                while :; do
                    read -rp "请输入您是否需要为${target}添加新的附件（Y/n）：" need_attach
                    if [[ $need_attach =~ ^[1Yy] ]]; then
                        echo "您选择了添加附件"
                        read -rp "请输入您想要添加的附件名称：" attach_name
                        attach_name=$(RemoveDanger "$attach_name")
                        echo "您的附件名称为：$attach_name"
                        read -rp "请输入您想要添加的附件URL：" attach_url
                        # 对于URL，我们使用不同的转义策略
                        attach_url=$(RemoveDanger "$attach_url" "[\"'\.\*;]")
                        echo "您的附件URL为：$attach_url"
                        query_insert_attach="insert into attachment(name, url) value (\"$attach_name\", \"$attach_url\")"
                        query_insert_attach_to="insert into attach_to(aid, uid) value (last_insert_id(), $iid)"
                        attach_id=$($mysql_prefix -se "set autocommit=0;$query_insert_attach;select last_insert_id();$query_insert_attach_to;commit;set autocommit=1;")
                        echo "您刚刚添加的附件ID为：$attach_id"
                    else
                        break
                    fi
                done

                echo "您刚刚对课程号为$cid的课程发布了如下的${target}："
                $mysql_prefix -e "$query_course_info;"

                PrintAttachment

                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function TeacherManageStudent() {
    while :; do
        target="$Green学生$NoColor"
        PrintTeacher

        query_sid="select sid from take where cid=$cid"
        query_student="select id 学生学号, name 学生姓名 from student where id in ($query_sid)"
        sids=($($mysql_prefix -e "$query_sid;"))
        if [ ${#sids[@]} -gt 0 ]; then
            echo "选上这门课的$target们有："
            $mysql_prefix -e "$query_student;"
        else
            echo "没有$target选上这门课"
        fi
        echo "您可以进行的操作有："
        echo "1. 向课程名单中添加$target"
        echo "2. 从课程名单中移除$target"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了对课程导入新的$target账户"
                query_all_sids="select id from student where id not in ($query_sid)"
                query_all_students="select id 学号, name 姓名 from student where id not in ($query_sid)"
                all_sids=($($mysql_prefix -se "$query_all_sids;"))
                echo "没有被导入该课程但是已经注册的$target有："
                $mysql_prefix -e "$query_all_students;"
                while :; do
                    read -rp "请输入您想要添加的$target学号：" sid
                    [[ "${all_sids[@]}" =~ "${sid}" ]] && break
                    echo "您输入的学号$sid有误，请输入上表中列举出的某个$target的学号"
                done
                echo "您选择了将下列$target添加进课程名单："
                query_student_info="select id 学号, name 姓名 from student where id=$sid"
                $mysql_prefix -e "$query_student_info;"
                read -rp "是否要添加（Y/n）：" need_insert_student_course
                if [[ $need_insert_student_course =~ ^[1Yy] ]]; then
                    query_insert_student_course="insert into take(sid, cid) value ($sid, $cid)"
                    $mysql_prefix -e "$query_insert_student_course;"
                fi
                break
                ;;
            2)
                echo "您选择了从课程名单中移除$target"
                if [ ${#sids[@]} -eq 0 ]; then
                    echo "本门课程还没有$target选上"
                    break
                fi
                while :; do
                    read -rp "请输入您想要删除的$target学号：" sid
                    [[ "${sids[@]}" =~ "${sid}" ]] && break
                    echo "您输入的学号$sid有误，请输入上表中列举出的某个$target的学号"
                done
                echo "您选择了将下列$target从课程名单中移除："
                query_student_info="select id 学号, name 姓名 from student where id=$sid"
                $mysql_prefix -e "$query_student_info;"
                read -rp "是否要移除（Y/n）：" need_delete_student_course
                if [[ $need_delete_student_course =~ ^[1Yy] ]]; then
                    echo "正在删除...$sid from $cid"
                    query_delete_student_course="delete from take where sid=$sid and cid=$cid"
                    query_delete_student_attach_to="delete from attach_to where uid in (select id from submission where sid=$sid and hid in (select id from homework where cid=$cid))"
                    query_delete_student_submission="delete from submission where sid=$sid and hid in (select id from homework where cid=$cid)"
                    $mysql_prefix -e "set autocommit=0;$query_delete_student_course;$query_delete_student_attach_to;$query_delete_student_submission;commit;set autocommit=1;"
                fi
                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function TeacherManageHomework() {
    while :; do
        PrintTeacher

        target="$Green课程作业/实验$NoColor"
        query_hid="select id from homework where cid=$cid"
        query_hw="select id 作业ID, intro 作业简介, creation_time 作业发布时间, end_time 作业截止时间 from homework where cid=$cid"

        hids=($($mysql_prefix -e "$query_hid;"))
        if [ ${#hids[@]} -gt 0 ]; then
            echo "本课程已有的${target}如下图所示"
            $mysql_prefix -e "$query_hw;"
        else
            echo "本课程还没有已发布的$target"
        fi

        echo "您可以进行的操作有："
        echo "1. 发布新的${target}"
        echo "2. 删除已发布的${target}"
        echo "3. 修改已发布的${target}"
        echo "4. 查看已发布的${target}的完成情况"
        echo "0. 返回上一级"

        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了发布新的${target}"
                echo "请输入课程实验的简介内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的${target}的简介内容为\n$full_string"

                read -rp "请输入您想要创建的是作业还是实验（H/E）：" h_or_e
                [[ $h_or_e =~ ^[Hh] ]] && h_or_e="H" || h_or_e="E"

                while :; do
                    read -rp "请输入作业的持续时间（天）：" days
                    [[ $days =~ ^[0-9]+$ ]] && break || echo "请输入整数"
                done

                # 由于我们需要保证在Content中与其他具体类型中的标号相同，我们使用Commit
                query_insert_content="insert into content value ()"
                query_insert_hw="insert into homework(id, cid,tid,intro,creation_time,end_time) value (last_insert_id(),$cid,$tid,\"$full_string\",now(),from_unixtime($(expr $(date +%s) + "$days" '*' 86400)))"

                hid=$($mysql_prefix -se "set autocommit=0;$query_insert_content;select last_insert_id();$query_insert_hw;commit;set autocommit=1;")

                echo "您刚刚添加的${target}ID为：$hid"
                attachment_count=0
                while :; do
                    read -rp "请输入您是否需要为${target}添加附件（Y/n）：" need_attach
                    if [[ $need_attach =~ ^[1Yy] ]]; then
                        attachment_count+=1
                        echo "您选择了添加附件"
                        read -rp "请输入您想要添加的附件名称：" attach_name
                        attach_name=$(RemoveDanger "$attach_name")
                        echo "您的附件名称为：$attach_name"
                        read -rp "请输入您想要添加的附件URL：" attach_url
                        # 对于URL，我们使用不同的转义策略
                        attach_url=$(RemoveDanger "$attach_url" "[\"'\.\*;]")
                        echo "您的附件URL为：$attach_url"
                        query_insert_attach="insert into attachment(name, url) value (\"$attach_name\", \"$attach_url\")"
                        query_insert_attach_to="insert into attach_to(aid, uid) value (last_insert_id(), $hid)"
                        attach_id=$($mysql_prefix -se "set autocommit=0;$query_insert_attach;select last_insert_id();$query_insert_attach_to;commit;set autocommit=1;")
                        echo "您刚刚添加的附件ID为：$attach_id"
                    else
                        break
                    fi
                done

                echo "您刚刚对课程号为$cid的课程发布了如下的${target}："
                query_course_homework="select H.id \`作业/实验ID\`, H.intro \`作业/实验简介\`, H.creation_time 创建时间, H.end_time 结束时间 from homework H where H.id=$hid"
                query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$hid"
                $mysql_prefix -e "$query_course_homework;"

                PrintAttachment

                break
                ;;
            2)
                echo "您选择了删除已发布的${target}"
                if [ ${#hids[@]} -eq 0 ]; then
                    echo "本门课程还没有已发布的${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要删除的${target}ID：" hid
                    [[ "${hids[@]}" =~ "${hid}" ]] && break
                    echo "您输入的${target}ID$hid有误，请输入上表中列举出的某个${target}ID"
                done
                # query_delete_attach_to="delete from attach_to where uid=$hid"
                # query_delete_submission="delete from submission where hid=$hid"
                # query_delete_homework="delete from homework where id=$hid"
                query_delete_content="delete from content where id=$hid"
                # $mysql_prefix -e "set autocommit=0;$query_delete_attach_to;$query_delete_submission;$query_delete_homework;$query_delete_content;commit;set autocommit=1;"
                $mysql_prefix -e "$query_delete_content;"

                break
                ;;
            3)
                echo "您选择了修改已发布的${target}"
                if [ ${#hids[@]} -eq 0 ]; then
                    echo "本门课程还没有已发布的${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要修改的${target}ID：" hid
                    [[ "${hids[@]}" =~ "${hid}" ]] && break
                    echo "您输入的${target}ID$hid有误，请输入上表中列举出的某个${target}ID"
                done

                echo "您选择了修改以下的${target}："
                query_course_homework="select id \`作业/实验ID\`, intro \`作业/实验简介\`, creation_time 创建时间, end_time 截止时间 from homework where id=$hid"
                query_attachment="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$hid"
                query_count_attachment="select count(1) from attachment join attach_to on id=aid where uid=$hid"
                $mysql_prefix -e "$query_course_homework;"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                PrintAttachment

                echo "请输入${target}简介的新内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的新${target}简介内容为\n$full_string"

                query_insert_homework="update homework set intro=\"$full_string\" where id=$hid"

                $mysql_prefix -se "$query_insert_homework;"

                while :; do
                    read -rp "请输入作业的持续时间（天）：" days
                    [[ $days =~ ^[0-9]+$ ]] && break || echo "请输入整数"
                done

                query_get_start_time="select unix_timestamp(creation_time) from homework where id=$hid"
                creation_time=$($mysql_prefix -se "$query_get_start_time;")
                query_update_end_time="update homework set end_time=from_unixtime($(expr "$creation_time" + "$days" '*' 86400)) where id=$hid"
                $mysql_prefix -e "$query_update_end_time;"

                echo "您刚刚修改的课程${target}ID为：$hid"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                while :; do
                    read -rp "请输入您是否需要为课程${target}添加新的附件（Y/n）：" need_attach
                    if [[ $need_attach =~ ^[1Yy] ]]; then
                        echo "您选择了添加附件"
                        read -rp "请输入您想要添加的附件名称：" attach_name
                        attach_name=$(RemoveDanger "$attach_name")
                        echo "您的附件名称为：$attach_name"
                        read -rp "请输入您想要添加的附件URL：" attach_url
                        # 对于URL，我们使用不同的转义策略
                        attach_url=$(RemoveDanger "$attach_url" "[\"'\.\*;]")
                        echo "您的附件URL为：$attach_url"
                        query_insert_attach="insert into attachment(name, url) value (\"$attach_name\", \"$attach_url\")"
                        query_insert_attach_to="insert into attach_to(aid, uid) value (last_insert_id(), $hid)"
                        attach_id=$($mysql_prefix -se "set autocommit=0;$query_insert_attach;select last_insert_id();$query_insert_attach_to;commit;set autocommit=1;")
                        echo "您刚刚添加的附件ID为：$attach_id"
                    else
                        break
                    fi
                done

                echo "您刚刚对课程号为$cid的课程发布了如下的课程${target}："
                $mysql_prefix -e "$query_course_homework;"

                PrintAttachment

                break
                ;;
            4)
                echo "您选择了查看已发布的${target}的完成情况"
                if [ ${#hids[@]} -eq 0 ]; then
                    echo "本门课程还没有已发布的${target}"
                    break
                fi
                while :; do
                    read -rp "请输入您想要查看的${target}ID：" hid
                    [[ "${hids[@]}" =~ "${hid}" ]] && break
                    echo "您输入的${target}ID$hid有误，请输入上表中列举出的某个${target}ID"
                done

                query_sid="select sid from take where cid=$cid"
                query_finish="select stu.id 学生学号, stu.name 学生姓名, if(count(sub.id)>0,\"是\",\"否\") 是否完成, count(sub.id) 创建的提交数目 from (select * from submission where hid=$hid) sub right join (select * from student where id in ($query_sid)) stu on sub.sid=stu.id group by stu.id"

                $mysql_prefix -e "$query_finish"

                # insert into submission value (null,1,1,6,"就是一个测试辣",now(),now());

                while :; do
                    read -rp "请输入您是否需要查询完成情况（Y/n）：" check_finish
                    if [[ $check_finish =~ ^[1Yy] ]]; then
                        read -rp "请输入您要查询完成情况的学号：" sid
                        query_finish_sid="$query_finish having stu.id=$sid"
                        $mysql_prefix -e "$query_finish_sid"
                    else
                        break
                    fi
                done

                break
                ;;
            0)
                echo "您选择了返回上一级"
                return 0
                ;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
                ;;
            esac
        done
    done
}

function RemoveDanger() {
    danger_set="[\"'\.\*;%]"
    [ ${#2} -gt 0 ] && danger_set=$2
    danger=$1
    safe=""
    for i in $(seq ${#danger}); do
        thechar="${danger:$i-1:1}"
        if [[ "$thechar" =~ $danger_set ]]; then
            # echo "$thechar"
            safe="$safe"'\'"$thechar"
        else
            safe="$safe$thechar"
        fi
    done
    echo "$safe"
}

function LoginInUI() {
    while :; do
        PrintBanner
        while :; do
            read -rp "请输入您的身份（T/S/A）或输入0退出系统：" identity
            case $identity in
            [Tt])
                identity="teacher"
                break
                ;;
            [Ss])
                identity="student"
                break
                ;;
            [Aa])
                identity="admin"
                break
                ;;
            0)
                echo "再见！祝您生活愉快。"
                exit 0
                ;;
            *) echo "请输入T, S, A或0" ;;
            esac
        done
        while :; do
            read -rp "请输入您的登陆账号：" user_id
            user_id=$(RemoveDanger "$user_id")
            query_all_hash="select id, name, password_hash from $identity"
            query_right_hash="select password_hash from ($query_all_hash) all_hash where id=\"$user_id\""
            right_hash=$($mysql_prefix -se "$query_right_hash;")
            [ -z "$right_hash" ] || break
            echo "用户不存在，请重新输入"
        done
        while :; do
            read -rp "请输入您的密码：" -s password
            echo ""
            password_hash=$(echo "$password" | sha256sum - | tr -d "[ \-]")
            [ "$password_hash" = "$right_hash" ] && break
            echo "验证失败，请重新输入"
        done
        echo "验证成功"
        query_name="select name from $identity where id=$user_id"
        name=$($mysql_prefix -se "$query_name")
        case $identity in
        "teacher")
            TeacherUI "$user_id" "$name"
            ;;
        "student")
            StudentUI "$user_id" "$name"
            ;;

        "admin") ;;

        esac
    done
}

DefineColor
DefineMySQL
LoginInUI
