# WitchWay for PortMaster

Port of **WitchWay** by Andrew Gleeson, Henri Rochefort, Niilo Takalainen, and Nathan Antony for PortMaster-compatible Linux handheld gaming devices (muOS, ArkOS, AmberELEC, ROCKNIX, JELOS, etc.).

[![Download PortMaster Zip](https://img.shields.io/badge/Download-witchway.zip-blue?style=for-the-badge&logo=github)](https://github.com/XenoSlug/portmaster-witchway/releases/latest/download/witchway.zip)

## About the Game
*WitchWay* is a charming puzzle-platformer where you play as a young witch lost in a deep, sprawling underground well. Equipped with a magical wand, you can pick up, cast, and manipulate blocks and interactive environmental objects to solve clever physics puzzles, avoid deadly hazards, uncover secrets, and rescue lost bunnies.

## Requirements
- A PortMaster-compatible ARM Linux handheld (e.g. Anbernic RG35XX series, RG40XX, Powkiddy, RGB30, etc.)
- A legally purchased copy of *WitchWay* (available DRM-free on [itch.io](https://andrewgleeson.itch.io/witchway))

## Installation Instructions

### Option 1: PortMaster Autoinstall (Recommended)
1. Download [**`witchway.zip`**](https://github.com/XenoSlug/portmaster-witchway/releases/latest/download/witchway.zip) from the latest release.
2. Copy `witchway.zip` directly into your handheld SD card under `/roms/ports/autoinstall/` (or `/ports/autoinstall/`).
3. Boot PortMaster or your handheld to allow PortMaster to extract the files.
4. Place your purchased `WitchWay 1-12 WIN .zip` (or `WitchWay.exe`) into `/roms/ports/witchway/assets/`.
5. Launch **WitchWay** from the Ports menu! The game files will be prepared and configured automatically on first launch.

### Option 2: Pre-assemble on Mac / PC
1. Run the included `tools/patch_witchway.py` on your computer:
   ```bash
   python3 tools/patch_witchway.py /path/to/WitchWay.exe
   ```
2. It generates `game.port`.
3. Copy `WitchWay.sh`, the `witchway/` directory, and `game.port` to your SD card under `/roms/ports/witchway/`.

## Controls

| Handheld Button | Game Action |
| :--- | :--- |
| **D-Pad / Left Stick** | Move / Aim Wand |
| **A** | Jump / Confirm |
| **B** | Magic Wand (Levitate / Pull / Throw) |
| **X** | Interact / Inspect |
| **Y / L1** | View Rescued Bunnies / Inventory |
| **Start** | Pause Menu |
| **Select** | Back / Options |

## Credits
- **Original Game**: Andrew Gleeson, Henri Rochefort, Niilo Takalainen, Nathan Antony ([itch.io page](https://andrewgleeson.itch.io/witchway))
- **GMLoader**: SonicMastr, Johnny on Flame, and the PortMaster development team
- **Port Package**: [XenoSlug](https://github.com/XenoSlug)
