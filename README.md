## 概述

本来只想安个线程池直接用的。但是感觉ThreadPool这个库写的实在是水。于是把它源码复制粘贴修改了一下，增加了一些好用的功能。

最起码，你不必自己调用pool.wait()了。原来的实现。你如果不调用这个，他就不会从结果队列里面取结果。

其次。除了用回调函数，现在还提供了更方便的方法来获取结果。而且还能通过结果后端把结果持久化到数据库。

这个库在功能上有参考celery。在单机的情形下，也可一定程度的替代celery的部分功能。但是它和celery很不一样。

区别在于这个库更加轻量，占用的资源更少（celery默认的prefork会为每个worker创建一个进程，而我这里仅仅创建一个线程）。不需要消息队列（这意味着它不能调用远程的过程，但同时也意味着他的响应更快）。

有了这个库，你就可以随时随地的异步了。考虑下面的情形：

```python
from simple_async.asyncImp import async_function, ResultWrapper


@async_function()
def get_some_info_from_rpc(i):
    # 从rpc获取数据，非常缓慢
    print("start %d" % i)
    sleep(2)
    print("end %d" % i)
    return i

@async_function()
def get_some_info_from_db(i):
    # 从数据库获取数据，非常缓慢
    print("start %d" % i)
    sleep(2)
    print("end %d" % i)
    return i

@async_function()
def get_some_info_from_webapi(i):
    # 从rest api获取数据，非常缓慢
    print("start %d" % i)
    sleep(2)
    print("end %d" % i)
    return i

# 现在我们可以并行的调用三个方法了
def main():
    r1 = get_some_info_from_rpc(1)
    r2 = get_some_info_from_db(2)
    r3 = get_some_info_from_webapi(3)
    print(r1.wait()+r2.wait()+r3.wait())

main()
```



## 安装

- 克隆代码,放入自己的项目中,作为一个app
- 在install_app中注册
- migrate
- 你可以通过再setting.py文件中加入`ASYNC_WORKER_NUM`选项来设置worker的数量

## 快速指引

你可以通过`async_function`修饰器将一个同步函数变为一个异步函数.`async_function`修饰器有一个可选的参数,用于填入运行完成后的回调函数。要获取执行结果,除了回调函数,还有更多方法,你会在接下来读到。

函数经过`async_function`修饰器后,会变成一个`AsyncFunctionWrapper`对象。

`AsyncFunctionWrapper`对象有一些重要的方法:

- `__call__(self, *args, **kwargs)`：

  这使得这个对象可以直接调用。直接调用此对象会将原函数交给一个线程池来运行。将返回一个`ResultWrapper`对象，你会在后文了解到这个对象的用法。

- `sync(self, args, kwargs)`：

  同步调用原函数，返回值为原函数的返回值

- `with_option(self, args, kwargs, callback=None, keep_result=None)`：

  效果和`__call__`相同，但是你可以为本次调用单独指定callback和是否持久化原函数返回值。如果keep_result=True，原函数返回值会持久化到数据库。返回值依然是`ResultWrapper`对象。

异步调用总是会返回一个`ResultWrapper`对象，`ResultWrapper`对象有一些重要方法：

- wait()：

  阻塞直到该任务异步执行完毕，如果函数成功执行，那么此函数会返回原函数的结果。如果原函数发生异常，那么这个函数也会抛出异常。

- status：

  属性。可能的取值：

  - Pending：任务已经分配给线程池了，但是由于没有空闲的线程，所以这个任务正在排队
  - Running：任务正在执行
  - Failed：执行时抛出了异常
  - Success：执行成功

- request_id：

  字段，不要修改它。用来获得本次异步调用的id值

了解了这些之后，我们来看一个例子：

```python
from simple_async.asyncImp import async_function, ResultWrapper, get_result, wait_all


def callback(request, result):
    print "callback %s %s" % (request, str(result))

# 对于相当耗时的任务。我们更倾向于通过回调函数来处理
@async_function(callback)
def some_block_task(i):
    print("start %d" % i)
    sleep(20)
    print("end %d" % i)
    return i

def i_cant_wait_the_task():
    result_list = [some_block_task(i) for i in range(10)]
    print("任务已发送")

i_cant_wait_the_task()
wait_all()
```

----------

接下来。我们再来看两个例子。他们演示了如何使用结果后端。结果后端会将数据持久化到数据库，你可以通过request_id在之后通过get_result(request_id)来处理。

这样做的好处在于，你可能想要在合适的时候再统一处理调用的结果。或者将调用的结果交给其他服务处理。

注意： 一个尚未运行的任务（pending中的任务）不会加入数据库。任何数据库中查不到的任务get_result()的返回值为（“Pending”，None）。

```python
class TestException(Exception):
    pass

# 启用结果后端
@async_function(keep_result=True)
def when_error_raise():
    raise TestException

# test case 2
def test_exception():
    result_list = [when_error_raise() for i in range(10)]
    print("任务已发送")
    for result in result_list:
        try:
            # 如果执行时有异常，会在这时抛出异常
            # 详细的异常信息可以通过get_result获得
            result.wait()
        except TestException as e:
            print("异常已捕获")
            assert result.status == ResultWrapper.FAILED
            continue

        assert False, "不该执行到这里来"

# test case 3
def test_result_backend():
    result_list = [when_error_raise() for i in range(10)]
    wait_all()
    for result in result_list:
        # 从result后端获取
        status, result = get_result(result.request_id)
        assert status == ResultWrapper.FAILED
        print result

```



你可以通过三种方式获得异步调用的返回值。分别是通过回调函数，通过`ResultWrapper`对象，和通过get_result(request_id)获得。

你可以在返回的`ResultWrapper`对象中获得request_id。

除此之外，还有几个值得注意的函数：

- wait_all()：如果你要等待所有异步任务执行完毕然后安全的结束你的程序，你应该在程序结束前调用wait_all()。
- async_call_function(func, args, kwargs, callback=None, keep_result=False)：如果你想异步调用一个没有被@async_function包装的函数，那么你可以用这个方法
- set_print_exc(bool)：默认为true。当原函数发生异常时，它会将原函数的异常栈打印到标准错误中
- get_payload()：用来观察线程池的负载情况。返回pending的任务数量。



*以上提到的所有的东西，你可以从`simple_async.asyncImp `引入*

## API参考

看源码吧，很短的。

线程池用的是threadpool这个包。魔改了一下使它能够支持我的一些逻辑。如果要看源码的话，请结合https://chrisarndt.de/projects/threadpool/食用。你不需要自己去安装threadpool这个包，因为我是把它复制到我的代码中进行修改的。

