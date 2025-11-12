from typing import Iterator, Optional, List, Dict, Any
import lmstudio as lms
import threading
import time

class LMStudioQwenClient:
    """
    Simple wrapper for LM Studio Qwen3-VL-8B (or other models).
    Methods:
      - respond_text: synchronous full response (string)
      - respond_stream: generator that yields incremental text fragments
      - respond_with_image: send an image + prompt (returns final full response)
    """

    def __init__(self, model_id: str = "qwen/qwen3-vl-8b", system_prompt: Optional[str] = None):
        # lazy create model handle on first use
        self.model_id = model_id
        self._model = lms.llm(model_id)
        self._system_prompt = system_prompt or "You are a helpful assistant."
        # optional default config
        self.default_config = {
            "temperature": 0.0,
            "maxTokens": 1024,
        }

    def _build_chat(self, user_text: str, chat_history: Optional[List[Dict[str, str]]] = None) -> lms.Chat:
        """
        Build a Chat instance. chat_history is a list of messages in OpenAI style:
          [{"role":"user","content":"..."},
           {"role":"assistant","content":"..."}]
        """
        chat = lms.Chat(self._system_prompt)
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    chat.add_user_message(content)
                elif role == "assistant":
                    chat.add_assistant_response(content)
                else:
                    # fallback: append as user message
                    chat.add_user_message(content)
        chat.add_user_message(user_text)
        return chat

    def respond_text(self, prompt: str, chat_history: Optional[List[Dict[str, str]]] = None,
                     config: Optional[Dict[str, Any]] = None) -> str:
        """
        Synchronous non-streaming full response.
        Returns assistant text.
        """
        chat = self._build_chat(prompt, chat_history)
        cfg = dict(self.default_config)
        if config:
            cfg.update(config)
        result = self._model.respond(chat, config=cfg)
        # result typically has a .content or str(result) returns content
        return result.content

    def respond_stream(self, prompt: str, chat_history: Optional[List[Dict[str, str]]] = None,
                       config: Optional[Dict[str, Any]] = None) -> Iterator[str]:
        """
        Streaming generator. Yield string fragments as they arrive.
        Use like:
            for chunk in client.respond_stream("Hello"):
                send_edit_to_telegram(chunk)
        """
        chat = self._build_chat(prompt, chat_history)
        cfg = dict(self.default_config)
        if config:
            cfg.update(config)
        # model.respond_stream yields fragments (objects). Each fragment typically has .content
        stream = self._model.respond_stream(chat, config=cfg)
        for frag in stream:
            yield frag.content
    def respond_with_image(self, prompt: str, path_to_image: str,
                           chat_history: Optional[List[Dict[str, str]]] = None,
                           config: Optional[Dict[str, Any]] = None) -> str:
        """
        Send an image + text prompt. Returns assistant text (non-streaming).
        """
        chat = self._build_chat("", chat_history)  # start with system + history
        # now add user message with image
        image_handle = lms.prepare_image(path_to_image)
        chat.add_user_message(prompt, images=[image_handle])
        cfg = dict(self.default_config)
        if config:
            cfg.update(config)
        result = self._model.respond(chat, config=cfg)
        return result.content