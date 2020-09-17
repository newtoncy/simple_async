# coding=utf-8
from __future__ import unicode_literals

from django.db import models
import pickle
# from django.db import transaction
from threading import Lock
# Create your models here.


class ResultBackend(models.Model):
    """
    异步结果后端
    serialize(obj)如何序列化
    deserialize(bytes_)如何反序列化
    put_result(task_id,obj)存放结果
    get_result(task_id)->(status,result)取得任务结果
    set_task_status(task_id,status)任务执行状态
    """
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"
    PENDING = "Pending"
    result = models.BinaryField("序列化的返回值", max_length=4 * 1024 * 1024, null=True)
    task_id = models.CharField("任务id", max_length=100, unique=True)
    status = models.CharField("状态", max_length=40, default=PENDING)
    result_status_lock = Lock()

    @classmethod
    def serialize(cls, obj):
        return pickle.dumps(obj)

    @classmethod
    def deserialize(cls, bytes_):
        if bytes_ is None:
            return None
        return pickle.loads(bytes_)

    @classmethod
    def put_result(cls, task_id, obj):
        # 因为设置结果和设置状态有时会同时发生
        # 所以必须用事务
        # 不管用，事务隔离级别不对？事务没有打开？
        # 加锁
        # 更新，现在不会冲突了，现在对于同一行，这两个函数始终是串行访问的
        # with transaction.atomic():
        # with cls.result_status_lock:
        instance, _ = cls.objects.get_or_create(task_id=task_id)
        instance.result = cls.serialize(obj)
        instance.save()

    @classmethod
    def set_task_status(cls, task_id, status):
        # with transaction.atomic():
        # with cls.result_status_lock:
        instance, _ = cls.objects.get_or_create(task_id=task_id)
        instance.status = status
        instance.save()

    @classmethod
    def get_result(cls, task_id):
        try:
            instance = cls.objects.get(task_id=task_id)
        except:
            return "Pending", None
        return instance.status, cls.deserialize(instance.result)
