#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   王超逸
@File    :   async.py
@Time    :   2020/9/15 11:53
@Desc    :
提供一个修饰器，将一个同步的方法转变为一个异步的方法
当然，你也可以使用celery，不过celery并不总是很好用，比如说我们以后可能会想要异步执行rpc方法
btw，能开线程解决的事情，就不要起服务、开进程、配消息队列了
os.exec是相对不优雅的做法，我们应该逐渐用其他方法替代！
"""
import traceback

from .threadpool_wcy import ThreadPool, WorkRequest, ResultWrapper
from .models import ResultBackend
from threading import Thread
from uuid import uuid4


class AsyncScheme(object):
    """
    异步解决方案
    call_function(函数,返回值回调,参数,关键字参数)
    """

    def __init__(self, num_worker):
        """
        :return:
        """
        self.result_backend = ResultBackend()
        self.thread_pool = ThreadPool(num_worker)
        self.result_thread = Thread(target=self.thread_pool.consume)
        # 守护线程
        self.result_thread.daemon = True
        self.result_thread.start()

    def get_callback(self, function):
        def f(request, result):
            # self.result_backend.set_task_status(request.requestID, self.result_backend.SUCCESS)
            self.result_backend.put_result(request.requestID, result)
            if function is not None:
                function(request, result)

        return f

    def get_exception_callback(self, function):
        def f(request, result):
            # self.result_backend.set_task_status(request.requestID, self.result_backend.FAILED)
            # print("hit")
            tb_message = traceback.format_exception(*result)
            self.result_backend.put_result(request.requestID, tb_message)
            if function is not None:
                function(request, result)

        return f

    def status_change_callback(self, result, status):
        # print(result.request_id)
        self.result_backend.set_task_status(result.request_id, status)

    def call_function(self, func, args, kwargs, callback=None):
        uuid = uuid4()
        request = WorkRequest(func, args, kwargs, requestID=uuid,
                              callback=self.get_callback(callback),
                              exc_callback=self.get_exception_callback(callback),
                              status_change_callback=self.status_change_callback)
        result = self.thread_pool.putRequest(request)
        return result

    def async_function(self, callback):
        """
        生成一个修饰器，修饰器返回AsyncFunctionWrapper对象
        :param callback: 默认回调函数
        :return:
        """

        def decorator(function):
            return AsyncFunctionWrapper(function, self, callback)

        return decorator


class AsyncFunctionWrapper(object):

    def __init__(self, function, async_scheme, default_callback=None):
        self.default_callback = default_callback
        self.async_scheme = async_scheme
        self.function = function

    def with_callback(self, args, kwargs, callback):
        return self.async_scheme.call_function(self.function, args, kwargs, callback)

    def sync(self, args, kwargs):
        return self.function(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.async_scheme.call_function(self.function, args, kwargs, self.default_callback)


async_scheme = AsyncScheme(10)

async_function = async_scheme.async_function

wait_all = async_scheme.thread_pool.wait_all_task_done

get_result = async_scheme.result_backend.get_result

__all__ = ["async_function", "AsyncScheme", "ResultBackend", "wait_all", "ResultWrapper", "get_result"]
__version__ = '1.0'
__license__ = "MIT license"
