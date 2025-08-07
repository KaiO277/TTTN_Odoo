from dataclasses import dataclass, asdict
from typing import List


@dataclass
class UserInfoResponse:
    id: int
    name: str
    username: str
    email: str
    roles: List[str]
    latestStatusInOut: str
    latestCheckInTime: str
    latestCheckOutTime: str
    companyId: str

    def to_dict(self):
        return asdict(self)
