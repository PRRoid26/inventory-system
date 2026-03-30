#!/bin/bash
set -e

APP_NAME="FugroInventory"
VERSION="1.0.0"

echo "==> Installing PyInstaller..."
pip install pyinstaller --break-system-packages 2>/dev/null || pip install pyinstaller

echo "==> Building binary with PyInstaller..."
pyinstaller FugroInventory.spec --distpath dist --workpath build --noconfirm

echo "==> Creating AppDir structure..."
APPDIR="$APP_NAME.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy binary
cp dist/$APP_NAME "$APPDIR/usr/bin/$APP_NAME"

# Desktop entry
cat > "$APPDIR/$APP_NAME.desktop" << DESKTOP
[Desktop Entry]
Name=Fugro Inventory
Exec=FugroInventory
Icon=fugroinventory
Type=Application
Categories=Utility;
DESKTOP

cp "$APPDIR/$APP_NAME.desktop" "$APPDIR/usr/share/applications/"

# Placeholder icon (replace with actual .png if you have one)
# Requires imagemagick: sudo apt install imagemagick
if command -v convert &>/dev/null; then
    convert -size 256x256 xc:#0055A4 -fill white \
        -font DejaVu-Sans-Bold -pointsize 48 \
        -gravity center -annotate 0 "FI" \
        "$APPDIR/usr/share/icons/hicolor/256x256/apps/fugroinventory.png"
    cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/fugroinventory.png" "$APPDIR/fugroinventory.png"
else
    # Create a minimal 1x1 PNG as placeholder
    printf '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82' \
        > "$APPDIR/fugroinventory.png"
fi

# AppRun entrypoint
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "$HERE/usr/bin/FugroInventory" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

echo "==> Downloading appimagetool..."
wget -q -O appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
chmod +x appimagetool

echo "==> Building AppImage..."
ARCH=x86_64 ./appimagetool "$APPDIR" "${APP_NAME}-${VERSION}-x86_64.AppImage"

echo ""
echo "✅ Done: ${APP_NAME}-${VERSION}-x86_64.AppImage"
