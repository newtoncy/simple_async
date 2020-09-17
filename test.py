# coding=utf-8
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Scsl.settings")
import django

django.setup()

import unittest
from time import sleep
from simple_async.asyncImp import async_function, ResultWrapper, get_result, wait_all, get_payload


def callback(request, result):
    print "callback %s %s" % (request, str(result))


@async_function(callback)
def some_block_task(i):
    print("start %d" % i)
    sleep(2)
    print("end %d" % i)
    return i


class TestException(Exception):
    pass


@async_function(callback)
def when_error_raise():
    raise TestException


# test case 1
def test_wait():
    result_list = [some_block_task(i) for i in range(10)]
    print("任务已发送")
    for i, result in enumerate(result_list):
        assert i == result.wait()
        assert result.status == ResultWrapper.SUCCESS


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
    for result in result_list:
        # 从result后端获取
        wait_all()
        status, result = get_result(result.request_id)
        assert status == ResultWrapper.FAILED
        assert isinstance(result, list) and len(result) > 1


# test case 4
def test_success():
    result_list = [some_block_task(i) for i in range(20)]
    wait_all()
    print("!!")
    for i, result in enumerate(result_list):
        # 从result后端获取
        # sleep(60 * 60 * 50)
        status, result = get_result(result.request_id)
        assert status == ResultWrapper.SUCCESS
        assert result == i

def test_payload():
    result_list = [some_block_task(i) for i in range(40)]
    print(get_payload())

if __name__ == '__main__':
    test_wait()
    test_exception()
    # test_result_backend()
    # test_success()
    test_payload()
    wait_all()
    sleep(60*60*50)
