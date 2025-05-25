import functions_framework
from app.workers.consumer_workers.consumer_links_worker import LinksConsumerWorker

@functions_framework.http
def consumer_links_worker(request):
    # TODO: Parse event/message from request if needed
    # You must implement a process_event method in LinksConsumerWorker
    worker = LinksConsumerWorker()
    # Example: worker.process_event(request.get_json())
    # For now, just call setup_and_run for demo (should be refactored for real use)
    import asyncio
    asyncio.run(worker.setup_and_run())
    return "Processed", 200 