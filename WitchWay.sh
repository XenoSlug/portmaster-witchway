#!/bin/bash

XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

source "$controlfolder/control.txt"
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
get_controls

GAMEDIR="/$directory/ports/witchway"
cd "$GAMEDIR"
> "$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1

# Auto-copy boxart to muOS catalogue if running on muOS
for muos_box in "/mnt/mmc/MUOS/info/catalogue/Ports/box" "/mnt/sdcard/MUOS/info/catalogue/Ports/box"; do
    if [ -d "$muos_box" ] && [ ! -f "$muos_box/WitchWay.png" ]; then
        cp "$GAMEDIR/cover.png" "$muos_box/WitchWay.png" 2>/dev/null
    fi
done

$ESUDO chmod +x "$GAMEDIR/tools/patchscript"

export LD_LIBRARY_PATH="$GAMEDIR/libs:$LD_LIBRARY_PATH"
export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"
export ESUDO
export controlfolder
export DEVICE_ARCH

# Check if game needs setup / patching
if [ ! -f "$GAMEDIR/game.port" ]; then
    if [ -f "$controlfolder/utils/patcher.txt" ]; then
        export PATCHER_FILE="$GAMEDIR/tools/patchscript"
        export PATCHER_GAME="WitchWay"
        export PATCHER_TIME="1 to 2 minutes"
        source "$controlfolder/utils/patcher.txt"
        $ESUDO kill -9 $(pidof gptokeyb) 2>/dev/null
    else
        echo "Running patchscript directly..."
        bash "$GAMEDIR/tools/patchscript"
    fi
fi

if [ ! -f "$GAMEDIR/game.port" ]; then
    echo "Error: game.port was not created! Please check assets in $GAMEDIR/assets"
    pm_message "WitchWay assets missing! Place WitchWay game files into ports/witchway/assets/"
    sleep 5
    exit 1
fi

# Load gmtoolkit runtime if gmloadernext is not local
if [ ! -f "$GAMEDIR/gmloadernext.aarch64" ] && [ -f "$controlfolder/libs/gmtoolkit.squashfs" ]; then
    TOOLKIT="$HOME/gmtoolkit"
    $ESUDO mkdir -p "$TOOLKIT"
    $ESUDO umount "$TOOLKIT" 2>/dev/null || true
    $ESUDO mount "$controlfolder/libs/gmtoolkit.squashfs" "$TOOLKIT"
    GMLOADER_BIN="$TOOLKIT/gmloadernext.aarch64"
    export LD_LIBRARY_PATH="$TOOLKIT/libs:$LD_LIBRARY_PATH"
elif [ -f "$GAMEDIR/gmloadernext.aarch64" ]; then
    $ESUDO chmod +x "$GAMEDIR/gmloadernext.aarch64"
    GMLOADER_BIN="$GAMEDIR/gmloadernext.aarch64"
elif [ -f "$controlfolder/harbourmaster" ]; then
    # Attempt to fetch gmtoolkit runtime if missing
    $controlfolder/harbourmaster --quiet --no-check runtime_check "gmtoolkit.squashfs"
    TOOLKIT="$HOME/gmtoolkit"
    $ESUDO mkdir -p "$TOOLKIT"
    $ESUDO mount "$controlfolder/libs/gmtoolkit.squashfs" "$TOOLKIT"
    GMLOADER_BIN="$TOOLKIT/gmloadernext.aarch64"
    export LD_LIBRARY_PATH="$TOOLKIT/libs:$LD_LIBRARY_PATH"
else
    GMLOADER_BIN="./gmloadernext.aarch64"
fi

# Launch game with gptokeyb
$GPTOKEYB "$(basename "$GMLOADER_BIN")" -c "$GAMEDIR/witchway.gptk" &
pm_platform_helper "$GMLOADER_BIN" >/dev/null

$GMLOADER_BIN -c gmloader.json

# Cleanup
[ -d "$HOME/gmtoolkit" ] && $ESUDO umount "$HOME/gmtoolkit" 2>/dev/null || true
pm_finish
