#!python
import os  # 大部分os相关功能来自此包
import io  # 用于构建一个stdin的wrapper以捕捉程序的输入/输出请求
import sys  # 一些系统调用/常数的来源包
import re  # 正则表达式
import time  # 用在builtin_sleep中，针对Windows系统的睡眠操作
import platform  # 获取平台信息
import getpass  # 获取用户信息
import logging  # 用于打印一些详细调试信息
import coloredlogs  # 用于打印带颜色的调试信息
import datetime  # 用于取得时间/日期，用于builtin_time
import readline  # 用于提供人性化的input函数操作，例如输入历史功能等
import subprocess  # 用于刷出/控制子进程
import multiprocessing  # 用于后台程序的运行/管理
import traceback  # 用于打印报错信息的调用堆栈
import argparse  # 用于解释本程序的命令行参数
import codecs  # 用于转义字符串，用于builtin_echo
import signal  # 用于在调用builtin_term后给multiprocessing传递信号
import copy  # 用于复制MyShell以进行multiprocessing和任务管理

from subprocess import Popen, PIPE, STDOUT  # 子进程管理
from multiprocessing import Process, Queue, Pipe, Pool, Manager, Value  # 多进程管理
from COLOR import COLOR  # 颜色信息
from MyShellException import *  # MyShell错误管理
log = logging.getLogger(__name__)

coloredlogs.install(level='DEBUG')  # Change this to DEBUG to see more info.


# a decorator for logging function call
# 装饰器：用于在函数调用之前打印相关信息，有助于调试或检查函数调用记录
def logger(func):
    def wrapper(*args, **kwargs):
        # 本装饰器中我们使用logging模块提供详细信息打印功能
        log.debug(f"CALLING FUNCTION: {COLOR.BOLD(func)}")
        return func(*args, **kwargs)
    return wrapper


# a class decorator that can modify all callable class method with a decorator
# here we use this to log function call of sys.stdin wrapper
# 一个带参数装饰器，用于对类进行修改：为类中的每一个可调用函数添加参数中所示的装饰器
def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:  # there's propably a better way to do this
            if callable(getattr(cls, attr)):
                # 通过批量修改类的内容，避免重复代码，提高拓展性
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


# a dict that logs itself on every getting item operation
# 一个会在调用__get_item__前打印相关信息的函数
class LoggingDict(dict):
    def __getitem__(self, key):
        log.debug(f"GETTING DICT ITEM {COLOR.BOLD(key)}")
        return super().__getitem__(key)


