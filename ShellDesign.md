# 浙江大学实验报告

## 基本信息

- 课程名称：Linux程序设计

- 实验项目名称：Shell程序设计

- 学生姓名：徐震

- 学号：3180105504

- 专业：计算机科学与技术

- 电子邮件地址：[3180105504@zju.edu.cn](mailto:3180105504@zju.edu.cn)

- 实验日期：2020.07.28

## 实验环境

### 硬件配置

- CPU: `2.6 GHz 6-Core Intel Core i7-9750H`
- GPU: `NVIDIA® GeForce® GTX 1650 and Intel(R) UHD Graphics 630`
- Memory: `16 GB 2666 MHz DDR4`
- Disk: `500 GB Solid State PCI-Express Drive * 2`

### 软件环境

- System: `Microsoft Windows 10, macOS Catalina 10.15.5 dual booting`

- Linux: `WSL2 on Windows 10, VMWare Virtual Machine Ubuntu 18.04, Manjaro USB Boot Disk, Ali Cloud ECS Server CentOS 7`

- 注意：我们会==在VMWare Virtual Machine Ubuntu 18.04上进行绝大多数实验操作（Host: Windows 10）==，如实验过程中使用了其他系统我们会注明。

- 主要实验环境详细配置：

  - 系统内核：`Linux ubuntu 5.3.0-43-generic #36~18.04.2-Ubuntu SMP Thu Mar 19 16:03:35 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux`
  - CPU：`Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz`
  - Memory：`MemTotal 6060516 kB`

- Python 3: 我们使用Python 3来实现MyShell，模拟Shell的简单功能

  - 经过测试的有：

    - `Python 3.8.2`
    - `Python 3.7.6`
    - `Python 3.6.9`
- 经过测试的系统有：

  - `Linux ubuntu 5.4.0-42-generic #46~18.04.1-Ubuntu SMP Fri Jul 10 07:21:24 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux`
  - `Linux aliecs 3.10.0-1127.13.1.el7.x86_64 #1 SMP Tue Jun 23 15:46:38 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux`
  - `macOS Catalina 10.15.5`
  - 系统命令有很大不同，但Shell可以基本正常运行的系统有：
  - `DESKTOP-XUZH Microsoft Windows 10 Pro 10.0.18363 N/A Build 18363`
  - 遗憾的是，我们没有经历测试全部的Python版本和所有可能的系统环境，但我们合理推断，在一般的`*nix`环境和`Python 3`下，MyShell都可以正常运行。在Windows环境下，MyShell的基本功能也可正常工作。

## 实验目的

1. 学习`Bourne shell`的shell脚本的基本概念 
2. 学会shell程序如何执行
3. 通过写脚本，学会编写`Bourne shell`脚本程序的方法 
4. 理解并掌握shell


## 实验要求

本实验在提交实验报告时，需要有下面内容：

- **源程序及详细注释**，源程序开始两行为程序名和作者及学号；
- 每题的源代码以文本内容附在对应题目后面；
- 程序运行结果的截图；
- **程序注释必须要用中文，海外学生除外**
- 第4、5题需要设计文档
- 讨论与心得
- 第1、2题程序中不能使用sed、awk等工具
- 本实验完成后所有源代码（文本格式）同时上传到[拼题A系统](pintia.cn)

## 实验内容/结果及分析

### 1

要求：编写shell 脚本，统计指定目录下的普通文件、子目录及可执行文件的数目，统计该目录下所有普通文件字节数总和，目录的路径名字由参数传入。

### 源程序

```shell
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
```

#### 程序运行结果截图



## 讨论/心得

