#!/bin/bash
# 这是一个现代教务管理系统，主要面向作业管理
# 我们通过编写Shell程序来管理作业数据库

mysql_u="ShellDesigner"
mysql_p="ShellDesigner"
mysql_d="ShellDesign"
TeacherUI()
{
    name="zy"
    tid=1
    query_id="select cid from teach where tid=$tid"
    query_course="select id 课程号, name_zh 中文名称, name_en 英文名称 from course where id in ($query_id)"
    courses=($(mysql -u$mysql_u -p$mysql_p $mysql_d -se "$query_id;" 2>/dev/null))
    
    echo "欢迎来到现代作业管理系统（Modern Coursework Manage System）"
    if [ ${#courses[@]} -eq 0 ]; then
        echo "$name老师您好，您本学期没有课程，再见！"
        exit 0
    fi
    echo "$name老师您好，您本学期共${#courses[@]}有门课程，它们分别为："
    mysql -u$mysql_u -p$mysql_p $mysql_d -e "$query_course;" 2>/dev/null
    while :; do
        read -p "请输入您想要管理的课程号：" cid
        [[ "${courses[@]}" =~ "${cid}" ]] && break
        echo "您输入的课程号$cid有误，请输入上表中列举出的某个课程号"
    done
    query_sid="select sid from take where cid=$cid"
    query_tid="select tid from teach where cid=$cid"
    query_teacher="select id 教师工号, name 教师姓名 from teacher where id in ($query_tid)"
    query_student="select id 学生学号, name 学生姓名 from student where id in ($query_sid)"
    

    echo "您选择的课程为："
    mysql -u$mysql_u -p$mysql_p $mysql_d -e "select id 课程号, name_zh 中文名称, name_en 英文名称 from course where id=$cid;" 2>/dev/null
    
    tids=($(mysql -u$mysql_u -p$mysql_p $mysql_d -e "$query_tid and tid <> $tid;" 2>/dev/null))
    if [ ${#tids[@]} -gt 0 ]; then
        echo "与您一同教这门课的老师有："
        mysql -u$mysql_u -p$mysql_p $mysql_d -e "$query_teacher and id <> $tid;" 2>/dev/null
    fi
    
    sids=($(mysql -u$mysql_u -p$mysql_p $mysql_d -e "$query_sid;" 2>/dev/null))
    if [ ${#sids[@]} -gt 0 ]; then
        echo "选上这门课的同学们有："
        mysql -u$mysql_u -p$mysql_p $mysql_d -e "$query_student;" 2>/dev/null
    fi

    TeacherOP
}

TeacherOP()
{
    # ops=(1 2 3)
    echo "您可以进行的操作有："
    echo "1. 管理修读课程的学生"
    echo "2. 管理课程作业/实验"
    echo "3. 管理本课程（发布公告/信息，修改课程要求等）"
    while :;do
        read -p "请输入您想要进行的操作：" op
        # [[ "${ops[@]}" =~ "${op}" ]] && break
        # echo "您选择了操作：$op"
        case $op in
            1)
                echo "您想要管理学生？"
                break;;
            2)
                echo "您想要管理作业?"
                break;;
            3)
                echo "您想要管理课程?"
                TeacherManageCourse
                break;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
        esac
    done 
}

TeacherManageCourse()
{
    ops=(1 2)
    echo "您可以进行的操作有："
    echo "1. 管理课程公告"
    echo "2. 修改课程简介"
    while :;do
        read -p "请输入您想要进行的操作：" op
        # [[ "${ops[@]}" =~ "${op}" ]] && break
        # echo "您选择了操作：$op"
        case $op in
            1)
                echo "您想要管理课程公告？"
                break;;
            2)
                echo "您想要修改课程简介?"
                break;;
            *)
                echo "您输入的操作$op有误，请输入上面列出的操作"
        esac
    done
}

TeacherManageStudent()
{
    echo "Placeholder"
}

TeacherManageHW()
{
    echo "Placeholder"
}

TeacherUI
