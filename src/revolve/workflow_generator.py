from queue import SimpleQueue
from revolve.main import run_workflow

def run_workflow_generator(task, db_config=None):
    q = SimpleQueue()

    def send(msg):
        q.put(msg)

    def runner():
        run_workflow(task=task, db_config=db_config, send=send)
        q.put(None)  # sentinel to stop

    import threading
    threading.Thread(target=runner, daemon=True).start()

    while True:
        item = q.get()
        if item is None:
            break
        yield item