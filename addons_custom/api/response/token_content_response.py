from dataclasses import dataclass, asdict, field

from ..response.user_info_response import UserInfoResponse


@dataclass
class TokenContentResponse:
    accessToken: str
    refreshToken: str
    expiresIn: int
    tokenType: str = "Bearer"
    user: UserInfoResponse = field(default=None)

    def to_dict(self):
        return asdict(self)
