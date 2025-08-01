from dataclasses import dataclass, asdict, field, is_dataclass


@dataclass
class RootResponse:
    status: str = "success"
    message: str = ""
    data: any = field(default=None)

    def to_dict(self):
        return {
            "status": self.status,
            "message": self.message,
            "data": asdict(self.data) if is_dataclass(self.data) else self.data
        }
