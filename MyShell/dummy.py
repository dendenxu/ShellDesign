import multiprocessing
import readline
class MyFancyClass(object):
    
    def __init__(self, name):
        self.name = name
    
    def do_something(self):
        proc_name = multiprocessing.current_process().name
        print('Doing something fancy in %s for %s!' % (proc_name, self.name))


def worker(q):
    obj = q.get()
    obj.do_something()


if __name__ == '__main__':
    queue = multiprocessing.Queue()

    p = multiprocessing.Process(target=worker, args=(queue,))
    p.start()
    
    queue.put(MyFancyClass(input("myshell> ")))
    
    # Wait for the worker to finish
    queue.close()
    queue.join_thread()
    p.join()
    
# import sys
# import multiprocessing
# def func():
#     sys.stdin=open(0)
#     print(sys.stdin)
#     c = sys.stdin.read(1)
#     print("Got", c)

# multiprocessing.Process(target=func).start()