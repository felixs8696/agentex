from abc import ABC, abstractmethod
from typing import Annotated, Optional

from fastapi import Depends

from agentex.domain.entities.notifications import NotificationRequest, Notification


class NotificationPort(ABC):

    @abstractmethod
    async def send(self, notification: NotificationRequest) -> Notification:
        raise NotImplementedError


DNotificationPort = Annotated[Optional[NotificationPort], Depends(NotificationPort)]
