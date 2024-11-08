from typing import Optional, List

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class Action(BaseModel):
    action: str = Field(..., description="Action name")
    label: str = Field(..., description="Action label")
    url: str = Field(..., description="Action URL")
    clear: Optional[bool] = Field(False, description="Clear notification after action button is tapped")


class NotificationRequest(BaseModel):
    topic: str = Field(..., description="Target topic name")
    message: Optional[str] = Field("👋 Hello there", description="Message body")
    title: Optional[str] = Field("Notification", description="Message title")
    tags: Optional[List[str]] = Field(["notification"], description="List of tags that may or not map to emojis")
    priority: Optional[int] = Field(3, description="Message priority with 1=min, 3=default and 5=max")
    actions: Optional[List[Action]] = Field(
        default_factory=list, description="Custom user action buttons for notifications"
    )
    click: Optional[str] = Field(None, description="Website opened when notification is clicked")
    attach: Optional[str] = Field(None, description="URL of an attachment")
    markdown: Optional[bool] = Field(True, description="Set to true if the message is Markdown-formatted")
    icon: Optional[str] = Field(None, description="URL to use as notification icon")
    filename: Optional[str] = Field(None, description="File name of the attachment")
    delay: Optional[str] = Field(None, description="Timestamp or duration for delayed delivery")
    email: Optional[str] = Field(None, description="E-mail address for e-mail notifications")
    call: Optional[str] = Field(None, description="Phone number to use for voice call")


class Attachment(BaseModel):
    name: str = Field(..., description="Name of the attachment")
    url: str = Field(..., description="URL of the attachment")
    type: Optional[str] = Field(None, description="Mime type of the attachment")
    size: Optional[int] = Field(None, description="Size of the attachment in bytes")
    expires: Optional[int] = Field(None, description="Attachment expiry date as Unix time stamp")


class Notification(BaseModel):
    """JSON message format¶
Both the /json endpoint and the /sse endpoint return a JSON format of the message. It's very straight forward:

Message:

Field	Required	Type	Example	Description
id	✔️	string	hwQ2YpKdmg	Randomly chosen message identifier
time	✔️	number	1635528741	Message date time, as Unix time stamp
expires	(✔)️	number	1673542291	Unix time stamp indicating when the message will be deleted, not set if Cache: no is sent
event	✔️	open, keepalive, message, or poll_request	message	Message type, typically you'd be only interested in message
topic	✔️	string	topic1,topic2	Comma-separated list of topics the message is associated with; only one for all message events, but may be a list in open events
message	-	string	Some message	Message body; always present in message events
title	-	string	Some title	Message title; if not set defaults to ntfy.sh/<topic>
tags	-	string array	["tag1","tag2"]	List of tags that may or not map to emojis
priority	-	1, 2, 3, 4, or 5	4	Message priority with 1=min, 3=default and 5=max
click	-	URL	https://example.com	Website opened when notification is clicked
actions	-	JSON array	see actions buttons	Action buttons that can be displayed in the notification
attachment	-	JSON object	see below	Details about an attachment (name, URL, size, ...)
Attachment (part of the message, see attachments for details):

Field	Required	Type	Example	Description
name	✔️	string	attachment.jpg	Name of the attachment, can be overridden with X-Filename, see attachments
url	✔️	URL	https://example.com/file.jpg	URL of the attachment
type	-️	mime type	image/jpeg	Mime type of the attachment, only defined if attachment was uploaded to ntfy server
size	-️	number	33848	Size of the attachment in bytes, only defined if attachment was uploaded to ntfy server
expires	-️	number	1635528741	Attachment expiry date as Unix time stamp, only defined if attachment was uploaded to ntfy server
Here's an example for each message type:


Notification message
Notification message (minimal)
Open message
Keepalive message
Poll request message
{
    "id": "sPs71M8A2T",
    "time": 1643935928,
    "expires": 1643936928,
    "event": "message",
    "topic": "mytopic",
    "priority": 5,
    "tags": [
        "warning",
        "skull"
    ],
    "click": "https://homecam.mynet.lan/incident/1234",
    "attachment": {
        "name": "camera.jpg",
        "type": "image/png",
        "size": 33848,
        "expires": 1643946728,
        "url": "https://ntfy.sh/file/sPs71M8A2T.png"
    },
    "title": "Unauthorized access detected",
    "message": "Movement detected in the yard. You better go check"
}

List of all parameters¶
The following is a list of all parameters that can be passed when subscribing to a message. Parameter names are case-insensitive, and can be passed as HTTP headers or query parameters in the URL. They are listed in the table in their canonical form.

Parameter	Aliases (case-insensitive)	Description
poll	X-Poll, po	Return cached messages and close connection
since	X-Since, si	Return cached messages since timestamp, duration or message ID
scheduled	X-Scheduled, sched	Include scheduled/delayed messages in message list
id	X-ID	Filter: Only return messages that match this exact message ID
message	X-Message, m	Filter: Only return messages that match this exact message string
title	X-Title, t	Filter: Only return messages that match this exact title string
priority	X-Priority, prio, p	Filter: Only return messages that match any priority listed (comma-separated)
tags	X-Tags, tag, ta	Filter: Only return messages that match all listed tags (comma-separated)
Made with ❤️ by Philipp C. Heckel
Made with Material for MkDocs
"""
    id: str = Field(..., description="Randomly chosen message identifier")
    time: int = Field(..., description="Message date time, as Unix time stamp")
    expires: Optional[int] = Field(None, description="Unix time stamp indicating when the message will be deleted")
    event: str = Field(..., description="Message type, typically you'd be only interested in message")
    topic: str = Field(..., description="Comma-separated list of topics the message is associated with")
    message: str = Field(..., description="Message body")
    title: Optional[str] = Field(None, description="Message title")
    tags: Optional[List[str]] = Field(None, description="List of tags that may or not map to emojis")
    priority: Optional[int] = Field(None, description="Message priority with 1=min, 3=default and 5=max")
    click: Optional[str] = Field(None, description="Website opened when notification is clicked")
    actions: Optional[List[Action]] = Field(None, description="Custom user action buttons for notifications")
    attachment: Optional[Attachment] = Field(None, description="Details about an attachment (name, URL, size, ...)")