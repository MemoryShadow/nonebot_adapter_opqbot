import json
from enum import Enum
from typing_extensions import Literal
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError

from nonebot.typing import overrides
from nonebot.utils import escape_tag
from nonebot.adapters import Event as BaseEvent
from nonebot.adapters import Message as BaseMessage

from .. import log


class UserPermission(str, Enum):
    """
    :说明:

      用户权限枚举类

        * ``OWNER``: 群主
        * ``ADMINISTRATOR``: 群管理
        * ``MEMBER``: 普通群成员
    """
    OWNER = 'OWNER'
    ADMINISTRATOR = 'ADMINISTRATOR'
    MEMBER = 'MEMBER'
    

class GroupInfoModel(BaseModel):
    GroupCode: int
    GroupCard: str
    GroupInfoSeq: int
    GroupLevel: int
    GroupRank: int
    GroupType: int
    GroupName: str
    
class MsgHead(BaseModel):
    FromUin: int
    FromUid: str
    ToUin: int
    ToUid: str
    FromType: int
    SenderUin: int
    SenderUid: str
    SenderNick: str
    MsgType: int
    C2cCmd: int
    MsgSeq: int
    MsgTime: int
    MsgRandom: int
    MsgUid: int
    group: Optional[GroupInfoModel] = Field(None, alias='GroupInfo')
    GroupInfo: Optional[GroupInfoModel] = Field(None, alias='GroupInfo')
    C2CTempMessageHead: None

class MsgBody(BaseModel):
    SubMsgType: int
    Content: str
    AtUinLists: None = Field(None, alias='AtUinLists')
    Images: list = Field(None, alias='Images')
    Video: list  = Field(None, alias='Video')
    Voice: list  = Field(None, alias='Voice')


class EventCenter(BaseModel):
    # 事件触发的中心人物
    # 处理人Uid
    AdminUid: Optional[str]
    # 被处理人Uid
    Uid: Optional[str]
    # 被邀请人Uin
    Invitee: Optional[str]
    # 邀请入Uin
    Invitor: Optional[str]
    # 提示信息
    Tips: Optional[str]


# 在这里描述一套数据结构, 这套数据结构要和实际传过来的数据保持一致
class EventData(BaseModel):
    MsgHead: MsgHead
    MsgBody: MsgBody
    Event: EventCenter = Field(None, alias='EventCenter')


class GroupEventData(BaseModel):
    ActorUid: str
    ActorUidNick: str
    GroupCode: int
    GroupName: str
    InvitorUid: str
    InvitorUidNick: str
    MsgAdditional: str
    MsgSeq: int
    MsgType: int
    ReqUid: str
    ReqUidNick: str
    Status: int

class PrivateChatInfo(BaseModel):
    id: int
    nickname: str
    remark: str


class StrangerChatInfo(BaseModel):
    id: int
    nickname: str
    remark: str


class OtherChatInfo(BaseModel):
    id: int
    platform: str


class Event(BaseEvent):
    """
    mirai-api-http 协议事件，字段与 mirai-api-http 一致。各事件字段参考 `mirai-api-http 事件类型`_

    .. _mirai-api-http 事件类型:
        https://github.com/project-mirai/mirai-api-http/blob/master/docs/EventType.md
        OPQBot-api-ws 事件类型:
        https://73s2swxb4k.apifox.cn/doc-2271638
    TODO 这里的下游就是需要检测的事件
    """
    self_id: int
    type: str

    @classmethod
    def new(cls, data: Dict[str, Any]) -> "Event":
        """
        此事件类的工厂函数, 能够通过事件数据选择合适的子类进行序列化
        mirai通过这type来标注事件类型, 对于OPQBot则为EventName
        """
        EventName = data['EventName']
        log.debug(data.__str__())

        def all_subclasses(cls: Type[Event]):
            """通过反射返回一个集合, 这个集合中包含了所有的子类

            Args:
                cls (Type[Event]): 一个Event家族中的类

            Returns:
                set: 所有的子类, 是否是字符串有待考量
            """
            # 通过反射返回一个集合, 这个集合中包含了所有的子类
            return set(cls.__subclasses__()).union(
                [s for c in cls.__subclasses__() for s in all_subclasses(c)])

        # 检查是否有与type同名的子类, 如果有没有就将此类型的事件交给Event解析
        event_class: Optional[Type[Event]] = None
        for subclass in all_subclasses(cls):
            if subclass.__name__ != EventName:
                continue
            event_class = subclass
        log.debug(f'event_class: {event_class}')

        if event_class is None:
            return Event.parse_obj(data)
        # 如果找到了合适的子类, 就将这个事件交给这个子类解析. 如果解析失败, 则尝试使用其父类进行解析直到解析成功或者已经尝试到 Event 类为止.
        while event_class and issubclass(event_class, Event):
            try:
                # 调用子类的parse_obj方法, 这个方法是在基类BaseModel中被定义的: 
                # 主要目的是将一个对象(传入的事件模型)转化为指定的 Model 类型的对象。
                # 该函数首先确保根级别的对象是字典类型，然后将字典中的键值对作为关键字参数传递给指定的 Model 类的构造函数，
                # 最终返回一个 Model 类型的对象。如果类型不匹配或转换失败，将抛出相应的异常。
                return event_class.parse_obj(data)
            except ValidationError as e:
                log.info(
                    f'Failed to parse {data} to class {event_class.__name__}: '
                    f'{e.errors()!r}. Fallback to parent class.')
                event_class = event_class.__base__  # type: ignore
        # 如果解析失败且已经尝试到 Event 类, 就抛出 ValueError 异常.
        raise ValueError(f'Failed to serialize {data}.')

    @overrides(BaseEvent)
    def get_type(self) -> Literal["message", "notice", "request", "meta_event"]:  # noqa
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        return self.type

    @overrides(BaseEvent)
    def get_event_description(self) -> str:
        return escape_tag(str(self.normalize_dict()))

    @overrides(BaseEvent)
    def get_message(self) -> BaseMessage:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_plaintext(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_user_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_session_id(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def is_tome(self) -> bool:
        return False

    def normalize_dict(self, **kwargs) -> Dict[str, Any]:
        """
        返回可以被json正常反序列化的结构体
        """
        return json.loads(self.json(**kwargs))
