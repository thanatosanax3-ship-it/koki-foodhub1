from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    def ready(self):
        # Ensure media directories exist on startup to avoid runtime write errors
        try:
            from django.conf import settings
            import os
            import logging

            logger = logging.getLogger(__name__)
            media_root = getattr(settings, 'MEDIA_ROOT', None)
            if media_root:
                # Create media root
                if not os.path.exists(media_root):
                    os.makedirs(media_root, exist_ok=True)
                    logger.info(f'Created MEDIA_ROOT at startup: {media_root}')

                # Ensure products subdirectory exists
                products_dir = os.path.join(media_root, 'products')
                if not os.path.exists(products_dir):
                    os.makedirs(products_dir, exist_ok=True)
                    logger.info(f'Created products media dir at startup: {products_dir}')
        except Exception:
            # Avoid raising during app registry; only log problems
            import logging, traceback
            logging.getLogger(__name__).warning('Failed to ensure media directories at startup:\n%s', traceback.format_exc())
