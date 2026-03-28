"""
SYSTEM 1 — AI-Powered File Organizer
Watches C:\\Higgsfield_Exports for new images, identifies the model via
Claude Vision API, renames, and sorts them into the content folder tree.
"""

import os
import sys
import time
import shutil
import base64
import logging
from pathlib import Path

import anthropic
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

# ── Claude client ────────────────────────────────────────────────────────
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def encode_image(path: str) -> tuple[str, str]:
    """Read an image file and return (base64_data, media_type)."""
    ext = Path(path).suffix.lower()
    media_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    media_type = media_map.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def identify_model(image_path: str) -> tuple[str, float]:
    """
    Send an image to Claude Vision and ask which model is in the photo.
    Returns (model_key, confidence) e.g. ("Savannah", 0.95).
    """
    img_data, media_type = encode_image(image_path)

    model_descriptions = "\n".join(
        f"- {v['description']}" for v in MODELS.values()
    )
    model_keys = ", ".join(MODELS.keys())

    prompt = f"""You are an image analyst for a content team. Look at this photo
and determine which model is pictured.

Here are the two possible models:
{model_descriptions}

Respond with EXACTLY two lines and nothing else:
MODEL: <one of: {model_keys}>
CONFIDENCE: <a number from 0.0 to 1.0>

If you truly cannot tell, respond:
MODEL: Unknown
CONFIDENCE: 0.0
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    text = response.content[0].text.strip()
    model_key = "Unknown"
    confidence = 0.0

    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("MODEL:"):
            raw = line.split(":", 1)[1].strip()
            # Match against known keys (case-insensitive)
            for key in MODELS:
                if key.lower() == raw.lower():
                    model_key = key
                    break
        elif line.upper().startswith("CONFIDENCE:"):
            try:
                confidence = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    return model_key, confidence


def ask_batch_info() -> tuple[str, str]:
    """Prompt the operator for the day and post number."""
    print("\n" + "=" * 60)
    raw = input(
        "Which day and post number is this batch? (e.g. Thursday Post 2): "
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


def process_batch(image_paths: list[str], day: str, post: str):
    """Identify, rename, and sort a batch of images."""
    for frame_num, src_path in enumerate(sorted(image_paths), start=1):
        original_name = os.path.basename(src_path)
        ext = Path(src_path).suffix.lower()

        log.info(f"Analyzing {original_name} ...")
        model_key, confidence = identify_model(src_path)

        if model_key == "Unknown":
            log.warning(
                f"  Could not identify model in {original_name} "
                f"(confidence {confidence:.2f}). Skipping."
            )
            continue

        # Build new filename: Savannah_Thursday_Post2_Frame1.jpg
        new_name = f"{model_key}_{day}_{post}_Frame{frame_num}{ext}"

        # Build destination folder: C:\Content\Savannah\Thursday\Post2\
        dest_folder = os.path.join(CONTENT_ROOT, model_key, day, post)
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, new_name)

        shutil.copy2(src_path, dest_path)
        log.info(
            f"  -> {new_name}  (model={model_key}, conf={confidence:.2f})  "
            f"-> {dest_folder}"
        )

        # Log to database (also updates tracker dashboard)
        log_file(
            original_name=original_name,
            new_name=new_name,
            model=model_key,
            confidence=confidence,
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

        day, post = ask_batch_info()
        log.info(f"Processing as {day} / {post}")
        process_batch(batch, day, post)


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
    day, post = ask_batch_info()
    process_batch(images, day, post)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        run_manual()
    else:
        run_watcher()
