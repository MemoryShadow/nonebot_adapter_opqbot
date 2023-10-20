'''
Date: 2023-05-27 01:24:03
LastEditors: MemoryShadow
LastEditTime: 2023-05-30 00:20:27
Description: 
Copyright (c) 2023 by MemoryShadow@outlook.com, All Rights Reserved.
'''
from .base import Event
from typing import Literal
from nonebot.typing import overrides


class MetaEvent(Event):
    """元事件基类"""
    qq: int

    @overrides(Event)
    def get_type(self) -> Literal["meta_event"]:  # noqa
        return 'meta_event'


class ON_EVENT_LOGIN_SUCCESS(MetaEvent):
    """Bot登录成功"""
    pass


class BotOfflineEventActive(MetaEvent):
    """Bot主动离线"""
    pass


class BotOfflineEventForce(MetaEvent):
    """Bot被挤下线"""
    pass


class ON_EVENT_NETWORK_CHANGE(MetaEvent):
    """Bot被服务器断开或因网络问题而掉线"""
    pass


class BotReloginEvent(MetaEvent):
    """Bot主动重新登录"""
    pass
