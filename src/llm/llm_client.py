import logging
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletion,
)

from llm.llm_client_types import Role


class LLMClient:
    def __init__(
        self,
        history: bool = True,
        systemPrompt: str = 'You are a helpful assistant.',
        baseURL: str = 'http://localhost:8080/v1/',
        apiKey: str = 'foobar',
        model: str = 'gpt-3.5-turbo',
        maxTokens: int = 1024,
        temperature: float = 0.7,
    ) -> None:
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.__history: bool = history
        self.__client = OpenAI(base_url=baseURL, api_key=apiKey)
        self.__model: str = model
        self.__maxTokens: int = maxTokens
        self.__temperature: float = temperature
        self.__messages: list[ChatCompletionMessageParam] = []
        self.__addMessage(
            ChatCompletionSystemMessageParam(
                role=Role.SYSTEM.value, content=systemPrompt
            )
        )

    def __addMessage(self, message: ChatCompletionMessageParam) -> bool:
        self.__messages.append(message)
        return True

    def clearHistory(self) -> bool:
        self.__messages = [
            message
            for message in self.__messages
            if message['role'] == Role.SYSTEM.value
        ]
        return True

    def updateSystemPrompt(self, systemPrompt: str) -> bool:
        self.__messages[0] = ChatCompletionSystemMessageParam(
            role=Role.SYSTEM.value, content=systemPrompt
        )
        return True

    def sendMessage(self, message: str, retain: bool = False) -> str:
        self.__addMessage(
            ChatCompletionUserMessageParam(role=Role.USER.value, content=message)
        )
        completion: ChatCompletion = self.__client.chat.completions.create(
            model=self.__model,
            messages=self.__messages,
            max_tokens=self.__maxTokens,
            temperature=self.__temperature,
        )
        response: str | None = completion.choices[0].message.content
        self.__addMessage(
            ChatCompletionAssistantMessageParam(
                role=Role.ASSISTANT.value, content=response
            )
        )
        if not self.__history and not retain:
            self.clearHistory()
        return response or ""
