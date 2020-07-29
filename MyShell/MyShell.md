# MyShell：跨平台简单Shell程序

## 基本信息

- 课程名称：Linux程序设计

- 实验项目名称：Shell命令

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
  - [ ] ==添加MacOS系统信息==
  - 系统命令有很大不同，但Shell可以基本正常运行的系统有：
  - `DESKTOP-XUZH Microsoft Windows 10 Pro 10.0.18363 N/A Build 18363`
  - 遗憾的是，我们没有经历测试全部的Python版本和所有可能的系统环境，但我们合理推断，在一般的`*nix`环境和`Python 3`下，MyShell都可以正常运行。在Windows环境下，MyShell的基本功能也可正常工作。

## 需求描述

### 设计文档

shell 或者命令行解释器是操作系统中最基本的用户接口。我们实现了一个跨平台的简单的shell 程序——**MyShell**，它具有以下属性：

1. 支持的内部指令集：`cd, clr, pwd, dir, echo, exit, quit, jobs, fg, bg, term, environ, set, unset, umask, printio, exec, shift, test, sleep, time, help, verbose`

   开发者调试指令集：`dummy, check_zombie, queue`

   - `cd`

     更改工作目录

     `cd [target]`

     - 无参数调用时会打印当前工作目录
     - 传入一个参数调用时会尝试进入参数所示的目录
     - 在各平台上都可正常使用
     - 无法进入不存在的目录/或根本不是目录的路径/没有权限进入的路径

   - `clr`

     清空屏幕

     `clr`

     - 本指令没有参数
     - 本指令需要调用系统相关命令以管理终端屏幕

   - `pwd`

     打印当前工作目录

     `pwd [-a]`

     - 无参数调用时会打印当前工作目录，用户根目录以`~`显示
     - 传入参数`-a`调用时会打印当前工作目录完整路径

   - `dir`

     列举文件夹内容

     `dir [target [target ...]]`

     - 无参数调用时会显示当前目录下的文件列表
     - 传入多个目录时会依次显示目录的列举结果，结果中多个目录间以空行分隔
     - 对于每个目录，结果的第一行是下面将要现实的目录路径
     - 普通文件加粗显示，可执行文件以红色粗体显示，目录以蓝色粗体显示
     - 目录中的文件列表前以`rwxrwxrwx`格式显示文件/目录权限
     - 目录中的文件列表前显示的时间是最近修改时间
     - 若用户参数中有无法显示的目录（不存在/非目录/无权限等），会导致程序运行错误，此时将无法使用管道，但我们会打印出可以显示的那些目录的内容。

   - `echo`

     打印内容

     `echo [-r] [content [content ...]]`

     - 无参数调用时会打印空字符串
     - 传入多个参数（除了开头的`-r`）时会用空格分隔它们，并打印
     - 传入的参数可以通过双引号包裹，被包裹的内容被视为一个整体
     - 参数中可以包含`~`字符，会被替换为用户的根目录
     - 参数中可以包含`$...`代表的变量，会被替换为相应的变量值，变量不存在时替换为空字符串
     - 引号可以用于区分变量和普通内容，例如`echo PATH_TO_SHELL"$SHELL"SOME_STRING`只有一个参数，但是变量`$SHELL`会被正确处理
     - 若要打印`$`符号，请输入`\$`以转义
     - 若要打印`~`符号，请输入`\~`以转义
     - 不采用`-r`开关时，会尝试转义传入字符中的可转义内容，例如调用`echo "\033[1m\033[31mHello, world.\033[0m"`会以红色粗体打印`Hello, world.`
     - 加入`-r`参数后，上面的命令会以普通字体打印`\033[1m\033[31mHello, world.\033[0m`

   - `exit`

     退出MyShell

     `exit`

     - 我们不会处理任何参数，因为MyShell是一个Python Object，所以没有系统返回值的概念
     - 通过调用`exit/quit/EOF`退出是最安全的退出方式，因为这种情况下MyShell会有机会清空还没有结束的后台工作

   - `quit`

     同`exit`

   - `jobs`

     打印当前任务信息

     `jobs`

     - 我们不会处理任何参数
     - 后台任务的格式为`[i] status env command`例如`[0] suspended env dummy &`
     - 已经被清除/已经完成的任务不会被显示
     - 尝试读取内容的外部后台程序会直接获得EOF
  - 任务信息是管理性质的信息，所以我们会忽略`exec`命令的设置，将任务管理结果直接打印到屏幕上
   
