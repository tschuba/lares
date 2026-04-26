def is_uuid(uuid: str) -> bool:
    return len(uuid) == 32 and all(c in "0123456789abcdef" for c in uuid)
