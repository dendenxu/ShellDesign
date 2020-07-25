#!/usr/bin/python
from subprocess import PIPE, STDOUT, Popen
import os
fd = os.open("/dev/tty",os.O_RDONLY)

my_pid = os.tcgetpgrp(fd)

print(f"My PID is {my_pid}")

p = Popen(["vi", "dummy.py"], stdin=None)

print(f"Subprocess PID is {p.pid}")

fore_pid = os.tcgetpgrp(fd)
print(f"Foreground PID is {fore_pid}")

# print("Setting foreground process to subprocess")
# os.tcsetpgrp(fd, p.pid)


p.wait()

os.close(fd)
