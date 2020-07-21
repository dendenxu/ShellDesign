#!python
import os
import sys
import pwd
import copy
import subprocess
import logging
import coloredlogs
import datetime
import readline
from os import name
from COLOR import COLOR
from MyShellException import *
log = logging.getLogger(__name__)

coloredlogs.install(level='DEBUG')  # Change this to DEBUG to see more info.


class OnCallDict(dict):
    def __getitem__(self, key):
        value = super().__getitem__(key)
        if callable(value):
            log.debug(f"Accessing callable dict element: {COLOR.BOLD(key)}")
            return value()
        else:
            log.debug(f"Accessing non-callable dict element: {COLOR.BOLD(key)}")
            return value


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
            "SHELL": __file__[0:-3],
            "PWD": self.cwd,
            "HOME": self.home,
            "LOCATION": self.location,
            "USER": self.user,
        })

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
        pass

    def builtin_cd(self, pipe="", args=[]):
        if len(args):
            if len(args) > 1:
                log.warn("Are you trying to cd into multiple dirs? We'll only accept the first argument.")
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
            log.debug(f"Changing CWD to {COLOR.BOLD(target_dir)}")
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
        return ""

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
        result = ""
        for arg in args:
            result += f"{arg} "
        return result

    def builtin_exec(self, pipe="", args=[]):
        pass

    def builtin_exit(self, pipe="", args=[]):
        raise ExitException("Exitting...")

    def builtin_environ(self, pipe="", args=[]):
        pass

    def builtin_fg(self, pipe="", args=[]):
        pass

    def builtin_help(self, pipe="", args=[]):
        pass

    def builtin_jobs(self, pipe="", args=[]):
        pass

    def builtin_pwd(self, pipe="", args=[]):
        cwd = self.cwd()
        if len(args) and args[0] == "-a" and cwd.startswith("~"):
            cwd = f"{self.home()}{cwd[1::]}"
        return cwd

    def builtin_quit(self, pipe="", args=[]):
        raise ExitException("Quitting...")

    def builtin_set(self, pipe="", args=[]):
        pass

    def builtin_shift(self, pipe="", args=[]):
        pass

    def builtin_test(self, pipe="", args=[]):
        pass

    def builtin_time(self, pipe="", args=[]):
        return datetime.datetime.now()

    def builtin_unmask(self, pipe="", args=[]):
        pass

    def builtin_unset(self, pipe="", args=[]):
        pass

    def ps1(self):
        return "$"

    def home(self):
        return os.environ['HOME']

    def cwd(self):
        cwd = os.getcwd()
        if cwd.startswith(self.home()):
            cwd = f"~{cwd[len(self.home())::]}"
        return cwd

    def user(self):
        return pwd.getpwuid(os.getuid())[0]

    def location(self):
        return os.uname()[1]

    def prompt(self):
        prompt = f"{COLOR.BEIGE(self.user()+'@'+self.location())} {COLOR.BLUE(COLOR.BOLD(self.cwd()))} {COLOR.YELLOW(COLOR.BOLD(self.ps1()))} "
        # log.debug(repr(prompt))
        return prompt

    def execute(self, command, pipe=""):
        log.debug(f"Executing command {COLOR.BOLD(command['exec'])}")
        log.debug(f"Arguments are {COLOR.BOLD(command['args'])}")

        if command["pipe_in"] and command["redi_in"]:
            raise MultipleInputException("Redirection and pipe are set as input at the same time.")

        # todo: finish possible redirection from input file

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
            result = self.builtins[command["exec"]](self, pipe=pipe, args=command['args'])
        else:
            log.debug("This is not a builtin command.")
            # todo: finish executing none builtin command
            # this is a placeholder
            result = "PLACEHOLDER"

        if command['redi_out']:
            log.debug(f"User want to redirect the output to {COLOR.BOLD(command['redi_out'])}")
            # todo: write to file
            return result

        if command['pipe_out']:
            log.debug(f"User want to pipe the IO")
            return result

        if result is not None:
            print(result)
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

        try:
            commands = self.parse(command)
            result = ""
            for cidx, command in enumerate(commands):
                result = self.execute(command, pipe=result)
        except ExitException as e:
            log.debug("User is exiting...")
            log.debug(f"Exception says: {e}")
            log.info("Bye")
            return True
        except EmptyException as e:
            log.debug("The command is empty...")
            log.debug(f"Exception says: {e}")
            if e.errors["pipe"]:
                log.error(f"Your pipe is incomplete. {e}")
        except MultipleInputException as e:
            log.debug("Syntax error, user want to use input from pipe and redirection...")
            log.debug(f"Exception says: {e}")
            log.error(f"Cannot handle multiple inputs at the same time. {e}")
        except FileNotFoundException as e:
            log.debug("IO error, cannot find the file specified")
            log.debug(f"Exception says: {e}")
            if e.errors["type"] == "redi_in":
                log.error(f"Cannot find file at command \"{command['exec']}\" of position {cidx} for input. {e}")
            elif e.errors["type"] == "redi_out":
                # if this exception is raised here, output must being appended to a file
                log.error(f"Cannot find file at command \"{command['exec']}\" of position {cidx} for appending output. {e}")
            elif e.errors["type"] == "cd":
                log.error(f"Cannot find file at command \"{command['exec']}\" of position {cidx} for directory changing. {e}")
            elif e.errors["type"] == "dir":
                log.error(f"Cannot find file at command \"{command['exec']}\" of position {cidx} for directory listing. {e}")
        except QuoteUnmatchedException as e:
            log.debug("We've encountered quote unmatch error...")
            log.debug(f"Exception says: {e}")
            # currently the command is still a string
            log.error(f"Cannot match quote for command \"{command}\". {e}")
        # Returning exit signal
        return False

    def parse(self, command):
        inputs = self.process_dollar_quote(command)  # splitting by whitespace and processing varibles, quotes
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

        parsed_commands = []
        parsed_command = self.parsed_clean()

        for cidx, command in enumerate(commands):
            if not len(command):
                raise EmptyException(f"Command at position {cidx} is empty", {"pipe": len(commands) > 1})
            parsed_command["pipe_in"] = (cidx > 0)
            parsed_command["pipe_out"] = (cidx != len(commands)-1)
            index = 0
            while index < len(command):
                if not index:  # this should a larger priority
                    parsed_command["exec"] = command[index]
                elif command[index] == "<":
                    parsed_command["redi_in"] = command[index+1]
                    index += 1
                elif command[index] == ">":
                    parsed_command["redi_out"] = command[index+1]
                    index += 1
                elif command[index] == ">>":
                    parsed_command["redi_out"] = command[index+1]
                    parsed_command["redi_append"] = True
                    index += 1
                else:
                    parsed_command["args"].append(command[index])
                index += 1
            parsed_commands.append(parsed_command)
            parsed_command = self.parsed_clean()

        return parsed_commands

    def process_dollar_quote(self, command):
        # command should already been splitted by word
        command = command.split()
        quote_stack = ""
        index = 0
        while index < len(command):
            if quote_stack:
                if command[index].endswith("\""):
                    # except the last char
                    quote_stack += f" {command[index][0:-1]}"
                    # recursion to process $ and "" in the already processed ""
                    command[index] = ' '.join(self.process_dollar_quote(quote_stack))
                    quote_stack = ""
                    # index should continue to be added in the end
                else:
                    quote_stack += f" {command[index]}"
                    if index == len(command)-1:
                        raise QuoteUnmatchedException("Cannot match the quote for a series of arguments")
                    command = command[0:index] + command[index+1::]
                    index -= 1  # index should stay the same
            elif command[index].startswith("\""):
                if command[index].endswith("\"") and len(command[index]) > 1:
                    # getting the inner command
                    command[index] = command[index][1:-1]
                else:
                    log.debug("Trying to match quote...")
                    quote_stack += f" {command[index][1::]}"
                    # todo: might be an error
                    if index == len(command)-1:
                        raise QuoteUnmatchedException("Cannot match the quote for the last argument")
                    command = command[0:index] + command[index+1::]
                index -= 1
            elif command[index].startswith("$"):
                log.debug(f"Trying to get varible {COLOR.BOLD(command[index])}")
                try:
                    command[index] = self.vars[command[index][1::]]  # getting variable
                    log.debug(f"Got the varible {COLOR.BOLD(command[index])}")
                except KeyError as e:
                    command[index] = ""
                    log.debug("Unable to get the varible, assigning empty string")
                # splitting the expanded command since it might contain some information
                command = command[0:index] + command[index].split() + command[index + 1::]
                # to result in index staying the same
                index -= 1
            index += 1
        # if quote_stack:
        #     raise QuoteUnmatchedException("Cannot match the quote for a series of arguments")
        return command

    def parsed_clean(self):
        parsed_command = {}
        parsed_command["exec"] = ""
        parsed_command["args"] = []
        parsed_command["pipe_in"] = False
        parsed_command["pipe_out"] = False
        parsed_command["redi_in"] = ""
        parsed_command["redi_out"] = ""
        parsed_command["redi_append"] = False
        parsed_command["background"] = False
        return parsed_command


def main():
    myshell = MyShell({"TEST": "echo \"echo $SHELL\""})
    myshell()


if __name__ == "__main__":
    # hello -n "world" < input.txt | tr -d -c "re"
    main()
