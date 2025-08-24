#!/usr/bin/env python3

from config.settings import Settings

settings = Settings()
retention_hours = settings.get("DATA_RETENTION_HOURS")
print(f"DATA_RETENTION_HOURS: {retention_hours}")
print(f"This means products older than {retention_hours} hours will be automatically removed.")
