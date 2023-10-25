from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional

from nonebot.typing import overrides

from ..message import MessageChain
from .base import (
    Event,
    MsgBody,
    EventCenter,
    GroupInfoModel,
    MsgHead,
    OtherChatInfo,
    PrivateChatInfo,
    StrangerChatInfo
)


class MessageSource(BaseModel):
    id: int
    time: datetime


class MessageQuote(BaseModel):
    _type: str = Field(..., alias="EventName")
    id: int
    sender_id: int = Field(..., alias="senderId")
    target_id: int = Field(..., alias="targetId")
    group_id: int = Field(None, alias="groupId")
    origin: MessageChain


class MessageEvent(Event):
    """消息事件基类"""
    MsgHead: MsgHead
    MsgBody: MessageChain = Field(alias='messageChain')
    Event: Optional[EventCenter] = Field(None)
    message_chain: MessageChain = Field(alias='messageChain')

    @overrides(Event)
    def get_type(self) -> Literal["message"]:  # noqa
        return 'message'

    @overrides(Event)
    def get_message(self) -> MessageChain:
        return self.message_chain

    @overrides(Event)
    def get_plaintext(self) -> str:
        return self.message_chain.extract_plain_text()

    @overrides(Event)
    def get_user_id(self) -> str:
        raise NotImplementedError

    @overrides(Event)
    def get_session_id(self) -> str:
        raise NotImplementedError

class ON_EVENT_GROUP_NEW_MSG(MessageEvent):
    """群消息事件"""

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'group_{self.MsgHead.group.GroupCode}_{self.MsgHead.SenderUin}'

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.MsgHead.SenderUin)

    @overrides(MessageEvent)
    def is_tome(self) -> bool:
        return self.to_me
    

class GroupSyncMessage(MessageEvent):
    """同步群消息事件"""
    sender: GroupInfoModel = Field(alias="subject")
    to_me: bool = False
    self_id: int

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'groupSync_{self.sender.id}_{self.self_id}'

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.self_id)

    @overrides(MessageEvent)
    def is_tome(self) -> bool:
        return self.to_me


class ON_EVENT_FRIEND_NEW_MSG(MessageEvent):
    """好友消息事件"""

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.MsgHead.SenderUin)

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'friend_{self.MsgHead.SenderUin}'

    @overrides(MessageEvent)
    def is_tome(self) -> bool:
        return True


class FriendSyncMessage(MessageEvent):
    """同步好友消息事件"""
    sender: PrivateChatInfo = Field(alias="subject")

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.sender.id)

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'friendSync_{self.sender.id}'

    @overrides(MessageEvent)
    def is_tome(self) -> bool:
        return True


class TempMessage(MessageEvent):
    """临时会话消息事件"""
    sender: PrivateChatInfo

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.sender.id)

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'temp_{self.sender.group.id}_{self.sender.id}'

    @overrides(MessageEvent)
    def is_tome(self) -> bool:
        return True


class TempSyncMessage(MessageEvent):
    """同步临时会话消息事件"""
    sender: PrivateChatInfo = Field(alias="subject")

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.sender.id)

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'tempSync_{self.sender.group.id}_{self.sender.id}'

    @overrides(MessageEvent)
    def is_tome(self) -> bool:
        return True


class StrangerMessage(MessageEvent):
    """陌生人消息事件"""
    sender: StrangerChatInfo

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.sender.id)

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'stranger_{self.sender.id}'


class StrangerSyncMessage(MessageEvent):
    """同步陌生人消息事件"""
    subject: StrangerChatInfo = Field(alias="subject")
    self_id: int

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.self_id)

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'strangerSync_{self.self_id}'


class OtherClientMessage(MessageEvent):
    """其他客户端消息事件"""
    sender: OtherChatInfo

    @overrides(MessageEvent)
    def get_user_id(self) -> str:
        return str(self.sender.id)

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f'other_{self.sender.id}'

