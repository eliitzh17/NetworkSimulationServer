import functions_framework
from app.workers.consumer_workers.consumer_simulations_worker import MultiQueueConsumerWorker

@functions_framework.http
def consumer_simulations_worker(request):
    # TODO: Parse event/message from request if needed
    # You must implement a process_event method in MultiQueueConsumerWorker
    worker = MultiQueueConsumerWorker()
    # Example: worker.process_event(request.get_json())
    # For now, just call setup_and_run for demo (should be refactored for real use)
    import asyncio
    asyncio.run(worker.setup_and_run())
    return "Processed", 200 