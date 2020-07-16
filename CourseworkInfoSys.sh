#!/bin/bash
# 这是一个现代教务管理系统，主要面向作业管理
# 我们通过编写Shell程序来管理作业数据库

mysql_u="ShellDesigner"
mysql_p="ShellDesigner"
mysql_h="localhost"
mysql_d="ShellDesign"
mysql_f=".mysql.cnf"
# rm -rf $mysql_f
echo "[client]" >$mysql_f
echo "user=$mysql_u" >>$mysql_f
echo "password=$mysql_p" >>$mysql_f
echo "host=$mysql_h" >>$mysql_f

mysql_prefix="mysql --defaults-extra-file=$mysql_f $mysql_d"

TeacherUI() {
    # login informations
    name="zy"
    tid=1

    while :; do
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
                    echo "您本学期没有课程，再见！"
                    exit 0
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

TeacherOPCourse() {
    while :; do
        query_tid="select tid from teach where cid=$cid"
        query_teacher="select id 教师工号, name 教师姓名 from teacher where id in ($query_tid)"

        echo "您选择的课程为："
        $mysql_prefix -e "select id 课程号, name_zh 中文名称, name_en 英文名称 from course where id=$cid;"

        tids=($($mysql_prefix -e "$query_tid and tid <> $tid;"))
        if [ ${#tids[@]} -gt 0 ]; then
            echo "与您一同教这门课的老师有："
            $mysql_prefix -e "$query_teacher and id <> $tid;"
        fi

        # ops=(1 2 3)
        echo "您可以进行的操作有："
        echo "1. 管理修读课程的学生"
        echo "2. 管理课程作业/实验"
        echo "3. 管理本课程信息（管理公告/简介等）"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            # [[ "${ops[@]}" =~ "${op}" ]] && break
            # echo "您选择了操作：$op"
            case $op in
            1)
                echo "您选择了管理修读该课程的学生"
                TeacherManageStudent
                break
                ;;
            2)
                echo "您选择了管理本课程的实验和作业"
                TeacherManageHomework
                break
                ;;
            3)
                echo "您选择了管理本课程的公告/信息"
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

TeacherManageCourse() {
    # ops=(1 2)
    while :; do
        echo "您可以进行的操作有："
        echo "1. 管理课程公告"
        echo "2. 修改课程简介"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            # [[ "${ops[@]}" =~ "${op}" ]] && break
            # echo "您选择了操作：$op"
            case $op in
            1)
                echo "您选择了管理课程公告"
                TeacherManageCourseInfo
                break
                ;;
            2)
                echo "您选择了修改课程简介"
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

TeacherManageCourseBrief() {
    echo "课程简介的原内容为"
    $mysql_prefix -e "select brief 课程简介 from course where id=$cid"
    echo "请输入课程简介的新内容，以EOF结尾（换行后Ctrl+D）"
    full_string=""
    while read -r temp; do
        full_string+="$temp"$'\n'
    done

    full_string=$(RemoveDanger "$full_string")

    echo -e "您的新课程简介内容为\n$full_string"
    query_brief_update="update course set brief = \"$full_string\" where id=$cid"
    # 我们增加了字符串处理函数以减少受到SQL注入攻击的可能性。
    # we can easily perfomr SQL injection if the string is not carefully treated
    # update course set brief = "Hello, world.";select * from admin;\" where id=$cid
    $mysql_prefix -e "$query_brief_update;"
}

