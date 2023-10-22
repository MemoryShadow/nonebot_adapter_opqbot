from enum import Enum
from nonebot.typing import overrides
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional

from .base import Event, GroupEventData, GroupInfoModel, UserPermission
from .message import MessageChain


class NoticeEvent(Event):
    """通知事件基类"""
    @overrides(Event)
    def get_type(self) -> Literal["notice"]:  # noqa
        return 'notice'


class MuteEvent(NoticeEvent):
    """禁言类事件基类"""
    operator: GroupEventData


class BotMuteEvent(MuteEvent):
    """Bot被禁言"""
    duration_seconds: int = Field(alias='durationSeconds')


class BotUnmuteEvent(MuteEvent):
    """Bot被取消禁言"""
    pass


class MemberMuteEvent(MuteEvent):
    """群成员被禁言事件(该成员不是Bot)"""
    duration_seconds: int = Field(alias='durationSeconds')
    member: GroupEventData
    operator: Optional[GroupEventData] = None


class MemberUnmuteEvent(MuteEvent):
    """群成员被取消禁言事件(该成员不是Bot)"""
    member: GroupEventData
    operator: Optional[GroupEventData] = None


class BotJoinGroupEvent(NoticeEvent):
    """Bot加入了一个新群"""
    group: GroupInfoModel
    invitor: Optional[GroupEventData]


class BotLeaveEventActive(NoticeEvent):
    """Bot主动退出一个群"""
    group: GroupInfoModel


class BotLeaveEventKick(NoticeEvent):
    """Bot被踢出一个群"""
    group: GroupInfoModel
    operator: Optional[GroupEventData]


class BotLeaveEventDisband(NoticeEvent):
    """Bot因群主解散群而退出群"""
    group: GroupInfoModel
    operator: Optional[GroupEventData]


class ON_EVENT_GROUP_JOIN(NoticeEvent):
    """新人入群的事件"""
    EventData: GroupEventData


class MemberLeaveEventKick(NoticeEvent):
    """成员被踢出群（该成员不是Bot）"""
    EventData: GroupEventData


class ON_EVENT_GROUP_EXIT(NoticeEvent):
    """成员主动离群（该成员不是Bot）"""
    EventData: GroupEventData


class ON_EVENT_GROUP_SYSTEM_MSG_NOTIFY(NoticeEvent):
    """邀请事件"""
    EventData: GroupEventData

class ON_EVENT_GROUP_INVITE(NoticeEvent):
    """邀请事件"""
    EventData: GroupEventData


class GroupRecallEvent(NoticeEvent):
    """群消息撤回"""
    author_id: int = Field(alias='authorId')
    message_id: int = Field(alias='messageId')
    time: int
    group: GroupInfoModel
    operator: Optional[GroupEventData] = None


class FriendRecallEvent(NoticeEvent):
    """好友消息撤回"""
    author_id: int = Field(alias='authorId')
    message_id: int = Field(alias='messageId')
    time: int
    operator: int


class GroupStateChangeEvent(NoticeEvent):
    """群变化事件基类"""
    origin: Any
    current: Any
    group: GroupInfoModel
    operator: Optional[GroupEventData] = None


class GroupNameChangeEvent(GroupStateChangeEvent):
    """某个群名改变"""
    origin: str
    current: str


class GroupEntranceAnnouncementChangeEvent(GroupStateChangeEvent):
    """某群入群公告改变"""
    origin: str
    current: str


class GroupMuteAllEvent(GroupStateChangeEvent):
    """全员禁言"""
    origin: bool
    current: bool


class GroupAllowAnonymousChatEvent(GroupStateChangeEvent):
    """匿名聊天"""
    origin: bool
    current: bool


class GroupAllowConfessTalkEvent(GroupStateChangeEvent):
    """坦白说"""
    origin: bool
    current: bool
    is_bot: bool = Field(alias='isByBot')


class GroupAllowMemberInviteEvent(GroupStateChangeEvent):
    """允许群员邀请好友加群"""
    origin: bool
    current: bool


class MemberStateChangeEvent(NoticeEvent):
    """群成员变化事件基类"""
    member: GroupEventData
    operator: Optional[GroupEventData] = None


class MemberCardChangeEvent(MemberStateChangeEvent):
    """群名片改动"""
    origin: str
    current: str


class MemberSpecialTitleChangeEvent(MemberStateChangeEvent):
    """群头衔改动（只有群主有操作限权）"""
    origin: str
    current: str


class BotGroupPermissionChangeEvent(MemberStateChangeEvent):
    """Bot在群里的权限被改变"""
    origin: UserPermission
    current: UserPermission
    group: GroupInfoModel


class MemberPermissionChangeEvent(MemberStateChangeEvent):
    """成员权限改变的事件（该成员不是Bot）"""
    origin: UserPermission
    current: UserPermission



class NudgeSubjectKind(Enum):
    GROUP = "Group"
    FRIEND = "Friend"


class NudgeSubject(BaseModel):
    id: int
    kind: NudgeSubjectKind
    suffix: str


class NudgeEvent(NoticeEvent):
    """戳一戳事件"""
    from_id: int = Field(alias="FromId")
    target: int
    action: str
    subject: NudgeSubject
    suffix: str


class friend(BaseModel):
    id: int
    nickname: str
    remark: str


class FriendInputStatusChangedEvent(NoticeEvent):
    """好友输入状态改变事件"""
    friend: friend
    inputting: bool


class FriendNickChangedEvent(NoticeEvent):
    """好友昵称改变事件"""
    friend: friend
    from_name: str
    new_name: str


class action(Enum):
    ACHIEVE = "achieve"
    LOSE = "lose"


class MemberHonorChangeEvent(NoticeEvent):
    """群员称号改变"""
    member: GroupEventData
    action: action
    honor: str


class client(BaseModel):
    id: int
    platform: str
    kind: int


class OtherClientOnlineEvent(NoticeEvent):
    """其他客户端上线"""
    client: client


class OtherClientOfflineEvent(NoticeEvent):
    """其他客户端下线"""
    client: client


class CommandExecutedEvent(NoticeEvent):
    """命令被执行"""
    name: str
    friend: Optional[friend]
    member: Optional[GroupEventData]
    args: MessageChain
