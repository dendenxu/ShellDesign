import os
import sys
import pwd
import copy
import subprocess
import logging
import coloredlogs
import datetime
from os import name
log = logging.getLogger(__name__)

coloredlogs.install(level='DEBUG')  # Change this to DEBUG to see more info.


class MyShellException(Exception):
    """
    raised when we cannot find a particular key
    or duplication occurs
    """

    def __init__(self, message, errors=None):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class MultipleInputException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class ExitException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class EmptyException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class FileNotFoundException(MyShellException):
    def __init__(self, message, errors=None):
        super().__init__(message, errors)

class COLOR:
    @staticmethod
    def BOLD(string): return f'\33[1m{string}\33[0m'
    @staticmethod
    def ITALIC(string): return f'\33[3m{string}\33[0m'
    @staticmethod
    def URL(string): return f'\33[4m{string}\33[0m'
    @staticmethod
    def BLINK(string): return f'\33[5m{string}\33[0m'
    @staticmethod
    def BLINK2(string): return f'\33[6m{string}\33[0m'
    @staticmethod
    def SELECTED(string): return f'\33[7m{string}\33[0m'
    @staticmethod
    def BLACK(string): return f'\33[30m{string}\33[0m'
    @staticmethod
    def RED(string): return f'\33[31m{string}\33[0m'
    @staticmethod
    def GREEN(string): return f'\33[32m{string}\33[0m'
    @staticmethod
    def YELLOW(string): return f'\33[33m{string}\33[0m'
    @staticmethod
    def BLUE(string): return f'\33[34m{string}\33[0m'
    @staticmethod
    def VIOLET(string): return f'\33[35m{string}\33[0m'
    @staticmethod
    def BEIGE(string): return f'\33[36m{string}\33[0m'
    @staticmethod
    def WHITE(string): return f'\33[37m{string}\33[0m'
    @staticmethod
    def BLACKBG(string): return f'\33[40m{string}\33[0m'
    @staticmethod
    def REDBG(string): return f'\33[41m{string}\33[0m'
    @staticmethod
    def GREENBG(string): return f'\33[42m{string}\33[0m'
    @staticmethod
    def YELLOWBG(string): return f'\33[43m{string}\33[0m'
    @staticmethod
    def BLUEBG(string): return f'\33[44m{string}\33[0m'
    @staticmethod
    def VIOLETBG(string): return f'\33[45m{string}\33[0m'
    @staticmethod
    def BEIGEBG(string): return f'\33[46m{string}\33[0m'
    @staticmethod
    def WHITEBG(string): return f'\33[47m{string}\33[0m'
    @staticmethod
    def GREY(string): return f'\33[90m{string}\33[0m'
    @staticmethod
    def RED2(string): return f'\33[91m{string}\33[0m'
    @staticmethod
    def GREEN2(string): return f'\33[92m{string}\33[0m'
    @staticmethod
    def YELLOW2(string): return f'\33[93m{string}\33[0m'
    @staticmethod
    def BLUE2(string): return f'\33[94m{string}\33[0m'
    @staticmethod
    def VIOLET2(string): return f'\33[95m{string}\33[0m'
    @staticmethod
    def BEIGE2(string): return f'\33[96m{string}\33[0m'
    @staticmethod
    def WHITE2(string): return f'\33[97m{string}\33[0m'
    @staticmethod
    def GREYBG(string): return f'\33[100m{string}\33[0m'
    @staticmethod
    def REDBG2(string): return f'\33[101m{string}\33[0m'
    @staticmethod
    def GREENBG2(string): return f'\33[102m{string}\33[0m'
    @staticmethod
    def YELLOWBG2(string): return f'\33[103m{string}\33[0m'
    @staticmethod
    def BLUEBG2(string): return f'\33[104m{string}\33[0m'
    @staticmethod
    def VIOLETBG2(string): return f'\33[105m{string}\33[0m'
    @staticmethod
    def BEIGEBG2(string): return f'\33[106m{string}\33[0m'
    @staticmethod
    def WHITEBG2(string): return f'\33[107m{string}\33[0m'


class MyShell:
    def __init__(self):
        self.builtin_prefix = "builtin_"

        builtins = MyShell.__dict__.items()
        self.builtins = {}
        for key, value in builtins:
            if key.startswith(self.builtin_prefix):
                self.builtins[key[len(self.builtin_prefix)::]] = value
        self.vars = {
            "shell": __file__[0:-3],
        }
        log.debug(f"shell var content: {self.vars['shell']}")
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
            if len(args)>1:
                log.warn("Are you trying to cd into multiple dirs? We'll only accept the first argument.")
            target_dir = args[0]
        else:
            target_dir = self.home

        # the dir might not exist
        try:
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

    def builtin_dir(self, pipe="", args=[]):
        pass

    def builtin_echo(self, pipe="", args=[]):
        pass

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
        return self.cwd

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

    @property
    def ps1(self):
        return "$"

    @property
    def home(self):
        return os.environ['HOME']

    @property
    def cwd(self):
        cwd = os.getcwd()
        if cwd.startswith(self.home):
            cwd = f"~{cwd[len(self.home)::]}"
        return cwd

    @property
    def user(self):
        return pwd.getpwuid(os.getuid())[0]

    @property
    def location(self):
        return os.uname()[1]

    @property
    def prompt(self):
        return f"{COLOR.BEIGE(self.user+'@'+self.location)} {COLOR.BOLD(COLOR.BLUE(self.cwd))} {COLOR.BOLD(COLOR.YELLOW(self.ps1))} "

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
                raise FileNotFoundException(e, {"type":"redi_in"})
            pipe = f.read()

        result = ""
        if command["exec"] in self.builtins.keys():
            log.debug("This is a builtin command.")
            result = self.builtins[command["exec"]](self, pipe=pipe, args=command['args'])
        else:
            log.debug("This is not a builtin command.")
            # todo: finish executing none builtin command

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
        print(self.prompt, end="")
        command = input().strip()
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
        # Returning exit signal
        return False

    def parse(self, command):
        inputs = command.split()  # splitting by whitespace
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
            parsed_command["exec"] = command[0]
            command = command[1::]
            index = 0
            while index < len(command):
                if command[index] == "<":
                    parsed_command["redi_in"] = command[index+1]
                    index += 1
                elif command[index] == ">":
                    parsed_command["redi_out"] = command[index+1]
                    index += 1
                elif command[index] == ">>":
                    parsed_command["redi_out"] = command[index+1]
                    parsed_command["redi_append"] = True
                    index += 1
                elif command[index].startswith("$"):
                    log.debug(f"Trying to get varible {COLOR.BOLD(command[index])}")
                    try:
                        command[index] = self.vars[command[index][1::]] # getting variable
                        log.debug(f"Got the varible {COLOR.BOLD(command[index])}")
                    except KeyError as e:
                        command[index] = ""
                        log.debug("Unable to get the varible, assigning empty string")
                    parsed_command["args"].append(command[index])
                else:
                    parsed_command["args"].append(command[index])
                index += 1
            parsed_commands.append(parsed_command)
            parsed_command = self.parsed_clean()

        return parsed_commands

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
    myshell = MyShell()
    myshell()


if __name__ == "__main__":
    # hello -n "world" < input.txt | tr -d -c "re"
    main()