TeacherManageCourseInfo() {
    while :; do
        query_iid="select id from info where cid=$cid"
        query_info="select I.id 公告ID, release_time 公告发布时间, content 公告内容 from info I join course C on I.cid = C.id where I.cid in ($query_iid)"

        iids=($($mysql_prefix -e "$query_iid;"))
        if [ ${#iids[@]} -gt 0 ]; then
            echo "本课程已有的课程公告如下图所示"
            $mysql_prefix -e "$query_info;"
        fi

        echo "您可以进行的操作有："
        echo "1. 发布新的课程公告"
        echo "2. 删除已发布的课程公告"
        echo "3. 修改已发布的课程公告"
        echo "0. 返回上一级"

        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了发布新的课程公告"
                echo "请输入课程公告的新内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的新课程公告内容为\n$full_string"

                # 由于我们需要保证在Content中与其他具体类型中的标号相同，我们使用Commit
                query_insert_content="insert into content value ()"
                query_insert_info="insert into info(id, content, cid, release_time) value (last_insert_id(), \"$full_string\", $cid, now())"

                iid=$($mysql_prefix -se "set autocommit=0;$query_insert_content;select last_insert_id();$query_insert_info;commit;set autocommit=1;")

                echo "您刚刚发布的课程公告ID为：$iid"
                attachment_count=0
                while :; do
                    read -rp "请输入您是否需要为课程公告添加附件（Y/n）：" need_attach
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

                echo "您刚刚对课程号为$cid的课程发布了如下的课程公告："
                query_course_info="select I.id 公告ID, I.content 公告内容, I.release_time 公告发布时间 from (info I join course C on I.cid=C.id) where I.id=$iid;"
                query_attachment_info="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$iid"
                $mysql_prefix -e "$query_course_info;"

                if [ $attachment_count -gt 0 ]; then
                    echo "本公告的附件包括："
                    $mysql_prefix -e "$query_attachment_info;"
                fi

                break
                ;;
            2)
                echo "您选择了删除已发布的课程公告"
                while :; do
                    read -rp "请输入您想要删除的公告ID：" iid
                    [[ "${iids[@]}" =~ "${iid}" ]] && break
                    echo "您输入的公告ID$iid有误，请输入上表中列举出的某个公告ID"
                done
                query_delete_info="delete from info where id=$iid"
                $mysql_prefix -e "$query_delete_info"
                break
                ;;
            3)
                echo "您选择了修改已发布的"
                while :; do
                    read -rp "请输入您想要修改的公告ID：" iid
                    [[ "${iids[@]}" =~ "${iid}" ]] && break
                    echo "您输入的公告ID$iid有误，请输入上表中列举出的某个公告ID"
                done

                echo "您选择了修改以下的公告："
                query_course_info="select I.id 公告ID, I.content 公告内容, I.release_time 公告发布时间 from (info I join course C on I.cid=C.id) where I.id=$iid;"
                query_attachment_info="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$iid"
                query_count_attachment="select count(1) from attachment join attach_to on id=aid where uid=$iid"
                $mysql_prefix -e "$query_course_info;"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                if [ "$attachment_count" -gt 0 ]; then
                    echo "本公告的附件包括："
                    $mysql_prefix -e "$query_attachment_info;"
                fi

                echo "请输入课程公告的新内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的新课程公告内容为\n$full_string"

                query_insert_info="update info set content=\"$full_string\" where id=$iid"

                $mysql_prefix -se "$query_insert_info;"

                echo "您刚刚修改的课程公告ID为：$iid"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                while :; do
                    read -rp "请输入您是否需要为课程公告添加新的附件（Y/n）：" need_attach
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

                echo "您刚刚对课程号为$cid的课程发布了如下的课程公告："
                $mysql_prefix -e "$query_course_info;"

                if [ $attachment_count -gt 0 ]; then
                    echo "本公告的附件包括："
                    $mysql_prefix -e "$query_attachment_info;"
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

TeacherManageStudent() {
    # ops=(1 2)
    while :; do
        query_sid="select sid from take where cid=$cid"
        query_student="select id 学生学号, name 学生姓名 from student where id in ($query_sid)"
        sids=($($mysql_prefix -e "$query_sid;"))
        if [ ${#sids[@]} -gt 0 ]; then
            echo "选上这门课的同学们有："
            $mysql_prefix -e "$query_student;"
        fi
        echo "您可以进行的操作有："
        echo "1. 向课程名单中添加学生"
        echo "2. 从课程名单中移除学生"
        echo "0. 返回上一级"
        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了对课程导入新的学生账户"
                query_all_sids="select id from student where id not in ($query_sid)"
                query_all_students="select id 学号, name 姓名 from student where id not in ($query_sid)"
                all_sids=($($mysql_prefix -se "$query_all_sids;"))
                echo "没有被导入该课程但是已经注册的学生有："
                $mysql_prefix -e "$query_all_students;"
                while :; do
                    read -rp "请输入您想要添加的学生学号：" sid
                    [[ "${all_sids[@]}" =~ "${sid}" ]] && break
                    echo "您输入的学号$sid有误，请输入上表中列举出的某个学生的学号"
                done
                echo "您选择了将下列学生添加进课程名单："
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
                echo "您选择了从课程名单中移除学生"
                while :; do
                    read -rp "请输入您想要删除的学生学号：" sid
                    [[ "${sids[@]}" =~ "${sid}" ]] && break
                    echo "您输入的学号$sid有误，请输入上表中列举出的某个学生的学号"
                done
                echo "您选择了将下列学生从课程名单中移除："
                query_student_info="select id 学号, name 姓名 from student where id=$sid"
                $mysql_prefix -e "$query_student_info;"
                read -rp "是否要移除（Y/n）：" need_remove_student_course
                if [[ $need_remove_student_course =~ ^[1Yy] ]]; then
                    query_remove_student_course="delete from take where sid=$sid and cid=$cid"
                    $mysql_prefix -e "$query_remove_student_course;"
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

TeacherManageHomework() {
        while :; do
        query_hid="select id from homework where cid=$cid"
        query_hw="select H.id 作业ID, intro 作业简介, creation_time 作业发布时间 from homework H join course C on H.cid = C.id where I.cid in ($query_hid)"

        hids=($($mysql_prefix -e "$query_hid;"))
        if [ ${#hids[@]} -gt 0 ]; then
            echo "本课程已有的课程作业/实验如下图所示"
            $mysql_prefix -e "$query_hw;"
        fi

        echo "您可以进行的操作有："H
        echo "1. 发布新的课程作业/实验"
        echo "2. 删除已发布的课程作业/实验"
        echo "3. 修改已发布的课程作业/实验"
        echo "0. 返回上一级"

        while :; do
            read -rp "请输入您想要进行的操作：" op
            case $op in
            1)
                echo "您选择了发布新的课程作业/实验"
                echo "请输入课程实验的简介内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的课程实验的简介内容为\n$full_string"

                read -rp "请输入您想要创建的是作业还是实验（H/E）：" h_or_e
                [[ $h_or_e =~ ^[Hh] ]] && h_or_e="H" || h_or_e="E"

                while : ;do
                    read -rp "请输入作业的持续时间（天）：" days
                    [[ $days =~ ^[0-9]+$ ]] && break || echo "请输入整数"
                done

                # 由于我们需要保证在Content中与其他具体类型中的标号相同，我们使用Commit
                query_insert_content="insert into content value ()"
                query_insert_hw="insert into homework(cid,tid,intro,creation_time,end_time) value ($cid,$tid,\"$full_string\",now(),from_unixtime($(expr $(date +%s) + "$days" '*' 86400)))"

                hid=$($mysql_prefix -se "set autocommit=0;$query_insert_content;select last_insert_id();$query_insert_hw;commit;set autocommit=1;")

                echo "您刚刚添加的课程作业/实验ID为：$hid"
                attachment_count=0
                while :; do
                    read -rp "请输入您是否需要为课程公告添加附件（Y/n）：" need_attach
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

                echo "您刚刚对课程号为$cid的课程发布了如下的课程公告："
                query_course_info="select I.id 公告ID, I.content 公告内容, I.release_time 公告发布时间 from (info I join course C on I.cid=C.id) where I.id=$iid;"
                query_attachment_info="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$iid"
                $mysql_prefix -e "$query_course_info;"

                if [ $attachment_count -gt 0 ]; then
                    echo "本公告的附件包括："
                    $mysql_prefix -e "$query_attachment_info;"
                fi

                break
                ;;
            2)
                echo "您选择了删除已发布的课程公告"
                while :; do
                    read -rp "请输入您想要删除的公告ID：" iid
                    [[ "${iids[@]}" =~ "${iid}" ]] && break
                    echo "您输入的公告ID$iid有误，请输入上表中列举出的某个公告ID"
                done
                query_delete_info="delete from info where id=$iid"
                $mysql_prefix -e "$query_delete_info"
                break
                ;;
            3)
                echo "您选择了修改已发布的"
                while :; do
                    read -rp "请输入您想要修改的公告ID：" iid
                    [[ "${iids[@]}" =~ "${iid}" ]] && break
                    echo "您输入的公告ID$iid有误，请输入上表中列举出的某个公告ID"
                done

                echo "您选择了修改以下的公告："
                query_course_info="select I.id 公告ID, I.content 公告内容, I.release_time 公告发布时间 from (info I join course C on I.cid=C.id) where I.id=$iid;"
                query_attachment_info="select A.id 附件ID, A.name 附件名称, A.url 附件URL from attachment A join attach_to T on A.id=T.aid where T.uid=$iid"
                query_count_attachment="select count(1) from attachment join attach_to on id=aid where uid=$iid"
                $mysql_prefix -e "$query_course_info;"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                if [ "$attachment_count" -gt 0 ]; then
                    echo "本公告的附件包括："
                    $mysql_prefix -e "$query_attachment_info;"
                fi

                echo "请输入课程公告的新内容，以EOF结尾（换行后Ctrl+D）"
                full_string=""
                while read -r temp; do
                    full_string+="$temp"$'\n'
                done

                full_string=$(RemoveDanger "$full_string")

                echo -e "您的新课程公告内容为\n$full_string"

                query_insert_info="update info set content=\"$full_string\" where id=$iid"

                $mysql_prefix -se "$query_insert_info;"

                echo "您刚刚修改的课程公告ID为：$iid"
                attachment_count=$($mysql_prefix -se "$query_count_attachment")
                while :; do
                    read -rp "请输入您是否需要为课程公告添加新的附件（Y/n）：" need_attach
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

                echo "您刚刚对课程号为$cid的课程发布了如下的课程公告："
                $mysql_prefix -e "$query_course_info;"

                if [ $attachment_count -gt 0 ]; then
                    echo "本公告的附件包括："
                    $mysql_prefix -e "$query_attachment_info;"
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

RemoveDanger() {
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

TeacherUI

rm -rf $mysql_f
