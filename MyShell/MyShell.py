import os
import sys
import pwd
import copy
import subprocess
import logging
import coloredlogs
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


class Colors:
    END = '\33[0m'
    BOLD = '\33[1m'
    ITALIC = '\33[3m'
    URL = '\33[4m'
    BLINK = '\33[5m'
    BLINK2 = '\33[6m'
    SELECTED = '\33[7m'

    BLACK = '\33[30m'
    RED = '\33[31m'
    GREEN = '\33[32m'
    YELLOW = '\33[33m'
    BLUE = '\33[34m'
    VIOLET = '\33[35m'
    BEIGE = '\33[36m'
    WHITE = '\33[37m'

    BLACKBG = '\33[40m'
    REDBG = '\33[41m'
    GREENBG = '\33[42m'
    YELLOWBG = '\33[43m'
    BLUEBG = '\33[44m'
    VIOLETBG = '\33[45m'
    BEIGEBG = '\33[46m'
    WHITEBG = '\33[47m'

    GREY = '\33[90m'
    RED2 = '\33[91m'
    GREEN2 = '\33[92m'
    YELLOW2 = '\33[93m'
    BLUE2 = '\33[94m'
    VIOLET2 = '\33[95m'
    BEIGE2 = '\33[96m'
    WHITE2 = '\33[97m'

    GREYBG = '\33[100m'
    REDBG2 = '\33[101m'
    GREENBG2 = '\33[102m'
    YELLOWBG2 = '\33[103m'
    BLUEBG2 = '\33[104m'
    VIOLETBG2 = '\33[105m'
    BEIGEBG2 = '\33[106m'
    WHITEBG2 = '\33[107m'


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
        pass

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
        pass

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
        return f"{Colors.BEIGE}{self.user}@{self.location}{Colors.END} {Colors.BLUE}{self.cwd}{Colors.END} {Colors.BOLD}{Colors.YELLOW}{self.ps1}{Colors.END} "

    def execute(self, command, pipe=""):
        log.debug(f"Executing command {Colors.BOLD}{command['exec']}{Colors.END}")
        log.debug(f"Arguments are {Colors.BOLD}{command['args']}{Colors.END}")

        if command["pipe_in"] and command["redi_in"]:
            raise MultipleInputException("Redirection and pipe are set as input at the same time.")

        # todo: finish possible redirection from input file

        result = ""
        if command["exec"] in self.builtins.keys():
            log.debug("This is a builtin command.")
            result = self.builtins[command["exec"]](self, pipe=pipe, args=command['args'])
        else:
            log.debug("This is not a builtin command.")
            # todo: finish executing none builtin command

        if command['redi_out']:
            log.debug(f"User want to redirect the output to {command['redi_out']}")
            # todo: write to file
            return result
        
        if command['pipe_out']:
            log.debug(f"User want to pipe the IO")
            return result

        print(result)
        # return result # won't be used anymore

    def command_prompt(self):
        print(self.prompt, end="")
        command = input().strip()
        log.debug(f"Getting user input: {Colors.BOLD}{command}{Colors.END}")

        try:
            commands = self.parse(command)
            result = ""
            for command in commands:
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
