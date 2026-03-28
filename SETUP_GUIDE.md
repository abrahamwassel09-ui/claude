# AI Content Automation System — Setup Guide (Windows)

This guide walks you through everything from scratch on a Windows PC.

---

## STEP 1: Install Python

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer
4. **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom of the first screen
5. Click **"Install Now"**
6. When it finishes, click **"Close"**

**Verify it worked:** Open Command Prompt (press `Win + R`, type `cmd`, press Enter) and type:
```
python --version
```
You should see something like `Python 3.12.x`.

---

## STEP 2: Download the Project

Put all the project files into a single folder, for example:
```
C:\ContentAutomation\
```

The folder should contain these files:
```
C:\ContentAutomation\
    config.py
    database.py
    organizer.py
    dashboard.py
    requirements.txt
    templates\
        dashboard.html
        log.html
    static\
        style.css
```

---

## STEP 3: Install Required Libraries

Open Command Prompt and navigate to the project folder:
```
cd C:\ContentAutomation
```

Then install everything with one command:
```
pip install -r requirements.txt
```

This installs:
- **anthropic** — Claude AI API (for image analysis)
- **watchdog** — File system watcher (detects new images)
- **flask** — Web framework (for the dashboard)
- **Pillow** — Image handling library

---

## STEP 4: Set Up Your Claude API Key

You need an API key from Anthropic to use Claude Vision.

1. Go to **https://console.anthropic.com/**
2. Sign up or log in
3. Go to **API Keys** and create a new key
4. Copy the key (it starts with `sk-ant-...`)

Now set it as an environment variable. In Command Prompt:
```
setx ANTHROPIC_API_KEY "sk-ant-your-key-here"
```

**Close and reopen Command Prompt** for this to take effect.

**Verify it worked:**
```
echo %ANTHROPIC_API_KEY%
```
You should see your key printed.

---

## STEP 5: Create the Watch Folder

Create the folder where you'll drop Higgsfield exports:
```
mkdir C:\Higgsfield_Exports
```

The organizer will create `C:\Content\` and all subfolders automatically.

---

## STEP 6: Initialize the Database

This creates the SQLite database and seeds the post grid:
```
cd C:\ContentAutomation
python database.py
```

You should see: `Database initialized at C:\ContentAutomation\content_tracker.db`

---

## STEP 7: Run the System

You need **two Command Prompt windows** open at the same time.

### Window 1 — File Organizer
```
cd C:\ContentAutomation
python organizer.py
```
You'll see: `Watching folder: C:\Higgsfield_Exports`

### Window 2 — Dashboard
```
cd C:\ContentAutomation
python dashboard.py
```
You'll see: `Dashboard running at http://127.0.0.1:5000`

Open your browser and go to: **http://127.0.0.1:5000**

---

## HOW TO USE IT

### Sorting Images
1. Export images from Higgsfield
2. Drop them into `C:\Higgsfield_Exports`
3. The organizer detects them and asks: **"Which day and post number is this batch?"**
4. Type something like: `Thursday Post 2` and press Enter
5. Claude Vision analyzes each image, identifies the model, and sorts them into:
   ```
   C:\Content\Savannah\Thursday\Post2\Savannah_Thursday_Post2_Frame1.jpg
   C:\Content\Keliah\Thursday\Post2\Keliah_Thursday_Post2_Frame1.jpg
   ```
6. The dashboard automatically updates to show "Has Images: Yes"

### Manual Mode
If images are already in the folder before you start the organizer:
```
python organizer.py --manual
```

### Updating Post Status
- Open the dashboard at **http://127.0.0.1:5000**
- Use the dropdown on each post to set: **Not Started / Written / Approved / Scheduled / Posted**
- The dashboard auto-refreshes every 30 seconds

### Viewing the File Log
- Click **"File Log"** in the top nav to see every file that was processed
- Shows: timestamp, original name, new name, model, confidence score

---

## FOLDER STRUCTURE (after sorting)

```
C:\Content\
    Savannah\
        Thursday\
            Post1\
                Savannah_Thursday_Post1_Frame1.jpg
                Savannah_Thursday_Post1_Frame2.jpg
            Post2\
                ...
        Friday\
            ...
    Keliah\
        Thursday\
            Post1\
                Keliah_Thursday_Post1_Frame1.jpg
            ...
```

---

## CUSTOMIZATION

Edit **config.py** to change:
- `WATCH_FOLDER` — where to watch for new images
- `CONTENT_ROOT` — where sorted files go
- `DAYS` — which days to track (default: Thu–Sun)
- `POSTS_PER_DAY` — how many posts per day (default: 3)
- `MODELS` — add/remove/edit model descriptions
- `DASHBOARD_PORT` — change the web port (default: 5000)

---

## TROUBLESHOOTING

**"python is not recognized"**
- You didn't check "Add Python to PATH" during install. Reinstall Python and check the box.

**"ModuleNotFoundError: No module named 'anthropic'"**
- Run `pip install -r requirements.txt` again from the project folder.

**"Error: ANTHROPIC_API_KEY not set"**
- Make sure you ran `setx ANTHROPIC_API_KEY "your-key"` and reopened Command Prompt.

**Dashboard shows "Has Images: No" after sorting**
- Both scripts share the same database file. Make sure both are running from the same folder.

**Images not detected**
- Make sure you're dropping files into `C:\Higgsfield_Exports` (not a subfolder).
- Only image files are detected (.jpg, .png, .webp, .gif, .bmp).
