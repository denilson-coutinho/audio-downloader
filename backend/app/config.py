from dataclasses import dataclass
import os


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número inteiro") from exc
    if value <= 0:
        raise ValueError(f"{name} deve ser maior que zero")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    processing_timeout_seconds: int = _positive_int("PROCESSING_TIMEOUT_SECONDS", 300)
    socket_timeout_seconds: int = _positive_int("SOCKET_TIMEOUT_SECONDS", 30)
    max_file_size_mb: int = _positive_int("MAX_FILE_SIZE_MB", 200)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()

