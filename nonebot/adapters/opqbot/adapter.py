import json
import asyncio
import contextlib
from typing import Any, Dict, List, Optional, Literal, cast

from nonebot.typing import overrides
from nonebot.utils import escape_tag
from nonebot.adapters import Adapter as BaseAdapter
from nonebot.exception import ActionFailed, WebSocketClosed
from nonebot.drivers import (
    URL,
    Driver,
    Request,
    Response,
    WebSocket,
    ReverseDriver,
    ForwardDriver,
    WebSocketServerSetup
)

from . import log
from .bot import Bot
from .config import Config
from .event import Event
from .utils import (
    SyncIDStore,
    process_event,
    snake_to_camel,
    OPQBotDataclassEncoder,
    Message_OPQBot_to_mirai
)

class Adapter(BaseAdapter):
    """
    继承后必须实现__init__和get_name还有_call_api方法
    """
    @overrides(BaseAdapter)
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        # 初始化配置类里的信息
        self.opqbot_config: Config = Config(**self.config.dict())
        # 多Q兼容的缓存列表, 用KV存一下QQ号对应的连接信息
        self.connections: Dict[str, WebSocket] = {}
        # 监听任务列表, 等下给多Q用的, 单Q环境基本上就一个
        self.tasks: List["asyncio.Task"] = []
        self.setup()

    @classmethod
    @overrides(BaseAdapter)
    def get_name(cls) -> str:
        return 'opqbot'

    def setup(self) -> None:
        """
        在这里注册适配器的事件响应函数
        """
        # 判断已加载的drive是否符合本适配器要求
        if isinstance(self.driver, ReverseDriver):
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL(f'/{self.opqbot_config.opqbot_mountpoint}'), self.get_name(), self._handle_ws_server
                )
            )
            
        # 加载正向ws的配置
        if isinstance(self.driver, ForwardDriver) and self.opqbot_config.opqbot_forward:
            # 别忘记校验数据
            if not all([
                isinstance(self.opqbot_config.opqbot_host, str),
                isinstance(self.opqbot_config.opqbot_port, int),
                isinstance(self.opqbot_config.opqbot_mountpoint, str),
                isinstance(self.opqbot_config.opqbot_clusterinfo, str),
                isinstance(self.opqbot_config.opqbot_api_protocol, str),
                isinstance(self.opqbot_config.opqbot_api, str),
                isinstance(self.opqbot_config.opqbot_upload, str),
                isinstance(self.opqbot_config.opqbot_qq, str),
            ]):
                raise ValueError("请检查环境变量中的 opqbot_host, opqbot_port, opqbot_mountpoint, opqbot_qq 是否异常")
            self.driver.on_startup(self._start_ws_client)
            self.driver.on_shutdown(self._stop_ws_client)

    async def _handle_ws_server(self, websocket: WebSocket):
        """在这里处理WS发来的事件

        Args:
            websocket (WebSocket): 传入当前的ws对象
        """
        await websocket.accept()
        
        # 这里传入前检查过了(在Config里)
        qqid = self.opqbot_config.opqbot_qq

        bot = Bot(self, qqid)
        self.bot_connect(bot)
        self.connections[qqid] = websocket
        log.info(f"({bot.self_id}) connection ...")

        # 事件等待回环
        try:
            while True:
                data = await websocket.receive()
                json_data = json.loads(data)
                if json_data.get("data"):
                    self._event_handle(bot, json_data)
        except WebSocketClosed as e:
            qqid = ", ".join(self.connections)
            log.warning(f"WebSocket for Bot {escape_tag(qqid)} closed by peer")
        except Exception as e:
            log.error(f"<r><bg #f8bbd0>Error while process data from websocket "
                f"for bot {escape_tag(bot.self_id)}.</bg #f8bbd0></r>", e)
        finally:
            with contextlib.suppress(Exception):
                await websocket.close()
            self.connections.pop(qqid, None)
            self.bot_disconnect(bot=bot)
    
    async def _start_ws_client(self):
        # 校验一下数据更加安全, 但我建议别这么干, 因为浪费性能, 这里用到的数据在setup中已经校验过了
        # 所以我在这儿忽视Pylance的报告, 下面同理
        qq: str = self.opqbot_config.opqbot_qq
        try:
            ws_url = URL(f"ws://{self.opqbot_config.opqbot_host}:{self.opqbot_config.opqbot_port}/{self.opqbot_config.opqbot_mountpoint}")
            # 异步拉起一个监听任务避免堵塞
            self.tasks.append(asyncio.create_task(self._ws_client(qq, ws_url)))
        except Exception as e:
            log.error(f"<r><bg #f8bbd0>Bad url {escape_tag(str(ws_url))} "
                "in opqbot forward websocket config</bg #f8bbd0></r>",
                e)

    async def _stop_ws_client(self):
        # 关闭ws的时候记得删掉任务
        for task in self.tasks:
            if not task.done():
                task.cancel()

    async def _ws_client(self, qq: str, url: URL):
        """进入WS客户端

        Args:
            qq (str): 需要响应的QQ号
            url (URL): 要监听的URL
        """
        headers = {"qq": qq}
        request = Request("GET", url=url, headers=headers, timeout=3)
        # 进入监听回环, 不抛异常不出来
        while True:
            try:
                async with self.websocket(request) as ws:
                    log.debug(f"WebSocket Connection to {escape_tag(str(url))} established")
                    try:
                        bot = Bot(self, qq)
                        # 这里拿到一下Bot, 等下推消息回去好推
                        # 把连接信息塞进去
                        self.connections[qq] = ws
                        # 触发一下连接事件
                        self.bot_connect(bot)
                        log.info(f"<y>Bot {escape_tag(qq)}</y> connected")

                        while True:
                            # 等待事件传过来, 收到消息再丢给_event_handle处理
                            data = await ws.receive()
                            log.debug(f"$_ws_client@ Received data from: {data}")
                            json_data = json.loads(data)
                            self._event_handle(bot, json_data)
                    except WebSocketClosed as e:
                        log.error("<r><bg #f8bbd0>WebSocket Closed</bg #f8bbd0></r>", e)
                    except Exception as e:
                        log.error("<r><bg #f8bbd0>Error while process data from websocket"
                            f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                            e
                        )
                    finally:
                        self.connections.pop(qq, None)
                        # 照常忽略, 因为这里的值来源是new对象(谁家new对象new出None还不抛异常啊, 不用处理)
                        self.bot_disconnect(bot)
            except Exception as e:
                log.error("<r><bg #f8bbd0>Error while setup websocket to "
                    f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                    e
                )
            await asyncio.sleep(3)

    def _event_handle(self, bot: Bot, event: Dict):
        """处理收到的事件

        Args:
            bot (Bot): Bot对象本身
            event (Dict): 事件源
        """
        # 处理事件, 将OPQBot格式的数据簇转为Mirai格式的消息列表
        MsgSegment: list = []
        if event['CurrentPacket']['EventData']['MsgBody'] is not None:
            MsgData = event['CurrentPacket']['EventData']['MsgBody']
            MsgSegment = Message_OPQBot_to_mirai(MsgData)

        event['CurrentPacket']['EventData']['MsgBody'] = MsgSegment
        asyncio.create_task(process_event(
            bot,
            event=Event.new({
                **event['CurrentPacket']['EventData'],
                "type": event['CurrentPacket']['EventName'],
                "self_id": bot.self_id,
                "messageChain": MsgSegment
            })
        ))

    @overrides(BaseAdapter)
    async def _call_api(self, bot: Bot, api: str,
        subcommand: Optional[Literal['get', 'update']] = None, **data: Any) -> Any:
        log.debug(f'$_call_api@ api: {api}, data: {data}')
        if 'origin' in data:
            body = data['origin']
        else:
            # TODO: 不为origin信息, 就尝试识别api信息
            body = {
                "CgiCmd": "MessageSvc.PbSendMsg",
                "CgiRequest": {
                    "ToUin": 123456,
                    "ToType": 2,
                    "Content": "HelloWorld"
                }
            }
        # 发送数据
        ApiUrl: str = f'{self.opqbot_config.opqbot_api_protocol}://{self.opqbot_config.opqbot_host}:{self.opqbot_config.opqbot_port}/{api}'
        log.debug(f'$_call_api@ ApiUrl: {ApiUrl}')
        request = Request(
            method="POST",  # 请求方法
            url=ApiUrl,  # 接口地址
            # headers={
            #     'Content-Type': 'application/json'
            # },
            params={
                'funcname': 'MagicCgiCmd',
                'timeout': 10,
                'qq': f'{self.opqbot_config.opqbot_qq}'
            },
            json=body
        )
        result: Response = await self.driver.request(request)
        # TODO: 处理返回结果识别错误情况打印日志
        log.debug(f'$_call_api@ result: {result} -> {str(result.content, "utf-8")}')
        # 发送请求，返回结果
        return result

        result: Dict[str, Any] = await SyncIDStore.fetch_response(
            sync_id, timeout=self.config.api_timeout)

        if ('data') not in result or (result['data']).get('code') not in (None, 0):
            raise ActionFailed(
                f'{self.get_name()} | {result.get("data") or result}'
            )

        return result['data']
