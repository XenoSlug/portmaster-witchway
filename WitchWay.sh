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
for cat_dir in "/mnt/mmc/MUOS/info/catalogue" "/mnt/sdcard/MUOS/info/catalogue"; do
    if [ -d "$cat_dir" ]; then
        for pdir in "Ports" "PORTS" "ports"; do
            mkdir -p "$cat_dir/$pdir/box" "$cat_dir/$pdir/preview" 2>/dev/null
            cp -f "$GAMEDIR/cover.png" "$cat_dir/$pdir/box/WitchWay.png" 2>/dev/null
            cp -f "$GAMEDIR/cover.png" "$cat_dir/$pdir/preview/WitchWay.png" 2>/dev/null
        done
    fi
done

$ESUDO chmod +x "$GAMEDIR/gmloadernext.aarch64" 2>/dev/null || true
$ESUDO chmod +x "$GAMEDIR/tools/patchscript" 2>/dev/null || true
$ESUDO chmod +x "$GAMEDIR/tools/splash" 2>/dev/null || true

export LD_LIBRARY_PATH="$GAMEDIR/lib/arm64-v8a:$GAMEDIR/lib:$GAMEDIR/libs:$LD_LIBRARY_PATH"
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

# Display loading splash
if [ -f "$GAMEDIR/tools/splash" ] && [ -f "$GAMEDIR/splash.png" ]; then
    $ESUDO "$GAMEDIR/tools/splash" "$GAMEDIR/splash.png" 4000 &
fi

# Launch game with gptokeyb
$GPTOKEYB "gmloadernext.aarch64" -c "$GAMEDIR/witchway.gptk" &
pm_platform_helper "$GAMEDIR/gmloadernext.aarch64" >/dev/null

$GAMEDIR/gmloadernext.aarch64 -c gmloader.json

# Cleanup
$ESUDO kill -9 $(pidof gptokeyb) 2>/dev/null || true
pm_finish