- `fg`
   
  将后台任务提到前台执行
   
  `fg job_number`
   
     - 只接受一个参数
     - 对于正在执行的后台任务，提到前台运行
     - 通过外部命令的刷出的后台任务仍然不能获取输入，尝试读取内容的外部后台程序会直接获得EOF
  - 对于因为获取输入而暂停执行的命令，继续命令的执行并阻塞前台主线程
   
- `bg`
   
  继续后台程序的执行
   
  `bg [job_number [job_number ...]]`
   
     - 由于所有的暂停的后台任务都是因为尝试获取用户输入，继续在后台执行它们只会得到继续暂停的结果
  - MyShell没有对快捷键操作进行处理，因此没有暂停正在运行的外部命令的功能
   
- `term`
   
  终止后台任务的执行
   
  `term [job_number [job_number ...]]`
   
     - 对于后台任务进程（`multiprocessing.Process`），发出`SIGTERM`信号以终止运行；后台任务会自动处理信号并终止自身运行
  - 若后台任务不是内部命令，会对其子进程发出`SIGKILL`信号以尝试终止运行
   
- `environ`
   
  打印MyShell全部内部变量
   
  `environ`
   
     - MyShell使用了内部的变量处理机制，在系统环境变量上加了一层额外的接口用以满足更严苛的测试环境。
     - `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`是MyShell的保留变量，不能被修改和删除
     
   - `set`
   
     修改环境变量/设置新的环境变量
   
     `set key=value [key=value ...]`
   
     - 键值对以等于号配对，等于号的周围不允许出现空格，否则无法正常赋值
     - `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`是MyShell的保留变量，不能被修改（它们实际上也不存在）
     - 修改`PS1`变量会导致命令提示符的提示符号被修改，其默认值为`$`美元符号
     - 修改`PWD`等不会导致当前目录发生改变，但调用`cd`命令进入别的命令后`PWD`变量就会被修改到目录改变后的地址下
     - 修改`HOME`变量会导致程序处理`~`的方式发生改变
     - 修改`USER`等变量不会对命令提示符样式有影响，但可能会对其他使用到这些变量的程序有影响
     - 修改`PATH`可以改变程序搜索可执行文件的路径
   
   - `unset`
   
     删除环境变量
   
     `unset key [key ...]`
   
     - `0, 1, 2, 3, 4, 5, 6, 7, 8, 9`是MyShell的保留变量，不能被删除（它们实际上也不存在）
     - 删除`PS1`变量会导致命令提示符采用默认值`$`
     - 删除`HOME`变量会导致程序无法正确处理`~`
     - 删除`USER`等变量不会对命令提示符样式有影响，但可能会对其他使用到这些变量的程序有影响
   
   - `umask`
   
     修改程序的`umask`值
   
     `umask [value]`
   
     - 在Windows上修改`umask`的效果较为奇怪
     - 不传入参数的时候会显示当前的`umask`
     - 传入新的`umask`会被尝试以八进制解释，并设置为新的`umask`值
     - Linux上普通文本文件的默认权限是`0o666`，可执行文件为`0o777`
     - 在MyShell修改的`umask`值会影响其后的文件创建
   
   - `printio`
   
     打印当前的输入输出重定向目标
   
     `printio`
   
     - 本命令没有参数
   
     - 本命令会打印当前MyShell的`exec`指令重定向目标
   
     - 例如执行`exec < dummy.mysh > result.out`后调用`printio`会打印
   
       ```shell
       FILE NUMBER OF INPUT FILE: 3, redirecting MyShell input to <_io.TextIOWrapper name='dummy.mysh' mode='r' encoding='utf-8'>
       FILE NUMBER OF INPUT FILE: 4, redirecting MyShell output to <_io.TextIOWrapper name='result.out' mode='w' encoding='utf-8'>
       ```
   
     - 由于`printio`的意义就在于查看当前的重定向路径，我们不会将其输入输出重定向，而是直接打印到屏幕上
   
   - `shift`
   
     管理特殊环境变量`1...9`，移动变量的位置（管理命令行参数）
   
     `shift [shamt]`
   
     - 通过`$0...$9`可以访问脚本/程序执行时候的命令行参数
     - `$0`存储的是当前脚本的路径（脚本模式）/当前MyShell的路径（交互模式）
     - `$0...$9`不可以被修改/删除（他们实际上也不存在于环境变量中）
     - 不带参数时，本命令可以让`$1...$9`获取下一个命令行参数，例如`$1`会获取`$2`的旧值
     - 带参数时，移动一定的数量，例如传入参数1的效果与不传入相同，传入2会使得`$1`获得`$3`的原始值
     - 调用`shift`命令不会修改`$0`的值
     - 用户的参数必须要能够转换成整数类型

