import requests

from agentex.adapters.notifications.port import NotificationPort
from agentex.domain.entities.notifications import NotificationRequest, Notification

NTFY_BASE_URL = "https://ntfy.sh/"


class NtfyAdapter(NotificationPort):

    async def send(self, notification: NotificationRequest) -> Notification:
        response = requests.post(
            url=NTFY_BASE_URL,
            data=notification.to_json(),
        )
        return Notification.from_dict(response.json())
