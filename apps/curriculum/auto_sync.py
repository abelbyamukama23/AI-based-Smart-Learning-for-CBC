import time
import logging
import threading
from django.core.management import call_command

logger = logging.getLogger(__name__)

def _poll_r2_bucket():
    """
    Infinite loop running in a background daemon thread.
    Polls the Cloudflare R2 bucket every 60 seconds.
    If new files are found, it syncs them to the DB and updates the RAG index.
    """
    logger.info("[Auto-Sync] Started R2 background polling thread.")
    
    while True:
        try:
            # Sleep first to give Django time to boot fully before first run
            time.sleep(60)
            
            # 1. Sync from R2
            # We redirect stdout so it doesn't spam the server console every 60s
            # unless we find something.
            import io
            out = io.StringIO()
            
            # Call the sync_from_r2 command programmatically
            call_command("sync_from_r2", stdout=out, stderr=out)
            output = out.getvalue()
            
            # 2. Check if anything was actually created
            if "0 record(s) created" not in output:
                # We found new files!
                logger.info("[Auto-Sync] New files detected in R2 bucket! Syncing to DB...")
                
                # Run the index builder only for the new files
                out_idx = io.StringIO()
                call_command("build_library_index", only_unindexed=True, stdout=out_idx, stderr=out_idx)
                
                logger.info("[Auto-Sync] Sync and RAG indexing complete.")
                
        except Exception as e:
            logger.error("[Auto-Sync] Error during background sync: %s", e)


def start_auto_sync():
    """Starts the background thread. Called from CurriculumConfig.ready()."""
    t = threading.Thread(target=_poll_r2_bucket, daemon=True, name="r2-auto-sync")
    t.start()
