#!python
import os
import io
import sys
import getpass
import platform
import re
import copy
import logging
import coloredlogs
import datetime
import readline
import subprocess
import multiprocessing
import tempfile
import traceback
import argparse
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Process, Queue, Pipe, Pool, Manager, Value
from os import name
from COLOR import COLOR
from MyShellException import *
log = logging.getLogger(__name__)

coloredlogs.install(level='DEBUG')  # Change this to DEBUG to see more info.


# a decorator for logging function call
def logger(func):
    def wrapper(*args, **kwargs):
        log.debug(f"CALLING FUNCTION: {COLOR.BOLD(func)}")
        return func(*args, **kwargs)
    return wrapper


# a class decorator that can modify all callable class method with a decorator
# here we use this to log function call of sys.stdin wrapper
def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:  # there's propably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


# a dict that logs itself on every getting item operation
class LoggingDict(dict):
    def __getitem__(self, key):
        log.debug(f"GETTING DICT ITEM {COLOR.BOLD(key)}")
        return super().__getitem__(key)


@for_all_methods(logger)  # using the full class logging system
class StdinWrapper(io.TextIOWrapper):
    def __init__(self, queue, count, job, status_dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue
        self.job = job
        self.status_dict = status_dict
        self.count = count
        self.ok = False

    def job_status(self, status):
        self.status_dict[self.count] = status
        print(f"{COLOR.BOLD(COLOR.YELLOW(f'[{self.count}]'))} {COLOR.BOLD(status)} env {COLOR.BOLD(self.job)}")

    def isok(self):
        if not self.ok:
            log.debug("Aha! You want to read something? Wait on!")
            self.job_status("suspended")

            log.debug(f"WHAT IS SELF.STATUS_DICT: {self.status_dict}")
            log.debug(f"WHAT IS SELF.COUNT: {self.count}")

            content = self.queue.get()

            log.debug(f"WHAT DID YOU GET: {content}")

            self.isok = True

            self.job_status("running")

    def __getattribute__(self, name):
        log.debug(f"GETTING ATTRIBUTE: {COLOR.BOLD(name)}")
        return super().__getattribute__(name)

    def fileno(self):
        self.isok()
        return super().fileno()


class OnCallDict(dict):
    unsupported = ["HOME", "USER", "LOCATION", "SHELL"]
    reserved = unsupported + ["PATH", "PWD"]

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if callable(value):
            log.debug(f"Accessing callable dict element: {COLOR.BOLD(key)}")
            return value()
        else:
            log.debug(f"Accessing non-callable dict element: {COLOR.BOLD(key)}")
            return value

    def __setitem__(self, key, value):
        if key not in self:
            log.info(f"We might be copying current shell, setting value \"{value}\" to \"{key}\"")
            super().__setitem__(key, value)
            return
        elif key == "PATH":
            # for whatever reason, set this to a string (environment variables are meant to be strings)
            # here we're actually setting the REAL environ so that user can call stuff more conveniently
            # ? or should we
            log.info(f"User set PATH to {COLOR.BOLD(value)}")
            os.environ[key] = str(value)
        elif key == "PWD":
            # we're changing dir...
            # ? or should we just set variable
            log.info(f"User set PWD to {COLOR.BOLD(value)}")
            os.chdir(value)
        elif key in OnCallDict.unsupported:
            log.warning(f"Sorry, we don't currently support setting \"{key}\", included in {COLOR.BOLD(OnCallDict.unsupported)}")
        else:
            super().__setitem__(key, value)

    def __delitem__(self, key):
        if key in OnCallDict.reserved:
            log.warning(f"Sorry, we don't currently support deleting \"{key}\", included in {COLOR.BOLD(OnCallDict.reserved)}")
            raise ReservedKeyException(f"\"{key}\" is reserved, along with {OnCallDict.reserved}")
        else:
            super().__delitem__(key)


class MyShell:
    def __init__(self, dict_in={}):
        self.builtin_prefix = "builtin_"

        builtins = MyShell.__dict__.items()
        # builtins is a simple dict containing functions (not called on access)
        self.builtins = {}
        for key, value in builtins:
            if key.startswith(self.builtin_prefix):
                self.builtins[key[len(self.builtin_prefix)::]] = value

        # we're using callable dict to evaluate values on call
        self.vars = OnCallDict({
            "SHELL": os.path.abspath(__file__),
            "PWD": self.cwd,
            "HOME": self.home,
            "LOCATION": self.location,
            "USER": self.user,
            "PATH": self.path,
            "PS1": "$",
        })

        self.level = {
            "(": 0, ")": 0,
            "-z": 1, "-n": 1,
            "=": 2, "!=": 2, "-eq": 2, "-ge": 2, "-gt": 2, "-le": 2, "-lt": 2, "-ne": 2,
            "!": 3,
            "-a": 4, "-o": 4,
        }

        # ! damn strange... when an object has a Manager, multiprocessing refuse to spawn it on Windows
        # self.job_manager = Manager()
        self.jobs = Manager().dict()
        self.status_dict = Manager().dict()
        self.job_counter = 0
        self.queues = {}

        for key, value in dict_in.items():
            # user should not be tampering with the vars already defined
            # however we decided not to disturb them
            self.vars[key] = value

        log.debug(f"SHELL var content: {self.vars['SHELL']}")
        log.debug(f"Built in command list: {self.builtins}")
        log.debug("MyShell is instanciated.")

    def __call__(self):
        log.debug("This is MyShell.")
        exit_signal = False
        while not exit_signal:
            exit_signal = self.command_prompt()

    def builtin_bg(self, pipe="", args=[]):
        if len(args) != 1:
            raise JobException("Argument number is not correct, only one expected.", {"type": "len"})
        else:
            for arg in args:
                if arg not in self.jobs:
                    raise JobException(f"Cannot find job is jobs number \"{arg}\".", {"type": "key"})

        log.debug(f"Background is called with {COLOR.BOLD(args)}")
        for job_number in args:
            if self.status_dict[job_number] == "suspended":
                print(self.job_status_fmt(job_number, "running", self.jobs[job_number]))
                print(self.job_status_fmt(job_number, "suspended", self.jobs[job_number]))
            elif self.status_dict[job_number] == "running":
                log.warning(f"Job [{job_number}] is already running")

    def builtin_cd(self, pipe="", args=[]):
        if len(args):
            if len(args) > 1:
                log.warning("Are you trying to cd into multiple dirs? We'll only accept the first argument.")
            target_dir = args[0]
        else:
            # well, we'd like to stay in home
            # but the teacher says we should pwd instead
            # target_dir = self.home()
            return self.builtin_pwd(pipe=pipe, args=args)

        if target_dir.startswith("~"):
            target_dir = f"{self.home()}{target_dir[1::]}"
        # the dir might not exist
        try:
            log.info(f"Changing CWD to {COLOR.BOLD(target_dir)}")
            os.chdir(target_dir)
        except FileNotFoundError as e:
            raise FileNotFoundException(e, {"type": "cd"})

    def builtin_clr(self, pipe="", args=[]):
        # clear the screen
        # we're forced to do a system call here...
        if name == "nt":
            os.system("cls")
        else:
            os.system("clear")
        # return ""

    def path(self):
        return os.environ["PATH"]

    def get_mode(self, permissions):
        map_string = "rwxrwxrwx"
        map_empty = "---------"
        result = "".join([map_string[i] if permissions[i] else map_empty[i] for i in range(9)])
        return result

    def builtin_dir(self, pipe="", args=[]):
        if len(args):
            if len(args) > 1:
                log.warn("Are you trying to list content of multiple dirs? We'll only accept the first argument.")
            target_dir = args[0]
        else:
            target_dir = "."
        if target_dir.startswith("~"):
            target_dir = f"{self.home()}{target_dir[1::]}"
        # the dir might not exist
        try:
            result = []
            log.debug(f"Listing dir {COLOR.BOLD(target_dir)}")
            dir_list = os.listdir(target_dir)
            for file_name in dir_list:
                full_name = f"{target_dir}/{file_name}"
                file_stat = os.stat(full_name)
                # only getting the lower part
                file_mode = file_stat.st_mode
                # time
                file_time = file_stat.st_mtime
                # guess we're not using this...
                type_code = file_mode >> 12
                permissions = [(file_mode >> bit) & 1 for bit in range(9 - 1, -1, -1)]
                mode_str = self.get_mode(permissions)
                time_str = datetime.datetime.fromtimestamp(file_time).strftime("%Y-%m-%d %H:%M:%S")
                # print(time_str)
                file_line = f"{mode_str} {time_str} "
                if os.path.isdir(full_name):
                    # path is a directory
                    file_line += COLOR.BLUE(COLOR.BOLD(file_name))
                else:
                    # todo: maybe we can recognize char block or others
                    # this is brutal
                    if os.access(full_name, os.X_OK):
                        file_line += COLOR.RED(COLOR.BOLD(file_name))
                    else:
                        file_line += COLOR.BOLD(file_name)
                result.append(file_line)
            return "\n".join(result)
        except FileNotFoundError as e:
            raise FileNotFoundException(e, {"type": "dir"})

    def builtin_echo(self, pipe="", args=[]):
        result = f"{' '.join(args)}\n"
        return result

    def builtin_exec(self, pipe="", args=[]):
        pass

    def builtin_exit(self, pipe="", args=[]):
        raise ExitException("Exitting...")

    def builtin_environ(self, pipe="", args=[]):
        return "\n".join([f"{key}={COLOR.BOLD(self.vars[key])}" for key in self.vars])

    def builtin_fg(self, pipe="", args=[]):
        if len(args) != 1:
            raise JobException("Argument number is not correct, only one expected.", {"type": "len"})
        elif args[0] not in self.jobs:
            raise JobException(f"Cannot find job is jobs number \"{args[0]}\".", {"type": "key"})

        log.debug(f"Foreground is called with {COLOR.BOLD(args)}")
        self.queues[args[0]].put("dummy")

        log.info("Waiting for foreground task to finish...")

        self.queues[args[0]].get()
        log.debug("Continuing main process")
        # del self.queues[args[0]]
        # del self.jobs[args[0]]

    def builtin_help(self, pipe="", args=[]):
        pass

    @staticmethod
    def job_status_fmt(job_number, status, content):
        return f"{COLOR.BOLD(COLOR.YELLOW(f'[{job_number}]'))} {COLOR.BOLD(status)} env {COLOR.BOLD(content)}"

    def job_status(self, job_number, status=None):
        if status is not None:
            self.status_dict[job_number] = status
        else:
            status = self.status_dict[job_number]
        return self.job_status_fmt(job_number, status, self.jobs[job_number])

    def builtin_jobs(self, pipe="", args=[]):
        log.debug("Trying to get all jobs")
        log.info(f"Content of jobs {COLOR.BOLD(self.jobs)}")
        log.info(f"Content of status_dict {COLOR.BOLD(self.status_dict)}")
        result = [self.job_status(key) for key in self.jobs.keys()]
        return '\n'.join(result)

    def builtin_queues(self, pipe="", args=[]):
        log.debug("Trying to get all queues")
        log.info(f"Content of queues {COLOR.BOLD(self.queues)}")
        return str(self.queues)

    def builtin_pwd(self, pipe="", args=[]):
        cwd = self.cwd()
        if len(args) and args[0] == "-a" and cwd.startswith("~"):
            cwd = f"{self.home()}{cwd[1::]}"
        return cwd

    def builtin_quit(self, pipe="", args=[]):
        raise ExitException("Quitting...")

    def builtin_set(self, pipe="", args=[]):
        # we'd like the user to use the equal sign
        # and we'd like to treat varibles only as string
        for arg in args:
            split = arg.split("=")
            if len(split) != 2:
                raise SetPairUnmatchedException(f"Cannot match argument {arg}.", {"type": "set"})
            key, value = split
            log.debug(f"Setting \"{key}\" in environment variables to \"{value}\"")

            try:
                # might be error since self.vars is not a simple dict
                self.vars[key] = value
            except FileNotFoundError as e:
                raise FileNotFoundException(e, {"type": "set", "arg_pair": [key, value]})

    def builtin_shift(self, pipe="", args=[]):
        pass

    @staticmethod
    def test_unary(operator, operand):
        if operator == "-z":
            return not len(operand)
        if operator == "-n":
            return len(operand)
        if operator == "!":
            return not operand

        # todo: raise
        log.critical("Unrecoginized operator in a place it shouldn't be")
        raise TestException(f"Unrecognized unary operator \"{operator}\"")

    @staticmethod
    def test_binary(op, lhs, rhs):
        if op == "=":
            return lhs == rhs
        if op == "!=":
            return lhs != rhs
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
            return lhs and rhs
        elif op == "-o":
            return lhs or rhs

        # todo: raise
        log.critical("Unrecoginized operator in a place it shouldn't be")
        raise TestException(f"Unrecognized binary operator \"{operator}\"")

    def expand_expr(self, args):
        try:
            ind = 0
            if len(args) == 1:
                return args[0]

            if args[ind] not in self.level:
                lhs = args[ind]
                # not possible
                # if ind == len(args)-1:
                #     return lhs
                op = args[ind+1]
                rhs = self.expand_expr(args[ind+2::])
                return self.test_binary(op, lhs, rhs)

            # match parentheses
            if args[ind] == "(":
                org = ind
                while args[ind] != ")":
                    ind += 1
                lhs = self.expand_expr(args[org+1:ind])
                if ind == len(args)-1:
                    return lhs
                op = args[ind+1]
                rhs = self.expand_expr(args[ind+2::])
                return self.test_binary(op, lhs, rhs)

            if self.level[args[ind]] in [1, 3]:
                op = args[ind]
                oa, ind = self.get_one(args[ind+1::])
                lhs = self.test_unary(op, oa)
                if ind == len(args)-1:
                    return lhs
                op = args[ind+1]
                rhs = self.expand_expr(args[ind+2::])
                return self.test_binary(op, lhs, rhs)

        except (ValueError, KeyError) as e:
            raise TestException(e)

    def get_one(self, args):

        ind = 0
        if len(args) == 1:
            return args[0], 1

        if args[ind] == "(":
            org = ind
            while args[ind] != ")":
                ind += 1
            return self.expand_expr(args[org+1:ind]), ind+1

        if self.level[args[ind]] in [1, 3]:
            op = args[ind]
            oa, ind = self.get_one(args[ind+1::])
            return self.test_unary(op, oa), ind + 1

    def builtin_test(self, pipe="", args=[]):
        # we can only use print to pass values

        tf = {
            True: "True",
            False: "False",
        }

        return tf[bool(self.expand_expr(args))]
        # todo: fill in the hole
        # try:
        #     self.subshell(target="test", args=args, pipe=pipe, piping=True)
        #     return "True"
        # except CalledProcessException as e:
        #     return "False"

    def builtin_time(self, pipe="", args=[]):
        return str(datetime.datetime.now())

    def builtin_umask(self, pipe="", args=[]):
        if len(args) > 1:
            raise UmaskException("Argument number is not correct, only one or zero expected.", {"type": "len"})
        elif len(args) == 1:
            try:
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
            return "0o{:03o}".format(old)

    def builtin_unset(self, pipe="", args=[]):
        keys = []
        for key in args:
            try:
                del self.vars[key]
            except (KeyError, ReservedKeyException):
                keys.append(key)
        if len(keys):
            raise UnsetKeyException("Cannot find/unset these keys.", {"keys": keys})

    def builtin_dummy(self, pipe="", args=[]):
        # result = sys.stdin.readline()
        print("builtin_dummy: before any input requirements")
        print(input("dummy1> "))
        print(input("dummy2> "))
        print(input("dummy3> "))
        print(input("dummyend> "))

    def builtin_check_zombie(self, pipe="", args=[]):
        any_process = -1
        while True:
            try:
                # This will raise an exception on Windows.  That's ok.
                pid, status = os.waitpid(any_process, os.WNOHANG)
                if pid == 0:
                    break
                log.error(f"I don't know wtf this is... {COLOR.BOLD(str(pid) + ', ' + str(status))}")
                if os.WIFEXITED(status):
                    log.error(f"The job of pid \"{pid}\" is done.")
                if os.WIFSTOPPED(status):
                    log.error(f"The job of pid \"{pid}\" is suspended.")
                if os.WIFCONTINUED(status):
                    log.error(f"The job of pid \"{pid}\" is continued.")
            except:
                break

    def subshell(self, pipe="", target="", args=[], piping=False, io_control=False):
        if not target:
            raise EmptyException(f"Command \"{target}\" is empty", {"type": "subshell"})
        to_run = [target] + args
        log.debug(f"Runnning in subprocess: {COLOR.BOLD(to_run)}")
        result = None
        if piping:
            log.debug("Piping in subprocess...")
            # log.debug(f"content of pipe varible {COLOR.BOLD(pipe)}")
            p = subprocess.run(to_run, stdout=PIPE, input=pipe, stderr=STDOUT, encoding="utf-8", env=dict(os.environ, PARENT=self.vars["SHELL"]))
            result = str(p.stdout)
            # waits for the process to end
        elif io_control:
            # todo: cry
            log.debug("Doing io control")
            log.debug(f"Multiprocessing IO controller is: {sys.stdin}")
            p = subprocess.Popen(to_run, stdin=PIPE, stdout=None, stderr=STDOUT, encoding="utf-8", env=dict(os.environ, PARENT=self.vars["SHELL"]))

            # p.wait()
            # p.stdin.write("hello\n")
            result, error = p.communicate()
            # result = str(p.stdout)
            log.debug(f"The result is \"{result}\" and \"{error}\"")
            # waits for the process to end
        else:
            log.debug("Just running in regular env")
            p = subprocess.run(to_run, stderr=STDOUT, encoding="utf-8", env=dict(os.environ, PARENT=self.vars["SHELL"]))
            # here we're directing the IO straight to the command line, so no result is needed
            # waits for the process to end
        if p.returncode != 0:
            log.warning("The subprocess is not returning zero exit code")
            raise CalledProcessException("None zero return code encountered")
        # log.debug(f"Raw string content: {COLOR.BOLD(result)}")
        return result

    def cleanup(self):
        keys = list(self.queues.keys())
        log.debug(f"Queue is being cleaned, previous keys are {COLOR.BOLD(keys)}")
        for i in keys:
            if i not in self.jobs.keys():
                del self.queues[i]
        log.debug(f"Queue is cleaned, keys are {COLOR.BOLD(self.queues.keys())}")

    def home(self):
        return os.environ['HOME']

    def cwd(self):
        cwd = os.getcwd()
        if cwd.startswith(self.home()):
            cwd = f"~{cwd[len(self.home())::]}"
        return cwd

    def user(self):
        return getpass.getuser()

    def location(self):
        return platform.node()

    def prompt(self):
        prompt = f"{COLOR.BEIGE(self.user()+'@'+self.location())} {COLOR.BOLD(COLOR.BLUE(self.cwd()))} {COLOR.BOLD(COLOR.YELLOW(self.vars['PS1']))} "
        # log.debug(repr(prompt))
        try:
            conda = os.environ["CONDA_DEFAULT_ENV"]
            prompt = f"({conda}) {prompt}"
        except KeyError:
            pass  # not a conda environment
        return prompt

    def execute(self, command, pipe=""):
        log.info(f"Executing command {COLOR.BOLD(command['exec'])}")
        log.info(f"Arguments are {COLOR.BOLD(command['args'])}")
        # log.debug(f"Full content of command is {COLOR.BOLD(command)}")
        if command["pipe_in"] and command["redi_in"]:
            raise MultipleInputException("Redirection and pipe are set as input at the same time.")
        if command["pipe_in"] or command["redi_in"] or command["redi_out"] or command["pipe_out"]:
            command["piping"] = True
        else:
            command["piping"] = False

        # to the command itself, it doesn't matter whether the input comes from a pipe or file
        if command["redi_in"]:
            file_path = command["redi_in"]
            try:
                # the function open will automatically raise FileNotFoundError
                f = open(file_path, "r")
            except FileNotFoundError as e:
                raise FileNotFoundException(e, {"type": "redi_in"})
            pipe = f.read()

        result = ""
        if command["exec"] in self.builtins.keys():
            log.debug("This is a builtin command.")
            # executing as static method, calling with self variable
            result = self.builtins[command["exec"]](self, pipe=pipe, args=command['args'])
        else:
            log.debug("This is not a builtin command.")
            try:
                result = self.subshell(pipe, command["exec"], command['args'], piping=command["piping"], io_control=command["io_control"])
            except FileNotFoundError as e:
                raise FileNotFoundException(e, {"type": "subshell"})

        if command['redi_out']:
            log.debug(f"User want to redirect the output to {COLOR.BOLD(command['redi_out'])}")
            if command["redi_append"]:
                try:
                    f = open(command["redi_out"], "a")
                    f.write(result)
                except FileNotFoundError as e:
                    raise FileNotFoundException(e, {"type": "redi_out", "redi_append": True})
            else:
                try:
                    f = open(command["redi_out"], "w")
                    f.write(result)
                except FileNotFoundError as e:
                    raise FileNotFoundException(e, {"type": "redi_out", "redi_append": False})
            return result

        if command['pipe_out']:
            log.debug(f"User want to pipe the IO")
            return result

        if result is not None:
            print(result, end="" if result.endswith("\n") or not len(result) else "\n")
        # return result # won't be used anymore

    def command_prompt(self):
        # strange error if we use input
        # the input and readline prompt seems to be counting color char as one of the line chars
        # well it turns out to be a quirk of readline
        # we've fixed it in COLOR.py
        command = input(self.prompt()).strip()
        # print(self.prompt(), end="")
        # command = input().strip()
        log.debug(f"Getting user input: {COLOR.BOLD(command)}")
        result = self.run_command(command)
        return result

    @staticmethod
    def run_command_wrap(count, shell, args, job, queue, jobs, status_dict):
        log.debug(f"Wrapper [{count}] called with {COLOR.BOLD(f'{shell} and {args}')}")

        if sys.stdin is not None:
            sys.stdin.close()
        stdin = open(0)
        buffer = stdin.detach()
        wrapper = StdinWrapper(queue, count, job, status_dict, buffer)
        sys.stdin = wrapper

        try:
            shell.run_command(args, io_control=True)
        finally:
            print(shell.job_status_fmt(count, "finished", job))
            queue.put("dummy")
            del jobs[count]
            del status_dict[count]

    def run_command(self, command, io_control=False):
        try:
            # todo: finish subprocess here...
            commands, is_bg = self.parse(command)
            if is_bg:
                # ! changes made in subprocess is totally within the subprocess only
                # todo: the counter might get significantly large
                str_cnt = str(self.job_counter)
                self.jobs[str_cnt] = command
                self.queues[str_cnt] = Queue()
                self.status_dict[str_cnt] = "running"
                p = Process(target=self.run_command_wrap, args=(str_cnt, self, command[0:-1], self.jobs[str_cnt], self.queues[str_cnt], self.jobs, self.status_dict), name=command)
                p.start()
                self.job_counter += 1
                log.debug(f"We've spawned the job in a Process for command: {COLOR.BOLD(p.name)}")
            else:
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
            log.debug("User is exiting...")
            log.debug(f"Exception says: {e}")
            log.info("Bye")
            return True
        except EmptyException as e:
            log.debug("The command is empty...")
            log.info(f"Exception says: {e}")
            if e.errors["type"] == "pipe":
                log.error(f"Your pipe is incomplete. {e}")
            elif e.errors["type"] == "subshell":
                log.warning(f"Your command is empty. Did you use an empty var? {e}")
            elif e.errors["type"] == "empty":
                log.info(f"Your command is empty. {e}")
        except MultipleInputException as e:
            log.debug("Syntax error, user want to use input from pipe and redirection...")
            log.info(f"Exception says: {e}")
            log.error(f"Cannot handle multiple inputs at the same time. {e}")
        except FileNotFoundException as e:
            log.debug("IO error, cannot find the file specified")
            log.info(f"Exception says: {e}")
            if e.errors["type"] == "redi_in":
                log.error(f"Cannot find file at command \"{command['exec']}\" of position {cidx} for input. {e}")
            elif e.errors["type"] == "redi_out":
                if e.errors["redi_append"]:
                    log.error(f"Cannot find/write to file at command \"{command['exec']}\" of position {cidx} for appending output, check for file permission. {e}")
                else:
                    log.error(f"Cannot open/write to file at command \"{command['exec']}\" of position {cidx} for updating output, check for file permission. {e}")
            elif e.errors["type"] == "cd":
                log.error(f"Cannot find file at command \"{command['exec']}\" of position {cidx} for directory changing. {e}")
            elif e.errors["type"] == "dir":
                log.error(f"Cannot find file at command \"{command['exec']}\" of position {cidx} for directory listing. {e}")
            elif e.errors["type"] == "subshell":
                log.error(f"Cannot find an external or internal command \"{command['exec']}\" of position {cidx} for an external process spawning. {e}")
            elif e.errors["type"] == "set":
                log.error(f"Setting environment {e.errors['arg_pair'][0]} to {e.errors['arg_pair'][1]} failed. You're probably setting PWD and we're unable to find a proper place to cd into... {e}")
        except QuoteUnmatchedException as e:
            log.debug("We've encountered quote unmatch error...")
            log.info(f"Exception says: {e}")
            # currently the command is still a string
            log.error(f"Cannot match quote for command \"{command}\". {e}")
        except CalledProcessException as e:
            log.debug("We've encountered error in a subprocess")
            log.info(f"Exception says: {e}")
            # currently the command is still a string
            log.warning(f"Cannot run process successfully with command \"{command['exec']}\". {e}")
        except UnsetKeyException as e:
            log.debug("Exception when unsetting keys")
            log.info(f"Exception says: {e}")
            # currently the command is still a string
            log.warning(f"Cannot unset \"{e.errors['keys']}\" using command \"{command['exec']}\". {e}")
        except SetPairUnmatchedException as e:
            log.debug("Exception when unsetting keys")
            log.info(f"Exception says: {e}")
            if e.errors["type"] == "redi":
                log.error(f"Cannot set redirection using command \"{command}\". {e}")
            elif e.errors["type"] == "set":
                log.error(f"Cannot set keys using command \"{command['exec']}\". {e}")
        except UnexpectedAndException as e:
            log.debug("Exception when parsing command")
            log.info(f"Exception says: {e}")
            # currently the command is still a string
            log.error(f"Cannot interpret & sign in command \"{command}\". {e}")
        except JobException as e:
            log.debug("Exception when managing jobs")
            log.info(f"Exception says: {e}")
            if e.errors["type"] == "len":
                log.error(f"Error number of argements in command \"{command['exec']}\", {e}")
            elif e.errors["type"] == "key":
                log.error(f"Error job number in command \"{command['exec']}\", {e}")
        except UmaskException as e:
            log.debug("Exception when managing jobs")
            log.info(f"Exception says: {e}")
            if e.errors["type"] == "len":
                log.error(f"Error number of argements in command \"{command['exec']}\", {e}")
            elif e.errors["type"] == "value":
                log.error(f"Unable to interpret umask value in command \"{command['exec']}\", {e}")

        except TestException as e:
            log.debug("Error during test command")
            log.info(f"Exception says: {e}")
            log.error(f"Unable to perform \"{command['exec']}\", please check your syntax and operator match. {e}")
        except Exception as e:
            log.error(f"Unhandled error. {traceback.format_exc()}")
        finally:
            self.cleanup()  # always clean up

        return False

    def parse(self, command):
        inputs = self.quote(command)  # splitting by whitespace and processing varibles, quotes
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

        # print(commands)

        is_bg = False
        parsed_commands = []
        parsed_command = self.parsed_clean()

        for cidx, command in enumerate(commands):
            if not len(command):
                raise EmptyException(f"Command at position {cidx} is empty", {"type": "pipe" if len(commands) > 1 else "empty"})
            parsed_command["pipe_in"] = (cidx > 0)
            parsed_command["pipe_out"] = (cidx != len(commands)-1)
            index = 0
            while index < len(command):
                if not index:  # this should have a larger priority
                    parsed_command["exec"] = command[index]
                elif command[index] == "<":
                    if index == len(command) - 1:
                        raise SetPairUnmatchedException("Cannot match redirection input file with < sign.", {"type": "redi"})
                    parsed_command["redi_in"] = command[index+1]
                    index += 1
                elif command[index] == ">":
                    if index == len(command) - 1:
                        raise SetPairUnmatchedException("Cannot match redirection output file with > sign.", {"type": "redi"})
                    parsed_command["redi_out"] = command[index+1]
                    index += 1
                elif command[index] == ">>":
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
            parsed_command = self.parsed_clean()

        return parsed_commands, is_bg

    def quote(self, command, quote=True):
        # command should already been splitted by word
        # mark: this structure makes it possible that the arg is keep in one place if using quote
        # by not brutally expanding on every possible environment variables
        command = command.split()
        quote_stack = []
        index = 0
        while index < len(command):
            if command[index].count("\"") >= 1:
                # should remove all quotes here
                quote_count = command[index].count("\"")
                log.debug("Trying to remove quote...")
                splitted = command[index].split("\"")
                # there were not space at the beginning
                command[index] = "".join([self.expand(split) for split in splitted])

            else:
                quote_count = 0

            if quote_count % 2:  # previous quote_count
                if quote_stack:
                    # except the last char
                    quote_stack.append(command[index])
                    # recursion to process $ and "" in the already processed ""
                    command[index] = self.expand(" ".join(quote_stack))
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
                # no quote but
                quote_stack.append(command[index])
                if index == len(command)-1:
                    raise QuoteUnmatchedException("Cannot match the quote for a series of arguments")
                command = command[0:index] + command[index+1::]
                index -= 1  # index should stay the same

            prev = command[index]
            command[index] = self.expand(command[index])
            if prev == command[index]:
                index += 1  # advance only if the var is unchanged

        return command

    def expand(self, string):
        # log.debug(f"The string to be expanded is: {COLOR.BOLD(string)}")
        # string = re.sub(r"~", self.home(), string)
        string = string.replace("~", self.home())
        var_list = [(m.start(0), m.end(0)) for m in re.finditer(r"\$\w+", string)]
        str_list = []
        prev = [0, 0]
        for start, end in var_list:
            str_list.append(string[prev[1]:start])
            str_list.append(string[start:end])
            prev = [start, end]

        str_list.append(string[prev[1]::])

        # log.debug(f"The splitted vars are {COLOR.BOLD(str_list)}")

        for i in range(1, len(str_list), 2):
            key = str_list[i][1::]
            log.debug(f"Trying to get varible {COLOR.BOLD(key)}")
            try:
                var = self.vars[key]
                log.debug(f"Got the varible {COLOR.BOLD(var)}")
            except KeyError as e:
                log.warning(f"Unable to get the varible \"{key}\", assigning empty string")
                var = ""
            # splitting the expanded command since it might contain some information
            str_list[i] = var
            # to result in index staying the same

        string = "".join(str_list)
        return string

    def parsed_clean(self):
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


def main(args):

    if args.e:
        coloredlogs.set_level("ERROR")
    if args.w:
        coloredlogs.set_level("WARNING")
    if args.i:
        coloredlogs.set_level("INFO")
    if args.d:
        coloredlogs.set_level("DEBUG")

    # myshell = MyShell({"TEST": "echo \"echo $SHELL\""})
    myshell = MyShell()
    log.debug(f"Getting user command line argument(s): {COLOR.BOLD(args)}")
    # todo: batch process

    if args.f:
        try:
            for file_name in args.f:
                # ! using utf-8
                f = open(file_name, encoding="utf-8")  # opending the file specified
                for line in f:
                    line = line.strip()
                    myshell.run_command(line)  # execute line by line
        except FileNotFoundError as e:
            log.error(f"Cannot find the file specified for batch processing: \"{file_name}\". {e}")
    else:
        myshell()


if __name__ == "__main__":
    # hello -n "world" < input.txt | tr -d -c "re"
    # echo "zy" | sha256sum | tr -d " -" | wc
    parser = argparse.ArgumentParser(description='MyShell by xudenden@gmail.com')
    parser.add_argument('f', metavar='F', type=str, nargs='*', help='the batch file to be executed')
    parser.add_argument('-e', help='enable error level debugging info log', action='store_true')
    parser.add_argument('-w', help='enable warning level debugging info log', action='store_true')
    parser.add_argument('-i', help='enable info level debugging info log', action='store_true')
    parser.add_argument('-d', help='enable debug(verbose) level debugging info log', action='store_true')

    args = parser.parse_args()
    main(args)