```

shell 或者命令行解释器是操作系统中最基本的用户接口。写一个简单的shell 程序——**myshell**，它具有以下属性：

(一)  这个shell 程序必须支持以下内部命令：bg、cd 、clr、dir、echo 、exec 、exit 、environ、fg 、help、jobs 、pwd 、quit、set 、shift 、test 、time 、umask、unset。部分命令解释如下：

1)    cd <directory> ——把当前默认目录改变为<directory>。如果没有<directory>参数，则显示当前目录。如该目录不存在，会出现合适的错误信息。这个命令也可以改变PWD 环境变量。

2)    pwd ——显示当前目录。

3)    time ——显示当前时间

4)    clr ——清屏。

5)    dir <directory> ——列出目录<directory>的内容。

6)    environ ——列出所有的环境变量。

7)    echo <comment> ——在屏幕上显示<comment>并换行（多个空格和制表符可能被缩减为一个空格）。

8)    help ——显示用户手册，并且使用more 命令过滤。

9)    quit ——退出shell。

10)  shell 的环境变量应该包含shell=<pathname>/myshell，其中<pathname>/myshell 是可执行程序shell 的完整路径（不是你的目录下的路径，而是它执行程序的路径）。

(二)  其他的命令行输入被解释为程序调用，shell 创建并执行这个程序，并作为自己的子进程。程序的执行的环境变量包含一下条目：

parent=<pathname>/myshell。

(三)  shell 必须能够从文件中提取命令行输入，例如shell 使用以下命令行被调用：

myshell batchfile 

这个批处理文件应该包含一组命令集，当到达文件结尾时shell 退出。很明显，如果shell 被调用时没有使用参数，它会在屏幕上显示提示符请求用户输入。

(四)  shell 必须支持I/O 重定向，stdin 和stdout，或者其中之一，例如命令行为：

programname arg1 arg2 < inputfile > outputfile 

使用arg1 和arg2 执行程序programname，输入文件流被替换为inputfile，输出文件流被替换为outputfile。

stdout 重定向应该支持以下内部命令：dir、environ、echo、help。

使用输出重定向时，如果重定向字符是>，则创建输出文件，如果存在则覆盖之；如果重定向字符为>>，也会创建输出文件，如果存在则添加到文件尾。

(五)  shell 必须支持后台程序执行。如果在命令行后添加&字符，在加载完程序后需要立刻返回命令行提示符。

(六)  必须支持管道（“|”）操作。

(七)  命令行提示符必须包含当前路径。

```

### 用户手册



## 设计思想



## 功能模块



## 运行结果



## 附录

### 完整源码