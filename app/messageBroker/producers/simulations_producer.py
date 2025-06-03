from app.messageBroker.producers.base_producer import BaseProducer
from app.models.statuses_enums import EventType
from app.models.message_bus_models import OutboxPublisher
from app.app_container import app_container

class SimulationsProducer(BaseProducer):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        self.config = app_container.config()
        super().__init__(rabbitmq_manager, exchange_name, db, self.config.SIMULATION_QUEUE)
        self._initialize_outbox_publisher()

    def _initialize_outbox_publisher(self):
        """Initialize the outbox publisher with simulation-specific configuration."""
        self.outbox_publisher = OutboxPublisher(
            max_parallel=self.config.MAX_SIMULATIONS_IN_PARALLEL_PUBLISHER,
            initial_delay=self.config.INITIAL_DELAY,
            max_retries=self.config.MAX_RETRIES,
            retry_delay=self.config.RETRY_DELAY,
            batch_size_events_query=50,
            max_messages_to_publish=self.config.MAX_SIMULATIONS_IN_PARALLEL_PUBLISHER
        )

    def _get_event_filter(self):
        """Get the filter for simulation events."""
        return {
            "published": False,
            "event_type": {
                "$in": [
                    EventType.SIMULATION_CREATED.value,
                    EventType.SIMULATION_UPDATED.value,
                    EventType.SIMULATION_STOPPED.value,
                    EventType.SIMULATION_COMPLETED.value
                ]
            }
        }