from google.cloud import pubsub_v1

from ..logger import Logger

logger = Logger(__name__)


def publish_message(message, project_id, topic_id):
    """Publishes messages to a Pub/Sub topic."""

    try:
        publisher = pubsub_v1.PublisherClient()

        # The `topic_path` method creates a fully qualified identifier
        # in the form `projects/{project_id}/topics/{topic_id}`
        topic_path = publisher.topic_path(project_id, topic_id)

        # Data must be a bytestring
        data = message.encode("utf-8")

        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data)

        message_uuid = future.result()
        logger.info(f"Message {message_uuid} published to {topic_path}")

    except Exception as e:
        logger.exception(e)
