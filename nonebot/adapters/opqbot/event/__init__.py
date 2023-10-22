'''
Date: 2023-05-27 01:21:24
LastEditors: MemoryShadow
LastEditTime: 2023-10-23 00:37:32
Description: 
Copyright (c) 2023 by MemoryShadow@outlook.com, All Rights Reserved.
'''
r"""
\:\:\: warning
事件中为了使代码更加整洁, 我们采用了与PEP8相符的命名规则取代Mirai原有的驼峰命名

部分字段可能与文档在符号上不一致
\:\:\:
"""
from .base import (Event, GroupInfoModel, PrivateChatInfo,
                   UserPermission)
from .message import *  # noqa
from .notice import *  # noqa
from .request import *  # noqa
from .meta import *  # noqa

__all__ = [  # noqa
    'Event', 'GroupEventData', 'MsgHead', 'GroupInfoModel', 'PrivateChatInfo', 'UserPermission',
    'MessageSource', 'MessageEvent', 'ON_EVENT_GROUP_NEW_MSG', 'ON_EVENT_FRIEND_NEW_MSG',
    'TempMessage', 'NoticeEvent', 'MuteEvent', 'BotMuteEvent', 'BotUnmuteEvent',
    'MemberMuteEvent', 'MemberUnmuteEvent', 'BotJoinGroupEvent',
    'BotLeaveEventActive', 'BotLeaveEventKick', 'ON_EVENT_GROUP_JOIN',
    'MemberLeaveEventKick', 'ON_EVENT_GROUP_EXIT', 'ON_EVENT_GROUP_INVITE',
    'ON_EVENT_GROUP_SYSTEM_MSG_NOTIFY', 'FriendRecallEvent',
    'GroupRecallEvent', 'GroupStateChangeEvent', 'GroupNameChangeEvent',
    'GroupEntranceAnnouncementChangeEvent', 'GroupMuteAllEvent',
    'GroupAllowAnonymousChatEvent', 'GroupAllowConfessTalkEvent',
    'GroupAllowMemberInviteEvent', 'MemberStateChangeEvent',
    'MemberCardChangeEvent', 'MemberSpecialTitleChangeEvent',
    'BotGroupPermissionChangeEvent', 'MemberPermissionChangeEvent',
    'RequestEvent', 'NewFriendRequestEvent', 'MemberJoinRequestEvent',
    'BotInvitedJoinGroupRequestEvent', 'MetaEvent', 'ON_EVENT_LOGIN_SUCCESS',
    'BotOfflineEventActive', 'BotOfflineEventForce', 'ON_EVENT_NETWORK_CHANGE'
    'BotReloginEvent'
]
