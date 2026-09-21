"""App config, which exists for one reason: to warm the local model.

A cold generate against Ollama costs about 25 seconds while the weights load.
Every call after it costs under one. Without this, the first person to open the
app pays that 25 seconds and concludes the assistant is broken.

Warming happens on a daemon thread so it never delays the server coming up, and
only when a server is actually being started — running it during ``test`` or
``migrate`` would load half a gigabyte of weights to do nothing with them.
"""

from __future__ import annotations

import sys
import threading

from django.apps import AppConfig

SERVER_COMMANDS = {'runserver', 'daphne', 'runworker', 'gunicorn', 'uvicorn'}


class AiConfig(AppConfig):
    name = 'ai'
    verbose_name = 'AI'

    def ready(self) -> None:
        if not any(command in sys.argv for command in SERVER_COMMANDS):
            return

        from . import client

        threading.Thread(target=client.warm, name='ollama-warm', daemon=True).start()
