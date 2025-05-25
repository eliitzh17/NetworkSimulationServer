import functions_framework
from app.workers.outbox_publishers_workers.publish_completed_worker import main as worker_main

@functions_framework.http
def publish_completed_worker(request):
    # TODO: Parse event/message from request if needed
    worker_main()  # Should be refactored to process a single event
    return "Completed", 200 