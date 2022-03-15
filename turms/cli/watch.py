import asyncio
import asyncio
import sys
import time
from rich.console import Console
from watchdog.observers import Observer
from watchdog.events import (
    FileModifiedEvent,
    FileSystemEventHandler,
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


console = Console()


class QueueHandler(FileSystemEventHandler):
    def __init__(self, *args, sync_q=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.queue = sync_q

    def on_any_event(self, event):
        self.queue.put(event)
        self.queue.join()


def watcher(path, queue, event: threading.Event):
    try:
        console.print(f"Watching path {path}")
        event_handler = QueueHandler(sync_q=queue)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()

        with console.status("Watching"):
            while not event.is_set():
                time.sleep(1)
    except Exception as e:
        console.print(f"Error: {e}")


async def buffered_queue(queue, timeout=4):
    buffer = [None]

    async def iterator():
        while True:
            nana = await queue.get()
            queue.task_done()
            if isinstance(nana, FileModifiedEvent):
                console.print("modified file")
                if nana.src_path.lower().endswith((".graphql")):
                    buffer.append(nana)

    loop = asyncio.get_event_loop()
    loop.create_task(iterator())
    while True:
        await asyncio.sleep(timeout)
        yield buffer[len(buffer) - 1]
        buffer = [None]


class Host:
    def __init__(self, path=None, config_path=None, project=None) -> None:
        self.config_path = config_path
        self.watch_path = os.path.join(
            os.getcwd(),
            "/".join(
                path.split("*")[0].split("/")[:-1]
            ),  # should get root path even if using glob
        )
        self.console = Console()
        self.project = project

    async def restart(self):
        console.print("Restarting Generation")
        try:
            gen(self.config_path, project=self.project)
        except Exception as e:
            console.print("Generation Failed")
            console.print_exception()

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

    project = project or list(yaml_dict["projects"].items())[0][0]

    config = GraphQLConfig(**yaml_dict["projects"][project], domain=project)
    console.print(f"Running filewatcher for project: {project}")

    host = Host(path=config.documents, config_path=filepath, project=project)
    asyncio.run(host.run())
