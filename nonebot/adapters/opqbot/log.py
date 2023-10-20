'''
Date: 2023-05-26 19:43:27
Author: ieew
LastEditors: MemoryShadow
LastEditTime: 2023-06-04 17:17:48
Description: 日志模块
Source: https://github.com/ieew/nonebot_adapter_mirai2/blob/main/nonebot/adapters/mirai2/log.py
'''
from typing import Optional
from nonebot.utils import logger_wrapper

log = logger_wrapper("opqbot")


def info(message: str, exception: Optional[Exception] = None):
    log("INFO", message=message, exception=exception)


def warning(message: str, exception: Optional[Exception] = None):
    log("WARNING", message=message, exception=exception)


def warn(message: str, exception: Optional[Exception] = None):
    log("WARNING", message=message, exception=exception)


def debug(message: str, exception: Optional[Exception] = None):
    log("DEBUG", message=message, exception=exception)


def error(message: str, exception: Optional[Exception] = None):
    log("ERROR", message=message, exception=exception)