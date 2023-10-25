from typing import List, Optional

from pydantic import Field, Extra, BaseModel


class Config(BaseModel):
    """
    OPQBot 配置类

    :配置项:

        - ``opqbot_host``: 目标的地址
        - ``opqbot_port``: 目标的端口
        - ``opqbot_mountPoint``: 目挂载点
        - ``opqbot_qq``: 目标的QQ(这个框架通常来说不支持多个QQ同时连接)
        - ``opqbot_forward``: 是否启用正向 ws 来主动连接服务

    一般来说, 最终的合成就是 ``ws://host:port/mountPoint``
    """
    
    opqbot_host: Optional[str] = "localhost"
    opqbot_port: Optional[int] = 8086
    opqbot_mountpoint: Optional[str] = "ws"
    opqbot_clusterinfo: Optional[str] = "v1/clusterinfo"
    opqbot_api: Optional[str] = "v1/LuaApiCaller"
    opqbot_api_protocol: Optional[str] = "http"
    opqbot_upload: Optional[str] = "v1/upload"
    # 这里不应该是一个可选项, 因为OPQ的请求调用都要使用这个
    opqbot_qq: str
    opqbot_forward: Optional[bool] = True

    class Config:
        extra = Extra.ignore
        allow_population_by_field_name = True
