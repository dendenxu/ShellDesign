# import readline
# import multiprocessing
# class MyFancyClass(object):
    
#     def __init__(self, name):
#         self.name = name
    
#     def do_something(self):
#         proc_name = multiprocessing.current_process().name
#         print('Doing something fancy in %s for %s!' % (proc_name, self.name))


# def worker(q):
#     obj = q.get()
#     obj.do_something()


# if __name__ == '__main__':
#     queue = multiprocessing.Queue()

#     p = multiprocessing.Process(target=worker, args=(queue,))
#     p.start()
    
#     queue.put(MyFancyClass(input("myshell> ")))
    
#     # Wait for the worker to finish
#     queue.close()
#     queue.join_thread()
#     p.join()

# import io
# import sys
# from multiprocessing import Process, Queue, Manager, Pool

# class Wrapper(io.TextIOWrapper):
#     def __init__(self, queue, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.queue = queue
#     def read(self, size):
#         self.queue.get()
#         print("HAHA! GOTHA!")
#         return super().read(size)
    
# def func(queue):
#     if sys.stdin is not None:
#         sys.stdin.close()
#     stdin=open(0)
#     buffer = stdin.detach()
#     wrapper = Wrapper(queue, buffer)
#     sys.stdin = wrapper
#     print(sys.stdin)
#     c = sys.stdin.read(1)
#     print("Got", c)
#     q.put("dummy")

# q = Queue()
# Process(target=func, args=(q,)).start()
# print("Before putting stuff in the queue, the stdin should be responding to main process")
# print(input("myshell> "))
# print("Should wait for wrapper to finish")
# q.put("dummy")
# q.get()
# print(input("myshell> "))

print("Before any input requirements")

print(input("myshell1> "))
print(input("myshell2> "))
print(input("myshell3> "))
print(input("myshellend> "))