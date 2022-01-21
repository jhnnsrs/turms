from asyncio.tasks import sleep
from importlib import reload, import_module
import asyncio
from arkitekt.actors.registry import get_current_actor_registry, register
from arkitekt.agents.script import ScriptAgent
import fakts
from fakts.fakts import Fakts
import asyncio
import sys
import time
import logging
from rich.console import Console
from watchdog.observers import Observer
from watchdog.events import (
    FileModifiedEvent,
    FileSystemEventHandler,
    LoggingEventHandler,
)
import os
import subprocess
import janus
import threading
import os
import signal
import yaml

from turms.config import GraphQLConfig
from turms.run import gen


class QueueHandler(FileSystemEventHandler):
    def __init__(self, *args, sync_q=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.queue = sync_q

    def on_any_event(self, event):
        self.queue.put(event)
        self.queue.join()


def watcher(path, queue, event: threading.Event):
    try:
        print(f"Wathcing path {path}")
        event_handler = QueueHandler(sync_q=queue)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()

        while not event.is_set():
            time.sleep(1)

        print("Cancelled because threading event is set")
    except:
        print("Watcher failed")


async def buffered_queue(queue, timeout=4):
    buffer = [None]

    async def iterator():
        while True:
            nana = await queue.get()
            queue.task_done()
            if isinstance(nana, FileModifiedEvent):
                print("modified file")
                if nana.src_path.lower().endswith((".graphql")):
                    buffer.append(nana)

    loop = asyncio.get_event_loop()
    loop.create_task(iterator())
    while True:
        await asyncio.sleep(timeout)
        yield buffer[len(buffer) - 1]
        buffer = [None]


class Host:
    def __init__(
        self,
        path=None,
        config_path=None,
    ) -> None:
        self.config_path = config_path
        self.watch_path = os.path.join(
            os.getcwd(), "/".join(path.split("*")[0].split("/")[:-1])
        )
        self.console = Console()

    async def restart(self):
        print("Restarting Generation")
        gen(self.config_path)

    async def run(self):
        jqueue = janus.Queue()

        cancel_event = threading.Event()
        loop = asyncio.get_running_loop()
        fut = loop.run_in_executor(
            None, watcher, self.watch_path, jqueue.sync_q, cancel_event
        )

        try:
            async for event in buffered_queue(jqueue.async_q, timeout=1):
                if event:
                    await self.restart()
        except asyncio.CancelledError as e:
            cancel_event.set()
            await fut

        jqueue.close()
        await jqueue.wait_closed()


def watch(filepath, project=None):

    with open(filepath, "r") as f:
        yaml_dict = yaml.safe_load(f)

    assert "projects" in yaml_dict, "Right now only projects is supported"

    project = project or yaml_dict["projects"].items()[0][1]

    config = GraphQLConfig(**yaml_dict["projects"][project], domain=project)
    print(config)

    host = Host(path=config.documents, config_path=filepath)
    asyncio.run(host.run())
