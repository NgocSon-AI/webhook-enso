from typing import Any
from pydantic import BaseModel, Field


class ZaloAttachment(BaseModel):
    type: str
    payload: str
    payloadObject: Any


class ZaloMetadata(BaseModel):
    attachments: list[ZaloAttachment] = Field([], description="The attachments")
    callback: str | None = Field(None, description="The callback")
    sender_name: str | None = Field(None, description="The sender name")
    channel_id: str | None = Field(None, description="The channel id")
    message_id: str | None = Field(None, description="The message id")


class ZaloChatRequest(BaseModel):
    sender: str | None = Field(None, description="The sender of the message")
    message: str | None = Field(
        None, description="The message of the user input request"
    )
    metadata: ZaloMetadata = Field(description="The metadata of the message")

    def to_comet_input(self) -> dict[str, Any]:
        message: str = self.message or ""
        attachments: list[ZaloAttachment] = self.metadata.attachments
        message_id: str | None = self.metadata.message_id

        urls: list[str] = []
        for attachment in attachments:
            urls.append(attachment.payload)
            message = "\n".join(urls)

        metadata = {
            "sender_name": (
                self.metadata.sender_name if self.metadata.sender_name else ""
            ),
            "message_id": message_id,
            "callback": self.metadata.callback,
            "channel_id": self.metadata.channel_id,
        }

        user_input = {"text": message, "sender_id": self.sender, "metadata": metadata}

        return user_input


class ZaloChatResponse(BaseModel):
    text: str | None = Field(None, description="The response text")

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text}

    @classmethod
    def to_default(cls) -> dict[str, Any]:
        return {"text": None}
