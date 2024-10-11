import uuid


def orm_id():
    return str(uuid.uuid4())


def short_id():
    return str(uuid.uuid4())[:8]
