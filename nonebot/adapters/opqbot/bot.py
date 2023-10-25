'''
Date: 2023-10-22 20:19:07
LastEditors: MemoryShadow
LastEditTime: 2023-10-25 23:55:48
Description: 
Copyright (c) 2023 by MemoryShadow@outlook.com, All Rights Reserved.
'''
from typing import Any, Optional, Union
from nonebot.typing import overrides

from nonebot.adapters import Bot as BaseBot
from nonebot import get_driver

from .event.message import ON_EVENT_FRIEND_NEW_MSG, ON_EVENT_GROUP_NEW_MSG, TempMessage

from .event import Event
from .message import MessageChain, MessageSegment
from .utils import Message_mirai_to_OPQBot
from . import log


class Bot(BaseBot):
    @overrides(BaseBot)
    async def send(
        self,
        event: Event,
        message: Union[str, MessageChain, MessageSegment],
        at_sender: Optional[bool] = False,
        quote: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """
        :说明:

          根据 ``event`` 向触发事件的主体发送信息

        :参数:

          * ``event: Event``: Event对象
          * ``message: Union[MessageChain, MessageSegment, str]``: 要发送的消息
          * ``at_sender: bool``: 是否 @ 事件主体
        """
        if not isinstance(message, MessageChain):
            message = MessageChain(message)
        if isinstance(event, ON_EVENT_FRIEND_NEW_MSG):
            return await self.send_friend_message(
                target=event.MsgHead.SenderUin, message_chain=message, quote=quote
            )
        elif isinstance(event, ON_EVENT_GROUP_NEW_MSG):
            if at_sender:
                message = MessageSegment.at(event.MsgHead.SenderUin) + message
            return await self.send_group_message(
                group=event.MsgHead.GroupInfo.GroupCode,
                message_chain=message,
                quote=quote,
            )
        elif isinstance(event, TempMessage):
            return await self.send_temp_message(
                qq=event.MsgHead.SenderUin,
                group=event.MsgHead.GroupInfo.GroupCode,
                message_chain=message,
                quote=quote,
            )
        else:
            raise ValueError(f"Unsupported event type {event!r}.")

    async def send_group_message(
        self, *, group: int, message_chain: MessageChain, quote: Optional[int]
    ):
        log.debug(f"$send_group_message@ group: {group}")
        log.debug(f"$send_group_message@ message_chain: {message_chain}")
        log.debug(f"$send_group_message@ quote: {quote}")
        Msg = Message_mirai_to_OPQBot(message_chain)
        Msg['ToUin'] = group
        Msg['ToType'] = 2
        await self.call_api('v1/LuaApiCaller', message=message_chain, group_id=group, origin={
            "CgiCmd": "MessageSvc.PbSendMsg",
            "CgiRequest": Msg
        })
