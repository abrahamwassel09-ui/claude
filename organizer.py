"""
SYSTEM 1 — File Organizer
Watches C:\\Higgsfield_Exports for new images, prompts you for the model
and day/post, then renames and sorts them into the content folder tree.
"""

import os
import sys
import time
import shutil
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import (
    WATCH_FOLDER,
    CONTENT_ROOT,
    IMAGE_EXTENSIONS,
    MODELS,
    LOG_PATH,
)
from database import init_db, log_file

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("organizer")

# Build a lookup for the model selection prompt
MODEL_KEYS = list(MODELS.keys())


def ask_model() -> str:
    """Prompt the operator to pick which model this batch is for."""
    print("\n" + "=" * 60)
    options = " / ".join(
        f"{i + 1} for {MODELS[k]['full_name']}" for i, k in enumerate(MODEL_KEYS)
    )
    raw = input(f"Which model? ({options}): ").strip()
    print("=" * 60)

    # Accept a number or a name
    for i, key in enumerate(MODEL_KEYS):
        if raw == str(i + 1) or raw.lower() == key.lower():
            return key

    # Default to first model if input is unrecognized
    print(f"  Unrecognized input '{raw}', defaulting to {MODEL_KEYS[0]}.")
    return MODEL_KEYS[0]


def ask_batch_info() -> tuple[str, str]:
    """Prompt the operator for the day and post number."""
    raw = input(
        "Which day and post number? (e.g. Thursday Post 2): "
    ).strip()
    print("=" * 60 + "\n")

    parts = raw.replace(",", " ").split()
    day = parts[0].capitalize() if parts else "Thursday"

    # Extract post number
    post_num = "1"
    for p in parts[1:]:
        digits = "".join(c for c in p if c.isdigit())
        if digits:
            post_num = digits
            break

    post_label = f"Post{post_num}"
    return day, post_label


def process_batch(image_paths: list[str], model_key: str, day: str, post: str):
    """Rename and sort a batch of images."""
    for frame_num, src_path in enumerate(sorted(image_paths), start=1):
        original_name = os.path.basename(src_path)
        ext = Path(src_path).suffix.lower()

        # Build new filename: Savannah_Thursday_Post2_Frame1.jpg
        new_name = f"{model_key}_{day}_{post}_Frame{frame_num}{ext}"

        # Build destination folder: C:\Content\Savannah\Thursday\Post2\
        dest_folder = os.path.join(CONTENT_ROOT, model_key, day, post)
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, new_name)

        shutil.copy2(src_path, dest_path)
        log.info(f"  {original_name}  ->  {new_name}  ->  {dest_folder}")

        # Log to database (also updates tracker dashboard)
        log_file(
            original_name=original_name,
            new_name=new_name,
            model=model_key,
            confidence=1.0,
            day=day,
            post=post,
            frame=frame_num,
            dest_path=dest_path,
        )

    log.info("Batch complete.\n")


# ── Folder watcher ───────────────────────────────────────────────────────

class NewImageHandler(FileSystemEventHandler):
    """Collects new image files, then processes them as a batch."""

    def __init__(self):
        super().__init__()
        self._pending: list[str] = []
        self._last_event_time = 0.0
        self._batch_delay = 3.0  # seconds to wait after last new file

    def on_created(self, event):
        if event.is_directory:
            return
        ext = Path(event.src_path).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            self._pending.append(event.src_path)
            self._last_event_time = time.time()
            log.info(f"Detected new file: {os.path.basename(event.src_path)}")

    def check_and_process(self):
        """Called in the main loop; fires batch when files settle."""
        if not self._pending:
            return
        if time.time() - self._last_event_time < self._batch_delay:
            return  # still receiving files

        batch = list(self._pending)
        self._pending.clear()

        log.info(f"\n{'='*60}")
        log.info(f"New batch detected: {len(batch)} image(s)")
        log.info(f"{'='*60}")

        model_key = ask_model()
        day, post = ask_batch_info()
        log.info(f"Processing as {model_key} / {day} / {post}")
        process_batch(batch, model_key, day, post)


def run_watcher():
    """Start watching the export folder."""
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    init_db()

    handler = NewImageHandler()
    observer = Observer()
    observer.schedule(handler, WATCH_FOLDER, recursive=False)
    observer.start()

    log.info(f"Watching folder: {WATCH_FOLDER}")
    log.info("Drop images into the folder. Press Ctrl+C to stop.\n")

    try:
        while True:
            handler.check_and_process()
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Stopping watcher...")
        observer.stop()
    observer.join()


# ── Manual mode (process files already in folder) ────────────────────────

def run_manual():
    """Process all images currently sitting in the watch folder."""
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    init_db()

    images = [
        os.path.join(WATCH_FOLDER, f)
        for f in os.listdir(WATCH_FOLDER)
        if Path(f).suffix.lower() in IMAGE_EXTENSIONS
    ]
    if not images:
        print(f"No images found in {WATCH_FOLDER}")
        return

    print(f"Found {len(images)} image(s) in {WATCH_FOLDER}")
    model_key = ask_model()
    day, post = ask_batch_info()
    process_batch(images, model_key, day, post)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        run_manual()
    else:
        run_watcher()
