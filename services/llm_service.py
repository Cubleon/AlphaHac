import os
from typing import Iterator, Optional, List, Dict, Any
import lmstudio as lms
from markdown_pdf import MarkdownPdf, Section
import io
from utils.helpers import pptx_to_pdf
import fitz

from PIL import Image

import pandas as pd

class LMStudioClient:
    """
    Simple wrapper for LM Studio Qwen3-VL-8B (or other models).
    Methods:
      - respond_text_to_text: synchronous full response (string)
      - respond_text_to_stream: generator that yields incremental text fragments
      - respond_image_to_text: send an image + prompt (returns final full response)
    """

    def __init__(self, chat_history: lms.Chat.from_history, model_id: str = "qwen/qwen3-vl-8b", system_prompt: str = None):
        # lazy create model handle on first use
        self.model_id = model_id
        self._model = lms.llm(model_id)
        if chat_history:
            self._chat = chat_history
        else:
            self._chat = lms.Chat()
        self.default_config = {
            "temperature": 0.0,
            "maxTokens": 128
        }

    def get_chat(self):
        return self._chat

    def respond_text_to_text(self, prompt: str,
                             config: Optional[Dict[str, Any]] = None) -> str:
        """
        Synchronous non-streaming full response.
        Returns assistant text.
        """
        self._chat.add_user_message(prompt)
        cfg = dict(self.default_config)
        if config:
            cfg.update(config)
        result = self._model.respond(self._chat, config=cfg, on_message=self._chat.append)
        return result.content

    def respond_text_to_stream(self, prompt: str,
                               config: Optional[Dict[str, Any]] = None) -> Iterator[str]:
        """
        Streaming generator. Yield string fragments as they arrive.
        Use like:
            for chunk in client.respond_text_to_stream("Hello"):
                send_edit_to_telegram(chunk)
        """
        self._chat.add_user_message(prompt)
        cfg = dict(self.default_config)
        if config:
            cfg.update(config)
        # model.respond_text_to_stream yields fragments (objects). Each fragment typically has .content
        stream = self._model.respond_stream(self._chat, config=cfg, on_message=self._chat.append)
        for frag in stream:
            yield frag.content

    def respond_image_to_text(self, prompt: str, path_to_image: str,
                              config: Optional[Dict[str, Any]] = None) -> str:
        """
        Send an image + text prompt. Returns assistant text (non-streaming).
        """
        image_handle = lms.prepare_image(path_to_image)

        self._chat.add_user_message(prompt, images=[image_handle])
        cfg = dict(self.default_config)
        if config:
            cfg.update(config)
        result = self._model.respond(self._chat, config=cfg, on_message=self._chat.append)
        return result.content

    def respond_text_to_pdf(self, prompt: str,
                            config: Optional[Dict[str, Any]] = None) -> io.BytesIO:

        self._chat.add_user_message(prompt)
        cfg = dict(self.default_config)

        if config:
            cfg.update(config)
        result = self._model.respond(self._chat, config=cfg, on_message=self._chat.append).content

        title = prompt if len(prompt) <= 80 else prompt[:77] + "..."
        result = f"# {title}\n\n" + result

        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(result))
        pdf.save("output.pdf")
        out_bytes = io.BytesIO()
        pdf.save_bytes(out_bytes)

        out_bytes.seek(0)
        return out_bytes

    def respond_text_to_table(self, prompt: str,
                              config: Optional[Dict[str, Any]] = None) -> io.BytesIO:
        self._chat.add_user_message(prompt)
        cfg = dict(self.default_config)
        if config:
            cfg.update(config)
        result = self._model.respond(self._chat, config=cfg, on_message=self._chat.append).content

        lines = [ln.rstrip() for ln in result.splitlines() if '|' in ln]
        table_text = "\n".join(lines)
        cleaned = "\n".join(line.strip().strip('|') for line in lines)

        df = pd.read_csv(io.StringIO(cleaned), sep=r'\s*\|\s*', engine='python')

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Table1")

        buf.seek(0)  # rewind so the caller can read from the start
        return buf

    def respond_pdf_to_text(self, prompt: str, path_to_pdf: str, config: Optional[Dict[str, Any]] = None) -> str:
        doc = fitz.open(path_to_pdf)
        zoom = 0.5
        mat = fitz.Matrix(zoom, zoom)

        image_handles = []

        for i in range(doc.page_count):
            page = doc[i]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            img.save(f"page_{i + 1}.png")
            image_handles.append(lms.prepare_image(f"page_{i + 1}.png"))
            os.remove(f"page_{i + 1}.png")

        self._chat.add_user_message(prompt, images=image_handles)

        cfg = dict(self.default_config)
        if config:
            cfg.update(config)

        result = self._model.respond(self._chat, config=cfg, on_message=self._chat.append).content

        return result

    def respond_pptx_to_text(self, prompt: str, path_to_pptx: str, config: Optional[Dict[str, Any]] = None) -> str:
        path_to_pdf = path_to_pptx.replace(".pptx", ".pdf")
        pptx_to_pdf(path_to_pptx)
        self.respond_pdf_to_text(prompt, path_to_pdf, config)