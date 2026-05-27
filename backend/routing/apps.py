import logging
import os
import sys

from django.apps import AppConfig

from .services.graph_loader import load_graph


logger = logging.getLogger(__name__)


class RoutingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'routing'

    def ready(self) -> None:
        # if 'runserver' not in sys.argv:
        #     return

        if os.environ.get('RUN_MAIN') not in (None, 'true'):
            return

        try:
            load_graph()
        except Exception as exc:
            logger.warning('Failed to preload routing graph: %s', exc)
