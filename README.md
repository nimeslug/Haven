# Haven 🏡

> A cozy desktop companion — meet **Pamuk**, a pixel-art bunny who lives on your screen, hops around, sleeps, and reacts to your cursor.

Haven is an extensible desktop pet framework built with Python and PySide6. It ships with Pamuk 🐰, but its plugin-style architecture lets you add new animals by simply dropping a folder into `assets/`.

## ✨ Features

### Pamuk the Bunny
- 🫧 **Breathing animation** — subtle float effect makes her feel alive
- 👁️ **Reactive gaze** — she looks up, down, left, right based on your cursor position
- 🐾 **Hop-based movement** — walks across the screen with a natural bouncy gait
- 💤 **Sleep mode** — curls up and sleeps after inactivity
- 😴 **Yawns, blinks, ear wiggles** — random idle behaviors keep her charming
- 💨 **Personal space** — hops away when the cursor gets too close
- 💬 **Emoji speech bubbles** — 🥕 ✨ 🌸 🌿 and reactions to interaction
- 🖱️ **Fully draggable** — grab and move her anywhere on screen
- ❤️ **Click to make her happy** — a little jump and a heart bubble

### Technical
- 🪟 **Transparent overlay** — Windows-native layered window with color-key transparency
- 🔌 **Plugin architecture** — each pet is a self-contained folder with a `pet.json` config
- 📥 **System tray integration** — controls without opening the pet's context menu
- 🎨 **Modular animation system** — behaviors defined as JSON, no code changes needed

## 🚀 Getting Started

### Requirements
- Windows 10 or later
- Python 3.10+

### Installation

Clone the repo:
`git clone https://github.com/YOUR_USERNAME/haven.git`
`cd haven`

Create a virtual environment and install dependencies:
`python -m venv venv`
`venv\Scripts\activate`
`pip install -r requirements.txt`

Run:
`python src\main.py`

## 🎮 Usage

- **Left-click** Pamuk to make her happy — she'll do a little jump 💗
- **Left-click and drag** to move her around
- **Right-click** for the context menu (sleep, switch pet, quit)
- **Tray icon** in the system tray for quick access even when she's hidden
- **Move your cursor near her** — she'll notice and react

## 🐹 Adding a New Pet

The architecture is designed so that adding a new animal requires **zero code changes**. Simply:

1. Create a new folder under `assets/`, e.g. `assets/capybara/`
2. Add your sprite frames (PNGs with transparent background)
3. Create a `pet.json` describing the pet's behaviors, walk cycle, sleep pose, etc.
4. Restart the app — the new pet appears in the "Switch pet" menu

See `assets/bunny/pet.json` as a reference.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **UI Framework:** PySide6 (Qt for Python)
- **Platform:** Windows 10+ (uses `SetLayeredWindowAttributes` for reliable transparency)
- **Art:** AI-generated pixel art (via ChatGPT), background-cleaned

## 📁 Project Structure
Haven/
├── assets/
│   └── bunny/              # Pamuk's sprites and config
│       ├── pet.json
│       └── *.png
├── src/
│   ├── main.py             # Entry point
│   ├── overlay.py          # Transparent draggable window
│   ├── animator.py         # Animation and behavior engine
│   └── pet_loader.py       # Loads pets from assets/
├── requirements.txt
└── README.md
## 🗺️ Roadmap

- [x] Transparent overlay window
- [x] Idle behaviors (blink, yawn, ear wiggle)
- [x] Hop-based walking with direction awareness
- [x] Sleep mode with dedicated sleep sprite
- [x] Emoji speech bubbles
- [x] Cursor tracking (look up / down / left / right)
- [x] Flee behavior when cursor gets too close
- [x] System tray icon
- [ ] Control panel with tabs (quick commands, settings, chat, reminders)
- [ ] Standalone `.exe` build
- [ ] More pets: Bambi 🦌, Capybara 🐹

## 📜 License

MIT — see `LICENSE` file.

## 🙏 Acknowledgments

- Inspired by [myCat](https://github.com/yumiaura/myCat) — a lovely desktop cat that started this whole idea
- Pixel art frames generated with ChatGPT, background cleaning done manually

---

Built with love and a lot of `QPainter` magic. 🎨