class MyShell:
    def __init__(self, dict_in={}, cmd_args=[]):
        # 所有的内置功能的函数开头都是builtin_
        builtin_prefix = "builtin_"

        # builtins is a simple dict containing functions (not called on access)
        self.builtins = {}
        for key, value in MyShell.__dict__.items():
            if key.startswith(builtin_prefix):
                self.builtins[key[len(builtin_prefix)::]] = value

        # 环境变量，用到了下面将要提到的OnCallDict的功能
        # we're using callable dict to evaluate values on call
        self.vars = MyShell.OnCallDict({
            "SHELL": os.path.abspath(__file__),  # 这个变量无法被修改，是MyShell的辨识信息
            "PWD": self.cwd,  # 这个变量的修改会直接导致cd命令的调用，内容会在名利提示符显示
            "HOME": self.home,  # 这个变量存储着当前用户的根目录，无法修改
            "LOCATION": self.location,  # 这个变量的内容会在命令提示符显示，显示用户额外信息，无法修改
            "USER": self.user,  # 储存使用者用户名，无法修改
            "PATH": self.path,  # 储存path这一特殊环境变量，对它的修改会直接导致系统搜索目录的改变
            "PS1": "$"  # 这一变量储存命令提示符内容，可以被修改
        })

        # 对于命令函参数，我们为了防止写太多重复代码，就使用了picklable_nested类来自动生成相关callable object
        # ! pickle cannot handle nested function, however a simulating callable object is fine
        # 由于Pickle无法处理nested function，我们使用类来实现相关功能
        if not cmd_args:
            cmd_args = [os.path.abspath(__file__)]
        self.cmd_args = cmd_args

        prev_level = coloredlogs.get_level()
        log.debug(f"Logging level is {COLOR.BOLD(prev_level)}")
        # 由于这里会打印一些无用的INFO级别的调试信息（具体原因在于会通过非初始化的方式调用OnCallDict的内部方法）
        coloredlogs.set_level("WARNING")
        for i in range(10):
            self.vars[str(i)] = MyShell.picklable_cmd_args(self, i)
        coloredlogs.set_level(prev_level)

        # update: 我们会在调用多线程/后台执行功能时清空这一部分的变量，能够解决的问题有：
        # 1. queue can only be pass by inheritance
        # 2. cannot pickle weakref object
        # 3. cannot pickle thread lock object
        # 4. for safety purpose, cannot pickle authentification string
        # pickle无法正常处理含有multiprocessing.Manager的object，因此我们不会显示储存这样的变量
        # ! damn strange... when an object has a Manager, multiprocessing refuse to spawn it on Windows
        # self.job_manager = Manager()
        self.jobs = Manager().dict()
        self.status_dict = Manager().dict()
        self.queues = {}
        self.process = {}
        self.subp = None

        # 用于builtin_exec对输入输出的调整
        # None表示从原始输入/输出源接受相关信息
        self.input_file = None
        self.output_file = None

        # 初始化MyShell时可以传入初始环境变量
        for key, value in dict_in.items():
            # user should not be tampering with the vars already defined
            # however we decided not to disturb them
            self.vars[key] = value

        log.debug(f"SHELL var content: {self.vars['SHELL']}")
        log.debug(f"Built in command list: {self.builtins}")
        log.debug("MyShell is instanciated.")

    @property
    def job_counter(self):
        keys = [int(key) for key in self.jobs.keys()]
        count = 0
        while count in keys:
            count += 1
        return str(count)

    # 我们考虑过直接使用系统的环境变量接口，但那样或许就少了很多提前控制功能，跨平台性也不一定会很好
    # 所以MyShell会单独管理自己的变量（这里不一定要称为环境变量）
    # 与MyShell配合使用，用于统一管理环境变量，并与真正的系统环境变量交互的字典
    # 主要功能为，若字典value为可执行内容，则返回执行后的结果

    class OnCallDict(dict):
        unsupported = ["HOME", "USER", "LOCATION", "SHELL"] + [str(i) for i in range(10)]
        reserved = unsupported + ["PATH", "PWD"]

        def __getitem__(self, key):
            value = super().__getitem__(key)

            if callable(value):
                # 对于可调用的字典元素，获取调用后的结果，否则返回原结果
                log.debug(f"Accessing callable dict element: {COLOR.BOLD(key)}")
                return value()
            else:
                log.debug(f"Accessing non-callable dict element: {COLOR.BOLD(key)}")
                return value

        def __setitem__(self, key, value):
            # 由于环境变量的特殊性，我们对一些内容的设定操作进行了特殊处理
            if key not in self:
                # 在初始化时不进行任何特殊处理（配合pickle和copy函数）
                log.debug(f"We might be initializing current shell, setting initial value \"{value}\" to \"{key}\"")
                super().__setitem__(key, value)
            elif key == "PATH":
                # 对于PATH的改变会真的影响当前系统中的环境变量
                # for whatever reason, set this to a string (environment variables are meant to be strings)
                # here we're actually setting the REAL environ so that user can call stuff more conveniently
                # ? or should we
                log.info(f"User set PATH to {COLOR.BOLD(value)}")
                os.environ[key] = str(value)
            elif key == "PWD":
                # 设定PWD环境变量会导致cd操作
                # we're changing dir...
                # ? or should we just set variable
                log.info(f"User set PWD to {COLOR.BOLD(value)}")
                os.chdir(value)
            elif key in MyShell.OnCallDict.unsupported:
                # 对于某些不方便设置的环境变量，我们采取保留操作
                log.warning(f"Sorry, we don't currently support setting \"{key}\", included in {COLOR.BOLD(MyShell.OnCallDict.unsupported)}")
            else:
                super().__setitem__(key, value)

        def __delitem__(self, key):
            if key in MyShell.OnCallDict.reserved:
                log.warning(f"Sorry, we don't currently support deleting \"{key}\", included in {COLOR.BOLD(MyShell.OnCallDict.reserved)}")
                raise ReservedKeyException(f"\"{key}\" is reserved, along with {MyShell.OnCallDict.reserved}")
            else:
                super().__delitem__(key)

    # StdinWrapper是一个继承自io.TextWrapper，是本类型对获取输入的job进行线程暂停的一种方式
    # 我们考虑过直接使用系统调用，但跨平台性会很难保证，因此对于后台外部命令，我们会直接关闭输入PIPE
    @for_all_methods(logger)  # using the full class logging system
    class StdinWrapper(io.TextIOWrapper):
        def __init__(self, queue, count, job, status_dict, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.queue = queue
            self.job = job
            self.status_dict = status_dict
            self.count = count
            self.ok = False

        # 用于修改job状态并打印相关信息
        def job_status(self, status):
            self.status_dict[self.count] = status
            print(f"{COLOR.BOLD(COLOR.YELLOW(f'[{self.count}]'))} {COLOR.BOLD(status)} env {COLOR.BOLD(self.job)}")

        # 将第一次输入阻塞，等待主线程的fg命令
        # there might exists a better way
        def isok(self):
            if not self.ok:
                log.debug("Aha! You want to read something? Wait on!")
                self.job_status("suspended")

                log.debug(f"WHAT IS SELF.STATUS_DICT: {self.status_dict}")
                log.debug(f"WHAT IS SELF.COUNT: {self.count}")

                # queue的功能就是将本线程阻塞
                content = self.queue.get()

                log.debug(f"WHAT DID YOU GET: {content}")

                self.isok = True

                self.job_status("running")

        # 为了方便调试，我们对很多内容的调用都内置了记录器
        def __getattribute__(self, name):
            log.debug(f"GETTING ATTRIBUTE: {COLOR.BOLD(name)}")
            return super().__getattribute__(name)

        def fileno(self):
            self.isok()
            return super().fileno()

    # 以命令提示符方式执行MyShell
    def __call__(self):
        log.debug("This is MyShell.")

        # 通过返回值方式传输退出信号
        exit_signal = False
        while not exit_signal:
            exit_signal = self.command_prompt()

    # 用于模仿Nested Function的Object
    # 可以被pickle
    class picklable_cmd_args():
        # 在我们的使用环境下，shell变量被直接传入了self，也就保留了指针，因此外部对cmd_args变量的改变也会使得这里的结果不同
        def __init__(self, shell, number):
            self.shell = shell
            self.number = number

        def __call__(self):
            return self.shell.cmd_args[self.number]

    def builtin_cd(self, pipe="", args=[]):
        # 更换目录功能
        # 对于多个参数的情况进行警告，并尝试进入第一个参数所示的功能
        if len(args):
            if len(args) > 1:
                log.warning("Are you trying to cd into multiple dirs? We'll only accept the first argument.")
            target_dir = args[0]
        else:
            # 在一般的shell中，无参数的cd调用会进入用户主目录
            # 但我们根据作业要求实现了打印当前工作目录的功能
            # well, we'd like to stay in home
            # but the teacher says we should pwd instead
            # target_dir = self.home()
            return self.builtin_pwd(pipe=pipe, args=args)

        # 若用户的输入开头为~符号，替换为用户主目录内容
        # if target_dir.startswith("~"):
        #     target_dir = f"{self.home()}{target_dir[1::]}"
        # the dir might not exist
        # 路径不存在则报错
        try:
            log.info(f"Changing CWD to {COLOR.BOLD(target_dir)}")
            os.chdir(target_dir)
        except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
            raise FileNotFoundException(e, {"type": "cd"})

    # 清空屏幕功能
    def builtin_clr(self, pipe="", args=[]):
        # clear the screen
        # we're forced to do a system call here...
        # Windows系统下为cls命令，而*nix下为clear
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
        # return ""

    def builtin_pwd(self, pipe="", args=[]):
        # 打印当前目录，如果使用了-a参数会打印完整的目录（将~符号替换为self.home()的值）
        cwd = self.cwd()  # 通过系统调用获得当前路径

        # 根据参数判断
        if len(args):
            if args[0] == "-a" and cwd.startswith("~"):
                cwd = f"{self.home()}{cwd[1::]}"
            else:
                raise ArgCountException("pwd only accepts -a as argument, otherwise don't give any argument")
        return cwd

    def builtin_dir(self, pipe="", args=[]):
        # 内置get_mode函数，用于获取文件劝降
        def get_mode(permissions):
            map_string = "rwxrwxrwx"
            map_empty = "---------"
            # 我们使用列表生成器对bit列表进行判断
            result = "".join([map_string[i] if permissions[i] else map_empty[i] for i in range(9)])
            return result

        # 没有参数时，处理当前目录
        if not len(args):
            args.append(".")

        # 不存在的目录的报错信息集合（用于最后的raise检查，会被调用'\n'.join）
        not_in_list = []
        # 储存将要打印的内容，最后会作为'\n'.join(result)的参数
        result = []

        for target_dir in args:
            # 第一行是当前打印的目录的名称
            result.append(target_dir)
            # if target_dir.startswith("~"):
            #     target_dir = f"{self.home()}{target_dir[1::]}"
            # the dir might not exist
            try:
                # 可能会出现找不到文件的情况，将找不到的文件添加到not_in_list中，继续处理下一个目录的打印操作，并在最后raise
                log.debug(f"Listing dir {COLOR.BOLD(target_dir)}")
                # 通过os接口获得文件名称
                dir_list = os.listdir(target_dir)
                for file_name in dir_list:
                    # 下面的stat等函数调用需要全路径
                    full_name = f"{target_dir}/{file_name}"

                    # 文件的访问权限，最后修改时间等信息
                    file_stat = os.stat(full_name)
                    file_mode = file_stat.st_mode
                    file_time = file_stat.st_mtime

                    # # guess we're not using this...
                    # type_code = file_mode >> 12

                    # 提取整数的每一位，一共获取9位
                    permissions = [(file_mode >> bit) & 1 for bit in range(9 - 1, -1, -1)]

                    # 将访问权限和目录信息转换为字符串
                    mode_str = get_mode(permissions)
                    time_str = datetime.datetime.fromtimestamp(file_time).strftime("%Y-%m-%d %H:%M:%S")

                    # 合并成为最终结果的一行的前半部分
                    file_line = f"{mode_str} {time_str} "

                    # 根据文件的类型/是否位可执行文件，写入相关颜色
                    if os.path.isdir(full_name):
                        # path is a directory
                        file_line += COLOR.BLUE(COLOR.BOLD(file_name))
                    else:
                        # ! os.access not working properly on windows
                        # todo: maybe we can recognize char block or others
                        # this is brutal
                        if os.access(full_name, os.X_OK):
                            # 用红色显示可执行文件
                            file_line += COLOR.RED(COLOR.BOLD(file_name))
                        else:
                            # 用普通粗体显示一般文件
                            file_line += COLOR.BOLD(file_name)

                    # 添加到完整的result数组中
                    result.append(file_line)
            except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
                not_in_list.append(str(e))
            finally:
                # 若用户传入了多个参数，在不同的文件夹间打印一个换行（最终'\n'.join的效果）
                result.append("")

        # 找不到的目录（可能输入了一个文件）数量为非空
        if len(not_in_list):
            # 打印可以打印的内容
            # 由于raise会使函数停止继续执行，我们在此打印一些信息
            # ! 注意，这种情况下我们不会返回结果，piping会停止
            print("\n".join(result), file=self.output_file, end="")
            joined = '\n'.join(not_in_list)
            raise FileNotFoundException(f"Cannot list director[y|ies]: \n{joined}", {"type": "dir"})

        # 若一切正常则以字符串形式直接返回最终结果
        return "\n".join(result)

    def builtin_echo(self, pipe="", args=[]):
        # 我们支持-r参数，只能放在开头，如果用户使用了-r: raw input就不会对输入的特殊内容进行转义翻译
        # 但是相应的shell内置参数还是会被尝试替换，例如变量或者表示用户根目录的~符号，这不是echo函数所能控制的
        # 没有-r我们会尝试转义其他的escape code
        # ! if -r is provided, we won't do any escaping
        result = f"{' '.join(args)}\n"
        if len(args) >= 1 and args[0] == "-r":
            result = result[len("-r ")::]
        else:
            # 通过codecs包实现较易于拓展的转义功能
            result = codecs.escape_decode(bytes(result, "utf-8"))[0].decode("utf-8")
        return result

    def builtin_exit(self, pipe="", args=[]):
        # 我们通过异常退出
        raise ExitException("Exitting...")

    def builtin_quit(self, pipe="", args=[]):
        # 我们通过异常退出
        raise ExitException("Quitting...")

    # 后台工作的相关内容
    @staticmethod
    def job_status_fmt(job_number, status, content):
        # 以统一的形式获得后台工作的样式
        return f"{COLOR.BOLD(COLOR.YELLOW(f'[{job_number}]'))} {COLOR.BOLD(status)} env {COLOR.BOLD(content)}"

    def job_status(self, job_number, status=None):
        # 设定后台工作的状态并返回统一的打印样式
        if status is not None:
            self.status_dict[job_number] = status
        else:
            status = self.status_dict[job_number]
        return self.job_status_fmt(job_number, status, self.jobs[job_number])

    def builtin_jobs(self, pipe="", args=[]):
        # 打印当前所有后台工作的执行情况
        log.debug("Trying to get all jobs")
        log.info(f"Content of jobs {COLOR.BOLD(self.jobs)}")
        log.info(f"Content of status_dict {COLOR.BOLD(self.status_dict)}")
        result = [self.job_status(key) for key in self.jobs.keys()]
        return '\n'.join(result)

    def builtin_queues(self, pipe="", args=[]):
        # 开发者测试用命令，检查内存泄漏用
        log.debug("Trying to get all queues")
        log.info(f"Content of queues {COLOR.BOLD(self.queues)}")
        return str(self.queues)

    def builtin_fg(self, pipe="", args=[]):
        # 将因为尝试获取用户输入而挂起的工作提到前台执行

        # 数量检查
        if len(args) != 1:
            raise JobException("Argument number is not correct, only one expected.", {"type": "len"})
        elif args[0] not in self.jobs:
            raise JobException(f"Cannot find job is jobs number \"{args[0]}\".", {"type": "key"})

        # 通过multiprocessin.Queue进行沟通
        # ! 注意，外部命令的读取请求不会被处理，因为在后台执行的subshell中PIPE会被关闭
        log.debug(f"Foreground is called with {COLOR.BOLD(args)}")
        print(self.job_status_fmt(args[0], "continued", self.jobs[args[0]]))
        if self.status_dict[args[0]] == "suspended":
            # ! only put into queue if already suspended
            # else the main process will get what it just put into the queue
            self.queues[args[0]].put("dummy")

        log.info("Waiting for foreground task to finish...")

        # 挂起主线程，等待后台程序执行完毕
        self.queues[args[0]].get()
        log.debug("Continuing main process")

    # 继续执行后台job
    def builtin_bg(self, pipe="", args=[]):
        # 处理相关参数调用
        if not len(args):
            raise JobException("Argument number is not correct, one or more expected.", {"type": "len"})

        not_in_list = [arg for arg in args if arg not in self.jobs]
        args = [arg for arg in args if arg in self.jobs]

        log.debug(f"Background is called with {COLOR.BOLD(args)}")
        for job_number in args:
            if self.status_dict[job_number] == "suspended":
                print(self.job_status_fmt(job_number, "continued", self.jobs[job_number]))
                print(self.job_status_fmt(job_number, "suspended", self.jobs[job_number]))
            elif self.status_dict[job_number] == "running":
                log.warning(f"Job [{job_number}] is already running")

        # 找不到的后台工作会被反馈给用户
        if len(not_in_list):
            raise JobException(f"Cannot find job with number \"{not_in_list}\".", {"type": "key"})

    def builtin_term(self, pipe="", args=[]):
        # 处理相关参数调用
        if not len(args):
            raise JobException("Argument number is not correct, one or more expected.", {"type": "len"})

        not_in_list = [arg for arg in args if arg not in self.jobs]
        args = [arg for arg in args if arg in self.jobs]

        for job_number in args:
            log.debug("Terminating...")
            # 对multiprocessing的进程包发出signal.SIGTERM信号，给其机会处理相关内容（关闭subshell等）
            # ! 在*nix上与subshell，run_command_wrap配合可避免zombie process
            # ! Windows中由于接口不匹配的原因，无法完全清除zombie
            os.kill(self.process[job_number].pid, signal.SIGTERM)

            print(self.job_status_fmt(job_number, "terminated", self.jobs[job_number]))

            # 我们以jobs数组为蓝本，判断jobs是否已完成或者被强行结束等
            # 配合clean_up函数，status_dict和queues等其他数组会被正常清理
            del self.jobs[job_number]

        # 找不到的后台工作会被反馈给用户
        if len(not_in_list):
            raise JobException(f"Cannot find jobs with number \"{not_in_list}\".", {"type": "key"})

    def builtin_check_zombie(self, pipe="", args=[]):
        # 开发者调试用函数
        # 用于检查当前进程下的zombie process
        any_process = -1
        while True:
            # This will raise an exception on Windows.  That's ok.
            pid, status = os.waitpid(any_process, os.WNOHANG)
            if pid == 0:
                break
            log.warning(f"I don't know wtf this is... {COLOR.BOLD(str(pid) + ', ' + str(status))}")
            if os.WIFEXITED(status):
                log.warning(f"The process of pid \"{pid}\" is done.")
            elif os.WIFSTOPPED(status):
                log.warning(f"The process of pid \"{pid}\" is suspended.")
            elif os.WIFCONTINUED(status):
                log.warning(f"The process of pid \"{pid}\" is continued.")
            else:
                log.warning(f"The process of pid \"{pid}\" is of status {status}")

    def cleanup_jobs(self):
        # 对jobs命令的拓展
        # 我们的任务管理系统以self.jobs字典为准，每次命令调用后都会刷新当前的数组内容以删除不必要的元素
        # 管理：self.queues, self.status_dict, self.process
        # 避免了内存泄漏
        keys = list(self.queues.keys())

        log.debug(f"Queue is being cleaned, previous keys are {COLOR.BOLD(keys)}")
        for i in keys:
            if i not in self.jobs.keys():
                del self.queues[i]
        log.debug(f"Queue is cleaned, keys are {COLOR.BOLD(self.queues.keys())}")

        keys = list(self.process.keys())

        log.debug(f"Process is being cleaned, previous keys are {COLOR.BOLD(keys)}")
        for i in keys:
            if i not in self.jobs.keys():
                del self.process[i]
        log.debug(f"Process is cleaned, keys are {COLOR.BOLD(self.process.keys())}")

        keys = list(self.status_dict.keys())

        log.debug(f"Status Dict is being cleaned, previous keys are {COLOR.BOLD(keys)}")
        for i in keys:
            if i not in self.jobs.keys():
                del self.status_dict[i]
        log.debug(f"Status Dict is cleaned, keys are {COLOR.BOLD(self.status_dict.keys())}")

    def builtin_environ(self, pipe="", args=[]):
        # # 将MyShell的环境变量返回给用户
        result = []
        for key in self.vars:
            try:
                # 由于self.vars的特殊性，不能直接调用列表生成器
                # 对于命令行参数，我们事先不知道有效参数的数量，因此只能单独尝试
                result.append(f"{key}={COLOR.BOLD(self.vars[key])}")
            except IndexError:
                pass
        return "\n".join(result)

    def builtin_set(self, pipe="", args=[]):
        # 修改脚本变量，用户需要保证自己的输入内容被解释为一个完整的参数
        # 用等于号分割变量名和变量的具体值
        # 变量都以字符串的形式储存
        # we'd like the user to use the equal sign
        # and we'd like to treat varibles only as string
        for arg in args:
            split = arg.split("=")
            if len(split) != 2:
                raise SetPairUnmatchedException(f"Cannot match argument {arg}.", {"type": "set"})
            key, value = split
            log.debug(f"Setting \"{key}\" in environment variables to \"{value}\"")

            try:
                # 修改pwd时，可能会有找不到目录的错误
                # might be error since self.vars is not a simple dict
                self.vars[key] = value
            except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
                raise FileNotFoundException(e, {"type": "set", "arg_pair": [key, value]})

    def builtin_unset(self, pipe="", args=[]):
        # 取消MyShell中一些已经设置好的变量
        cannot_unset = []
        # 类似builtin_environ中的处理方式，为了跳过可能出错的变量，我们手动循环
        for key in args:
            try:
                del self.vars[key]
            except (KeyError, ReservedKeyException):
                cannot_unset.append(key)
        if len(cannot_unset):
            raise UnsetKeyException("Cannot find/unset these keys.", {"keys": cannot_unset})

    def builtin_umask(self, pipe="", args=[]):
        # 设置系统umask的值
        # subshell中的命令也会继续采用这一umask
        # 若没有任何参数，则直接打印umask
        # ! 在Windows上无法正常修改umask
        if len(args) > 1:
            # 参数数量为0或者1
            raise UmaskException("Argument number is not correct, only one or zero expected.", {"type": "len"})
        elif len(args) == 1:
            try:
                # 用户输入的umask值不一定有效
                log.debug(f"Value of ARG: {COLOR.BOLD(args[0])}")
                umask = int(args[0], 8)
                log.debug(f"Value of ARG in int of 8: {COLOR.BOLD(umask)}")
                os.umask(umask)
            except ValueError as e:
                raise UmaskException(e, {"type": "value"})
        else:
            # dummy parameter
            old = os.umask(0)
            log.debug(f"Value of OLD: {COLOR.BOLD(old)}")
            os.umask(old)
            # 返回umask的时候采用补零3位8进制格式
            return "0o{:03o}".format(old)

    def builtin_printio(self, pipe="", args=[]):
        # 开发者调试用命令，用于检查当前的exec文件重定向
        # note: 由于我们要检查重定向，这里会直接打印到stdout而非输入输出文件
        result = []
        result.append(f"FILE NUMBER OF INPUT FILE: {COLOR.BOLD(self.input_file.fileno() if self.input_file is not None else sys.stdin.fileno())}, redirecting MyShell input to {COLOR.BOLD(self.input_file)}")
        result.append(f"FILE NUMBER OF INPUT FILE: {COLOR.BOLD(self.output_file.fileno() if self.output_file is not None else sys.stdout.fileno())}, redirecting MyShell output to {COLOR.BOLD(self.output_file)}")
        # ! debugging command, no redirection
        print("\n".join(result))

    def builtin_exec(self, pipe="", args=[]):
        # exec命令会修改MyShell命令的输入输出源
        # note: 由于此命令的特殊性，我们会在该函数得到执行的上一层加入一些逻辑
        if len(args) != 2:
            log.critical("Internal error, builtin_exec should be executed with exactly two arguments")
            raise ArgCountException("Internal error, builtin_exec should be executed with exactly two arguments")

        log.debug(f"FILE NUMBER OF SYS.__STDIN__: {COLOR.BOLD(sys.__stdin__.fileno())}")
        log.debug(f"FILE NUMBER OF SYS.__STDOUT__: {COLOR.BOLD(sys.__stdout__.fileno())}")
        log.debug(f"FILE NUMBER OF SYS.__STDERR__: {COLOR.BOLD(sys.__stderr__.fileno())}")

        # 我们刚刚已经保证走到这一步的参数数量为2
        if args[0]:  # 若非空，尝试设置输入流
            try:
                # the function open will automatically raise FileNotFoundError
                new_file = open(args[0], "r", encoding="utf-8")

                # 新文件打开没有出错时我们才会关闭/修改旧文件
                # 无论如何，关闭原来已经打开的输入输出文件
                if self.input_file is not None:
                    self.input_file.close()
                self.input_file = new_file
                log.debug(f"FILE NUMBER OF INPUT FILE: {COLOR.BOLD(self.input_file.fileno())}")
            except FileNotFoundError as e:
                raise FileNotFoundException(e, {"type": "redi_in"})
        else:
            log.debug(f"Setting input file to None: stdin")
            self.input_file = None
        if args[1]:  # 若非空，尝试设置输入流
            try:
                # the function open will automatically raise FileNotFoundError
                new_file = open(args[1], "w", encoding="utf-8")

                # 新文件打开没有出错时我们才会关闭/修改旧文件
                if self.output_file is not None:
                    self.output_file.close()
                self.output_file = new_file
                log.debug(f"FILE NUMBER OF OUTPUT FILE: {COLOR.BOLD(self.output_file.fileno())}")
            except FileNotFoundError as e:
                raise FileNotFoundException(e, {"type": "redi_out"})
        else:
            log.debug(f"Setting output file to None: stdout")
            self.output_file = None

    def builtin_shift(self, pipe="", args=[]):
        # 内置shift功能，在脚本调用时尤其有用
        log.debug(f"Shift args are {COLOR.BOLD(args)}")
        log.debug(f"Previously cmd_args are {COLOR.BOLD(self.cmd_args)}")

        if len(args) > 1:
            raise ArgCountException("Expecting zero or one arguments")
        elif not args:
            # 空参数情况移动1位
            args.append(1)

        # $0会被保留
        dollar_zero = self.cmd_args[0]

        try:
            # 此时的shift时包含dollar_zero的
            self.cmd_args = self.cmd_args[args[0]::]
        except IndexError:
            pass

        # 替换掉dollar_zero位置的元素
        if not len(self.cmd_args):
            self.cmd_args = [dollar_zero]
        else:
            self.cmd_args[0] = dollar_zero

        log.debug(f"Now cmd_args are {COLOR.BOLD(self.cmd_args)}")

    def builtin_test(self, pipe="", args=[]):
        # ! test函数的结合方向是从右向左
        # todo: 实现带运算符顺序处理的逆波兰表达式（现在对-a和-o是一视同仁的）
        # 结合递归调用
        # builtin_test功能中使用到的等级函数
        # 主要用于对操作符进行分类，方便调用，例如1，3为单目运算符
        level = {
            "(": 0, ")": 0,
            "-z": 1, "-n": 1,
            "=": 2, "!=": 2, "-eq": 2, "-ge": 2, "-gt": 2, "-le": 2, "-lt": 2, "-ne": 2,
            "!": 3,
            "-a": 4, "-o": 4,
        }

        # 单目运算符操作
        def test_unary(operator, operand):
            if operator == "-z":
                return not len(str(operand))
            if operator == "-n":
                return len(str(operand))
            if operator == "!":
                return not bool(operand)

            log.critical("Unrecoginized operator in a place it shouldn't be")
            raise TestException(f"Unrecognized unary operator \"{operator}\"")

        # 双目运算符操作
        def test_binary(op, lhs, rhs):
            if op == "=":
                return str(lhs) == str(rhs)
            if op == "!=":
                return str(lhs) != str(rhs)
            if op == "-eq":
                # todo: exception
                return int(lhs) == int(rhs)
            if op == "-ge":
                return int(lhs) >= int(rhs)
            if op == "-gt":
                return int(lhs) > int(rhs)
            if op == "-le":
                return int(lhs) <= int(rhs)
            if op == "-lt":
                return int(lhs) < int(rhs)
            if op == "-ne":
                return int(lhs) != int(rhs)
            if op == "-a":
                return bool(lhs) and bool(rhs)
            elif op == "-o":
                return bool(lhs) or bool(rhs)

            log.critical("Unrecoginized operator in a place it shouldn't be")
            raise TestException(f"Unrecognized binary operator \"{operator}\"")

        def expand_expr(args):
            # ! we combine from the right, that is the right most value are evaluated first
            try:
                ind = 0
                if len(args) == 1:
                    return args[0]

                # 非运算符，视为双目运算
                if args[ind] not in level:
                    lhs = args[ind]
                    op = args[ind+1]
                    # 这句话保证了从右向左结合
                    rhs = expand_expr(args[ind+2::])
                    return test_binary(op, lhs, rhs)

                # match parentheses
                if args[ind] == "(":
                    # 对于小括号，我们将其视为一个整体
                    org = ind
                    while args[ind] != ")":
                        ind += 1
                    lhs = expand_expr(args[org+1:ind])
                    if ind == len(args)-1:
                        return lhs
                    op = args[ind+1]
                    # 这句话保证了从右向左结合
                    rhs = expand_expr(args[ind+2::])
                    return test_binary(op, lhs, rhs)

                if level[args[ind]] in [1, 3]:
                    # 对于单目运算符，我们也将其视为一个整体
                    op = args[ind]
                    oa, ind = get_one(args[ind+1::])
                    lhs = test_unary(op, oa)
                    if ind == len(args)-1:
                        return lhs
                    op = args[ind+1]
                    # 这句话保证了从右向左结合
                    rhs = expand_expr(args[ind+2::])
                    return test_binary(op, lhs, rhs)

            # note: 在此处理整个函数调用过程中可能的错误
            # int，bool无法转换/解释等
            except (ValueError, KeyError) as e:
                # log.error(f"{e}")
                raise TestException(e)

        def get_one(args):
            # 获取一位bool值，并返回下一个有效值的位置
            ind = 0
            if len(args) == 1 or args[ind] not in level:
                return args[0], 1

            if args[ind] == "(":
                org = ind
                while args[ind] != ")":
                    ind += 1
                return expand_expr(args[org+1:ind]), ind+1

            if level[args[ind]] in [1, 3]:
                op = args[ind]
                oa, ind = get_one(args[ind+1::])
                return test_unary(op, oa), ind+1

        # we can only use string to pass values
        # 返回布尔值的字符串表示
        # return tf[bool(expand_expr(args))]
        return str(bool(expand_expr(args)))

    def builtin_sleep(self, pipe="", args=[]):
        if os.name == "nt":
            # ! Windows系统没有相应的sleep命令，但Python存在相应的接口
            try:
                if len(args) == 1 and args[0].endswith("s"):
                    time.sleep(float(args[0][0:-1]))
                else:
                    raise ValueError
            except ValueError as e:
                raise SleepException(f"Unrecoginized sleep time format, are you on NT? Use second as unit and put s at the back of the time string. {e}")
        else:
            self.subshell(target="sleep", args=args, pipe=pipe)

    def builtin_time(self, pipe="", args=[]):
        # 显示当前的时间
        return str(datetime.datetime.now())

    def builtin_dummy(self, pipe="", args=[]):
        # 一个内置的dummy命令，用于测试是否可以正常触发suspension
        print("builtin_dummy: before any input requirements")
        print(input("dummy1> "))
        print(input("dummy2> "))
        print(input("dummy3> "))
        print(input("dummyend> "))

    def builtin_help(self, pipe="", args=[]):
        # 在线帮助函数
        # todo: 写好在线帮助
        pass

    def subshell(self, pipe="", target="", args=[], piping_in=False, piping_out=False, io_control=False):
        # 运行外部程序
        # 根据需要调整输入输出

        # 是一个内部命令，通过调用subprocess的接口完成外部程序的调用
        if not target:
            raise EmptyException(f"Command \"{target}\" is empty", {"type": "subshell"})
        to_run = [target] + args
        log.debug(f"Runnning in subprocess: {COLOR.BOLD(to_run)}")
        try:
            log.debug(f"EXEC OI controller is: {COLOR.BOLD(str(self.input_file) + ' ' + str(self.output_file))}")
            result = None
            if io_control:
                piping_in = True
            # waits for the process to end
            # 若需要通过管道传递相关内容，则使用PIPE
            # ! windows中有些内置命令是无法通过subprocess调用的，例如type等cmd.exe内置命令
            p = subprocess.Popen(
                to_run,
                stdin=PIPE if piping_in else self.input_file,
                stdout=PIPE if piping_out else self.output_file,
                stderr=STDOUT, encoding="utf-8",
                env=dict(os.environ, PARENT=self.vars["SHELL"])
            )

            self.subp = p
            result, error = p.communicate(pipe)  # 如果我们选择不使用PIPE，这里传入空字符串也不会有任何影响
            if p.returncode != 0:
                log.warning("The subprocess is not returning zero exit code")
                raise CalledProcessException("None zero return code encountered")
        finally:
            # 我们使用try block的原因在于无论如何都要清空一下self.subp
            self.subp = None

        # 若通过subshell调用，则直接将结果以字符串形式返回
        return result

    def path(self):
        # callable PATH function，随着系统变量的改变而改变
        return os.environ["PATH"]

    def home(self):
        # callable HOME function，随着系统变量的改变而改变
        return os.environ['HOME']

    def cwd(self):
        # callable PWD function，随着系统变量的改变而改变
        cwd = os.getcwd()
        if cwd.startswith(self.home()):
            cwd = f"~{cwd[len(self.home())::]}"
        return cwd

    def user(self):
        # callable USER function，随着系统变量的改变而改变
        return getpass.getuser()

    def location(self):
        # callable LOCATION function，随着系统变量的改变而改变
        return platform.node()

    def prompt(self):
        # 返回将要打印到屏幕的命令提示符
        # 包含：用户@地点 当前目录 当前时间 提示符
        # [conda_default_env] user@location /path/to/current/dir time_now PS1
        prompt = f"{COLOR.BEIGE(self.user()+'@'+self.location())} {COLOR.BOLD(COLOR.BLUE(self.cwd()))} {COLOR.BOLD(datetime.datetime.now().strftime('%H:%M:%S'))} {COLOR.BOLD(COLOR.YELLOW(self.vars['PS1']))} "
        # log.debug(repr(prompt))
        try:
            conda = os.environ["CONDA_DEFAULT_ENV"]
            prompt = f"({conda}) {prompt}"
        except KeyError:
            pass  # not a conda environment
        return prompt

    def execute(self, command, pipe=""):
        # 执行一个已经被格式化的命令
        # 命令以dict形式传入，其中exec代表命令本身，args代表命令参数
        # 还有一些其他控制参数，例如重定向或者管道操作
        # 本函数还包含了对于exec命令的特殊处理（我们会提前处理重定向操作，而非交给命令本身，因此需要特殊化参数才可正常传入）
        log.info(f"Executing command {COLOR.BOLD(command['exec'])}")
        log.info(f"Arguments are {COLOR.BOLD(command['args'])}")

        # pipe或者重定向输入只能有一个
        if command["pipe_in"] and command["redi_in"]:
            raise MultipleInputException("Redirection and pipe are set as input at the same time.")

        # piping_in/piping_out主要用于subshell的处理
        command["piping_in"] = command["pipe_in"] or command["redi_in"]
        command["piping_out"] = command["redi_out"] or command["pipe_out"]

        # 处理输入重定向
        # to the command itself, it doesn't matter whether the input comes from a pipe or file
        if command["redi_in"]:
            file_path = command["redi_in"]
            try:
                # the function open will automatically raise FileNotFoundError
                f = open(file_path, "r")
                pipe = f.read()
                f.close()
            except FileNotFoundError as e:
                raise FileNotFoundException(e, {"type": "redi_in"})

        # if we've specified input file in some thing
        if self.input_file is not None:
            sys.stdin = self.input_file

        # actual execution
        result = ""
        try:
            if command["exec"] == "exec":
                if len(command["args"]):
                    raise ArgCountException("exec command takes no argument")
                # setting redi_files to arguments
                # something might change
                self.builtin_exec(args=[command["redi_in"], command["redi_out"]])
            elif command["exec"] in self.builtins.keys():
                log.debug("This is a builtin command.")
                # executing as static method, calling with self variable
                result = self.builtins[command["exec"]](self, pipe=pipe, args=command['args'])
            else:
                log.debug("This is not a builtin command.")
                try:
                    result = self.subshell(pipe, command["exec"], command['args'], piping_in=command["piping_in"], piping_out=command["piping_out"], io_control=command["io_control"])
                except FileNotFoundError as e:
                    raise FileNotFoundException(e, {"type": "subshell"})
        finally:
            # 我们使用try block的原因在于无论如何都要清空一下self.subp
            sys.stdin = sys.__stdin__

        # 处理输出重定向
        if command['redi_out']:
            log.debug(f"User want to redirect the output to {COLOR.BOLD(command['redi_out'])}")
            try:
                f = open(command["redi_out"], "a" if command["redi_append"] else "w")
                f.write(result)
                f.close()
            except FileNotFoundError as e:
                raise FileNotFoundException(e, {"type": "redi_out", "redi_append": command["redi_append"]})
            return result

        # 若用户需要进行管道操作，就不打印相关内容，直接以字符串返回获得的内容
        if command['pipe_out']:
            log.debug(f"User want to pipe the IO")
            return result

        if result is not None:
            print(result, end="" if result.endswith("\n") or not len(result) else "\n", file=self.output_file)
        # return result # won't be used anymore

    def command_prompt(self):
        # 命令提示符打印
        # note: readline quirk
        # strange error if we use input
        # the input and readline prompt seems to be counting color char as one of the line chars
        # well it turns out to be a quirk of readline
        # we've fixed it in COLOR.py
        try:
            command = input(self.prompt()).strip()
        except EOFError:
            # 在程序以交互模式运行，但是读入源非标准输入，就有可能在读完全部命令后得到EOFError
            # 我们选择在这种情况下退出交互模式
            # note: 这也意味着在普通的交互模式下输入Ctrl+D也会使shell退出
            print()
            log.warning("Getting EOF from command prompt, exiting...")
            return self.run_command("exit")

        log.debug(f"Getting user input: {COLOR.BOLD(command)}")
        # 通过调用run_command来执行相关内容
        result = self.run_command(command)
        return result

    @staticmethod
    def run_command_wrap(count, shell, args, job, queue, jobs, status_dict):
        # 用于后台程序管理
        # 我们不仅可以后台运行外部命令，程序自身命令也可以后台执行
        # 且管道，重定向等操作都由MyShell执行，这与直接刷出一个新的subprocess完全不同
        # 我们没有在这种情况下借用已有shell的功能
        log.debug(f"Wrapper [{count}] called with {COLOR.BOLD(f'{shell} and {args}')}")

        # ! DOESN"T WORK ON WINDOWS!
        # ! WILL CREATE ZOMBIE PROCESS!

        # 为了在信号处理过程中正确杀死自身进程
        my_pid = os.getpid()

        # signal handler，遇到signal.SIGTERM后杀死可能正在运行的子进程
        def exit_subp(sig, frame):
            if shell.subp is not None:
                log.warning("Killing a still running subprocess...")
                os.kill(shell.subp.pid, signal.SIGKILL)
            log.debug(f"Getting signal: {COLOR.BOLD(sig)}")
            log.debug(f"Are you: {COLOR.BOLD(signal.SIGTERM)}")
            if sig == signal.SIGTERM:
                # 杀死自身进程
                log.warning(f"Terminating job [{count}] handler process by signal...")
                os.kill(my_pid, signal.SIGKILL)

        # 注册信号处理器
        # note: multiprocessin.Process.daemon = True时，若父进程退出，该信号会被触发
        signal.signal(signal.SIGTERM, exit_subp)

        # note: 正文
        # 通过Wrapper来控制内部命令的suspension
        if sys.stdin is not None:
            sys.stdin.close()
        # stdin的文件号
        stdin = open(0)
        buffer = stdin.detach()
        wrapper = MyShell.StdinWrapper(queue, count, job, status_dict, buffer)
        sys.stdin = wrapper

        try:
            # 真正的执行过程
            # 详见run_command
            # 包括解析命令/执行命令/错误处理
            # 此时不会执行后台逻辑，跳过parse阶段
            shell.run_command(args, io_control=True)
        finally:
            # 正常情况下不会出现raise的情况
            # 无论如何，都要退出当前的job
            print(shell.job_status_fmt(count, "finished", job))
            queue.put("dummy")
            del jobs[count]

    def term_all(self):
        # 杀死jobs数组中所有的剩余任务
        jobs = self.jobs
        for job in jobs:
            os.kill(self.process[job].pid, signal.SIGTERM)
            # 我们会将job相关信息直接打印到屏幕上
            print(self.job_status_fmt(job, "terminated", jobs[job]))

    def run_command(self, command, io_control=False):
        # 解析命令，执行命令，错误处理，后台任务
        try:
            # commands是一个command数组，包含具体的方便读取的命令格式信息
            # 由于存在PIPE调用的可能性，我们对commands创建了数组
            # parse会将命令字符串解释为完整的命令
            commands, is_bg = self.parse(command)
            if is_bg:
                # ! changes made in subprocess is totally within the subprocess only

                # job_counter实际上是一个函数
                # 会获取当前没有被使用掉的最小的job编号，从0开始
                str_cnt = self.job_counter

                # 创建相关内容
                self.jobs[str_cnt] = command
                self.queues[str_cnt] = Queue()
                self.status_dict[str_cnt] = "running"

                # 备份相关内容以便deepcopy时删除
                queues_bak = self.queues
                process_bak = self.process
                jobs_bak = self.jobs
                status_dict_bak = self.status_dict
                input_bak = self.input_file
                output_bak = self.output_file

                # note: 为了规避一些pickle error，我们会删除这里的：
                # thread_lock, multiprocessing.Manager, multiproessing.Queue, Manager.dict, io.TextWrapper
                del self.queues
                del self.process
                del self.jobs
                del self.status_dict
                del self.input_file
                del self.output_file

                # 获取一个deepcopy的shell以供后台程序执行
                clean_self = copy.deepcopy(self)

                # 填充默认内容
                # ! 我们默认后台程序不会尝试再次构建后台的后台指令
                clean_self.queues = {}
                clean_self.jobs = {}
                clean_self.process = {}
                clean_self.status_dict = {}
                clean_self.input_file = None
                clean_self.output_file = None

                # 还原到deepcopy以前的状态
                self.queues = queues_bak
                self.process = process_bak
                self.jobs = jobs_bak
                self.status_dict = status_dict_bak
                self.input_file = input_bak
                self.output_file = output_bak

                # 使用deepcopy初来的clean_self来构建新的进程
                p = Process(target=self.run_command_wrap, args=(str_cnt, clean_self, command[0:-1], self.jobs[str_cnt], self.queues[str_cnt], self.jobs, self.status_dict), name=command)

                # 添加到进程管理中，方便kill命令等的执行
                self.process[str_cnt] = p

                # ! so the multiprocessing process won't actually be totally gone if the main process is still around
                # but it will be terminated if demanded so (ps command can see it as <defunc>, but not a zombie)
                # 保证主进程退出后，下面的小进程也会退出
                p.daemon = True

                # 开始运行
                p.start()
                log.debug(f"We've spawned the job in a Process for command: {COLOR.BOLD(p.name)}")
            else:
                # 一般命令的执行
                result = None  # so that the first piping is directly from stdin
                if io_control:
                    for command in commands:
                        command["io_control"] = True
                else:
                    for command in commands:
                        command["io_control"] = False
                for cidx, command in enumerate(commands):
                    result = self.execute(command, pipe=result)
                    # log.debug(f"Getting result: {COLOR.BOLD(result)}")
        except ExitException as e:
            # 我们通过异常来处理程序的退出命令
            # 包括quit和exit
            # 某种意义上Ctrl+D代表的EOF也是一种推出指令
            log.debug("User is exiting...")
            log.debug(f"Exception says: {e}")
            log.info("Bye")
            self.term_all()
            return True
        except EmptyException as e:
            # EmptyException较为特殊，需要单独处理
            # 因为错误等级会根据type不同而变换
            log.debug("The command is empty...")
            log.info(f"Exception says: {e}")
            if e.errors["type"] == "pipe":
                log.error(f"Your pipe is incomplete. {e}")
            elif e.errors["type"] == "subshell":
                log.warning(f"Your command is empty. Did you use an empty var? {e}")
            elif e.errors["type"] == "empty":
                log.info(f"Your command is empty. {e}")
        except MyShellException as e:
            # this means that we've got a none zero return code / execution failure
            error_cmd = command['exec'] if isinstance(command, dict) else command
            line_end = "\n"
            log.error(f"Cannot successfully execute command \"{error_cmd}\". Exception is: {line_end}{COLOR.BOLD(str(e) + line_end + 'Extra info: ' + str(e.errors))}")
        except Exception as e:
            log.error(f"Unhandled error. {traceback.format_exc()}")
        finally:
            # 同步status_dict, queues, jobs
            self.cleanup_jobs()  # always clean up

        # 不返回退出指令
        return False

    def parse(self, command):
        # 命令解释器

        # quote函数会处理引号/变量替换/特殊变量转义/~替换
        inputs = self.quote(command)  # splitting by whitespace and processing varibles, quotes

        # 将命令分解，进行piping调用
        # splitting command of pipling
        commands = []
        command = []
        for word in inputs:
            if word != "|":
                command.append(word)
            else:
                commands.append(command)
                command = []
        commands.append(command)

        # 对每一个个别的命令进行解析
        is_bg = False  # 是否后台执行是整个命令的设置，只需要一个
        parsed_commands = []

        for cidx, command in enumerate(commands):
            parsed_command = self.parsed_clean()
            # 可能用户只是敲了一下回车
            # 也可能用户的某一个管道环节是空的：这是不允许的
            # 我们通过type传递相关信息
            if not len(command):
                raise EmptyException(f"Command at position {cidx} is empty", {"type": "pipe" if len(commands) > 1 else "empty"})
            parsed_command["pipe_in"] = (cidx > 0)
            parsed_command["pipe_out"] = (cidx != len(commands)-1)
            index = 0
            while index < len(command):
                if not index:  # this should have a larger priority
                    # 整个命令的第一个词汇是执行目标
                    parsed_command["exec"] = command[index]
                elif command[index] == "<":
                    # 输入重定向
                    if index == len(command) - 1:
                        raise SetPairUnmatchedException("Cannot match redirection input file with < sign.", {"type": "redi"})
                    parsed_command["redi_in"] = command[index+1]
                    index += 1
                elif command[index] == ">":
                    # 输出重定向
                    if index == len(command) - 1:
                        raise SetPairUnmatchedException("Cannot match redirection output file with > sign.", {"type": "redi"})
                    parsed_command["redi_out"] = command[index+1]
                    index += 1
                elif command[index] == ">>":
                    # 输出重定向：添加型
                    if index == len(command) - 1:
                        raise SetPairUnmatchedException("Cannot match redirection output file with >> sign.", {"type": "redi"})
                    parsed_command["redi_out"] = command[index+1]
                    parsed_command["redi_append"] = True
                    index += 1
                elif command[index] == "&":
                    if index != len(command)-1 or cidx != len(commands) - 1:
                        # & not at the end
                        raise UnexpectedAndException("Syntax error, unexpected & found")

                    # todo: communication
                    is_bg = True
                    log.info("User want this to run in background.")
                else:
                    parsed_command["args"].append(command[index])
                index += 1
            parsed_commands.append(parsed_command)

        return parsed_commands, is_bg

    def quote(self, command, quote=True):
        # 可以被递归调用的引号处理功能
        # command should already been splitted by word
        # mark: this structure makes it possible that the arg is keep in one place if using quote
        # by not brutally expanding on every possible environment variables
        command = command.split()
        # 清除所有的注释
        # note: 就像一般的shell，注释前面要有一个空格
        comment = [i for i, v in enumerate(command) if v.startswith("#")]
        if len(comment):
            command = command[0:comment[0]]

        quote_stack = []
        index = 0
        while index < len(command):

            # 这一个if-else代码块保证所有内容被解析过一次，且仅解析一次，调用self.expand函数
            # 并且若解析后的内容有引号，也不会影响程序的正常执行，因为我们是在处理引号后解析变量的
            # note: 也就是说如果你的变量中存在着可以被解析为变量的内容，它们不会被解析，以防止无限递归解析
            if command[index].count("\"") >= 1:
                # should remove all quotes here
                quote_count = command[index].count("\"")
                log.debug("Trying to remove quote...")
                splitted = command[index].split("\"")
                # there were not space at the beginning
                # expand函数会进行变量和~的替换
                # 我们会将读入的内容按照引号数量拆分，然后进行解析
                # 最后合并成一个长字符串
                # 并通过quote_count来和下面的代码沟通
                command[index] = "".join([self.expand(split) for split in splitted])
            else:
                command[index] = self.expand(command[index])
                quote_count = 0

            if quote_count % 2:  # previous quote_count
                # 引号分词中出现了空格
                if quote_stack:
                    # except the last char
                    quote_stack.append(command[index])
                    # recursion to process $ and "" in the already processed ""
                    command[index] = " ".join(quote_stack)
                    quote_stack = ""
                    # index should continue to be added in the end
                else:
                    log.debug("Trying to match quote...")
                    quote_stack.append(command[index])
                    if index == len(command)-1:
                        raise QuoteUnmatchedException("Cannot match the quote for the last argument")
                    command = command[0:index] + command[index+1::]
                    index -= 1
            elif quote_stack:
                # 引号分词没有空格，加入到上一个quote组中
                # no quote but
                quote_stack.append(command[index])
                if index == len(command)-1:
                    raise QuoteUnmatchedException("Cannot match the quote for a series of arguments")
                command = command[0:index] + command[index+1::]
                index -= 1  # index should stay the same
            index += 1

        return [i.replace("\\~", "~").replace("\\$", "$") for i in command]

    def expand(self, string):
        def get_key(key):
            # 第一个字符$不能被用于寻找变量
            key = key[1::]
            log.debug(f"Trying to get varible {COLOR.BOLD(key)}")
            try:
                var = self.vars[key]
                log.debug(f"Got the varible {COLOR.BOLD(var)}")
            except (KeyError, IndexError) as e:
                log.warning(f"Unable to get the varible \"{key}\", assigning empty string")
                var = ""
            # splitting the expanded command since it might contain some information
            return var

        def get_home(key):
            log.debug(f"GETTING HOME SIGN: {COLOR.BOLD(key)}")
            if key == "~":
                return self.home()
            else:
                return key

        # 通过调用regex的替换命令（其实是我们自己实现的）
        # ! re.sub在处理utf-8字符串时有难以预料的错误
        # ! if you use re.sub on windows, strange things can happen
        # *nix可以正常运行，但Windows下报错
        string = self.sub_re(r"(?<!\\)\$\w+", string, get_key)
        string = self.sub_re(r"(?<!\\)~", string, get_home)

        return string

    @staticmethod
    def sub_re(pattern, string, method):
        # 根据regex寻找匹配子串，然后通过调用method函数进行替换的静态方法

        # 所有的匹配结果
        var_list = [(m.start(0), m.end(0)) for m in re.finditer(pattern, string)]
        
        # 拆分为替换后的内容
        str_list = []
        prev = [0, 0]
        for start, end in var_list:
            str_list.append(string[prev[1]:start])
            str_list.append(string[start:end])
            prev = [start, end]
        str_list.append(string[prev[1]::])


        # log.debug(f"The splitted vars are {COLOR.BOLD(str_list)}")

        # 对于每一个匹配成功的字串，进行method(key)的调用
        for i in range(1, len(str_list), 2):
            str_list[i] = method(str_list[i])            
            # to result in index staying the same

        string = "".join(str_list)
        return string

    def parsed_clean(self):
        # 返回一个干净的指令
        parsed_command = {
            "exec": "",
            "args": [],
            "pipe_in": False,
            "pipe_out": False,
            "redi_in": "",
            "redi_out": "",
            "redi_append": False,
        }
        return parsed_command



if __name__ == "__main__":
    # echo "zy" | sha256sum | tr -d " -" | wc
    # ./MyShell.py -w dummy.mysh -a foo bar foobar hello world linux linus PyTorch CS231n

    # 调用此脚本时候传入-h以查看帮助
    parser = argparse.ArgumentParser(description='MyShell by xudenden@gmail.com')
    parser.add_argument('f', metavar='F', type=str, nargs='?', help='the batch file to be executed')
    parser.add_argument('-a', metavar='A', type=str, nargs='*', help='command line arguments to batch file')
    parser.add_argument('-e', help='enable error level debugging info log', action='store_true')
    parser.add_argument('-w', help='enable warning level debugging info log', action='store_true')
    parser.add_argument('-i', help='enable info level debugging info log', action='store_true')
    parser.add_argument('-d', help='enable debug(verbose) level debugging info log', action='store_true')

    args = parser.parse_args()
    # args为MyShell的命令行参数
    # 处理MyShell的命令行参数
    if args.e:
        coloredlogs.set_level("ERROR")
    if args.w:
        coloredlogs.set_level("WARNING")
    if args.i:
        coloredlogs.set_level("INFO")
    if args.d:
        coloredlogs.set_level("DEBUG")

    # 命令行参数的第一个为当前脚本的路径（脚本模式），或MyShell的路径（交互模式）
    cmd_args = [os.path.abspath(args.f) if args.f else os.path.abspath(__file__)]
    if args.a is not None:
        cmd_args += args.a
    myshell = MyShell(cmd_args=cmd_args)
    log.debug(f"Getting user command line argument(s): {COLOR.BOLD(args)}")

    # ! 一次只准执行一个脚本
    if args.f:
        try:
            # ! using utf-8
            f = open(args.f, encoding="utf-8")  # opending the file specified
            for line in f:
                line = line.strip()
                result = myshell.run_command(line)  # execute line by line
                if result:  # the execution of the file should be terminated
                    break
            myshell.run_command("exit") # call exit at the end of the shell execution
        except FileNotFoundError as e:
            log.error(f"Cannot find the file specified for batch processing: \"{args.f}\". {e}")
    else:
        # 直接使用交互模式
        myshell()
