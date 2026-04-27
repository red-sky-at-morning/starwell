import time

def timer(func):
    def wrap(*args, **kwargs):
        start = time.perf_counter()
        ret = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__str__()} took {end-start}s")
        return ret
    return wrap