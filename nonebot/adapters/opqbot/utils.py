import asyncio
import re
import sys
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from nonebot.message import handle_event
from nonebot.typing import overrides
from nonebot.utils import DataclassEncoder

from .exception import ApiNotAvailable

from .event import Event, ON_EVENT_GROUP_NEW_MSG, MessageEvent, MessageSource, MessageQuote
from .message import MessageSegment, MessageType
from . import log

if TYPE_CHECKING:
    from .bot import Bot


def snake_to_camel(name: str) -> str:
    """将蛇形命名转换为驼峰命名, 除了以指定字符串开头的

    Args:
        name (str): 蛇型命名

    Returns:
        str: 驼峰命名字符串
    """
    for i in ['anno', 'resp']:
        if re.match(i, name):
            # 匹配中的就不转换
            return name
    # 切分转换为小驼峰
    first, *rest = name.split('_')
    return ''.join([first.lower(), *(r.title() for r in rest)])


def process_source(bot: "Bot", event: MessageEvent) -> MessageEvent:
    source = event.message_chain.extract_first(MessageType.SOURCE)
    if source is not None:
        event.source = MessageSource.parse_obj(source.data)
    return event


def process_quote(bot: "Bot", event: Union[MessageEvent, ON_EVENT_GROUP_NEW_MSG]) -> MessageEvent:
    quote = event.message_chain.extract_first(MessageType.QUOTE)
    if quote is not None:
        event.quote = MessageQuote.parse_obj(quote.data)
        if quote.data['senderId'] == event.self_id:
            event.to_me = True
    return event


def process_at(bot: "Bot", event: ON_EVENT_GROUP_NEW_MSG) -> ON_EVENT_GROUP_NEW_MSG:
    c = 0
    for msg in event.message_chain:
        if (msg.type == MessageType.AT) and (msg.data.get('target', '') == event.self_id):
            event.to_me = True
            event.message_chain.pop(c)
            break
        c += 1
    if not event.message_chain:
        event.message_chain.append(MessageSegment.plain(""))
    return event


def process_nick(bot: "Bot", event: ON_EVENT_GROUP_NEW_MSG) -> ON_EVENT_GROUP_NEW_MSG:
    plain = event.message_chain.extract_first(MessageType.PLAIN)
    if plain is not None:
        if len(bot.config.nickname):
            text = str(plain)
            nick_regex = '|'.join(filter(lambda x: x, bot.config.nickname))
            matched = re.search(rf"^({nick_regex})([\s,，]*|$)", text, re.IGNORECASE)
            if matched is not None:
                event.to_me = True
                nickname = matched.group(1)
                log.info(f'User is calling me {nickname}')
                plain.data['text'] = text[matched.end():]
        event.message_chain.insert(0, plain)
    return event


async def process_event(bot: "Bot", event: Event) -> None:
    log.debug(f'$process_event: event: {event}[{type(event)}]')
    if isinstance(event, MessageEvent):
        event = process_source(bot, event)
        event = process_quote(bot, event)
        if isinstance(event, ON_EVENT_GROUP_NEW_MSG):
            event = process_nick(bot, event)
            event = process_at(bot, event)
    await handle_event(bot, event)

class SyncIDStore:
    """同步ID队列(仓库)
    这个是队列的管理与实现, 由于多任务回归时间是不确定的, 所以这里并不是单纯的队列, 而是将还未完成的任务以KV的形式进行储存

    """
    _sync_id = 0
    # 这是一个消息队列
    _futures: Dict[str, asyncio.Future] = {}

    @classmethod
    def get_id(cls) -> str:
        """生成一个不超过sys.maxsize的任务ID

        Returns:
            str: 字符串形式的任务ID
        """
        sync_id = cls._sync_id
        cls._sync_id = (cls._sync_id + 1) % sys.maxsize
        return str(sync_id)

    @classmethod
    def add_response(cls, response: Dict[str, Any]):
        """这里是将响应添加到响应仓库里来进行暂存

        Args:
            response (Dict[str, Any]): 传入的响应体(但在实际代码中我看到是服务器发来的问候)

        Returns:
            _type_: 一个数字ID
        """
        if not isinstance(response.get('syncId'), str):
            return
        sync_id: str = response['syncId']
        if sync_id in cls._futures:
            cls._futures[sync_id].set_result(response)
        return sync_id

    @classmethod
    async def fetch_response(cls, sync_id: str,
                             timeout: Optional[float]) -> Dict[str, Any]:
        """运行指定sync_id的任务, 直到任务完成返回或任务超时抛出异常
        在任务的最后, 无论如何都会删除仓库中对应的键值

        Args:
            sync_id (str): 指定一个任务ID
            timeout (Optional[float]): 设置超时时间

        Raises:
            ApiNotAvailable: 超时了

        Returns:
            Dict[str, Any]: 任务的返回结果
        """
        future = asyncio.get_running_loop().create_future()
        cls._futures[sync_id] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise ApiNotAvailable('timeout') from None
        finally:
            del cls._futures[sync_id]


class OPQBotDataclassEncoder(DataclassEncoder):
    """OPQBot的数据类解析工作
    好的代码具有自叙性, 但我还是要把注释写上
    Source: https://github.com/ieew/nonebot_adapter_mirai2/blob/main/nonebot/adapters/mirai2/utils.py#L115-L121
    接口来源是json.JSONEncoder, 也就是处理那些不能被直接序列化的数据(也就是MessageSegment, 需要执行一下as_dict)
    """

    @overrides(DataclassEncoder)
    def default(self, o):
        log.debug(f'$default@OPQBotDataclassEncoder: o: {o}')
        # 这里咱检查一下, 能解析咱就解析, 不能解析就塞给父类去解析
        if isinstance(o, MessageSegment):
            return o.as_dict()
        return super().default(o)