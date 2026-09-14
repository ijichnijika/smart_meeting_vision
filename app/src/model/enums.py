from enum import Enum
from typing import Optional


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"


class BehaviorType(Enum):
    LOOK_FORWARD = ("look_forward", "正视听讲", False)
    WRITE = ("write", "书写笔记", False)
    READ = ("read", "阅读资料", False)
    HANDRISE = ("handrise", "举手发言", False)
    STAND = ("stand", "起立发言", False)
    USING_DEVICE = ("using_device", "低头玩手机", True)
    SLEEP = ("sleep", "闭眼打瞌睡", True)
    TURN_HEAD = ("turn_head", "侧向交流", False)
    PERSON = ("person", "在席听讲", False)
    CELL_PHONE = ("cell phone", "移动终端", False)

    def __init__(self, code: str, label: str, is_distracted: bool):
        self.code = code
        self.label = label
        self.is_distracted = is_distracted

    @classmethod
    def from_code(cls, code: str) -> Optional["BehaviorType"]:
        for item in cls:
            if item.code == code:
                return item
        return None

    @classmethod
    def is_distracted_code(cls, code: str) -> bool:
        item = cls.from_code(code)
        return item.is_distracted if item is not None else False
