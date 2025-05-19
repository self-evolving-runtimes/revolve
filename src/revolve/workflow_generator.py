from queue import SimpleQueue
from src.revolve.main import run_workflow

def run_workflow_generator(task):
    q = SimpleQueue()

    def send(msg):
        q.put(msg)

    def runner():
        run_workflow(task=task, send=send)
        q.put(None)  # sentinel to stop

    import threading
    threading.Thread(target=runner, daemon=True).start()

    while True:
        item = q.get()
        if item is None:
            break
        yield item