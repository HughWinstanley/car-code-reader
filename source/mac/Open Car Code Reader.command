#!/bin/bash
# One-click opener for Macs other than the one it was built on.
# A downloaded app carries a "quarantine" flag; because this app isn't notarized by Apple,
# macOS can refuse to launch it (it just bounces in the Dock with no prompt). This script
# installs the app to /Applications if needed, clears that flag, and opens it. You only run it once.

set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Car Code Reader.app"
DEST="/Applications/$APP_NAME"
SRC="$HERE/$APP_NAME"

if [ ! -d "$DEST" ]; then
  if [ -d "$SRC" ]; then
    echo "Installing Car Code Reader to your Applications folder..."
    /bin/cp -R "$SRC" /Applications/ || {
      echo
      echo "Couldn't copy to Applications automatically."
      echo "Drag 'Car Code Reader' onto the Applications folder yourself, then run this again."
      read -r -p "Press Return to close."
      exit 1
    }
  else
    echo "Put this file in the same folder as 'Car Code Reader.app' and run it again."
    read -r -p "Press Return to close."
    exit 1
  fi
fi

echo "Clearing the download flag so macOS will open it..."
/usr/bin/xattr -cr "$DEST" 2>/dev/null || true
echo "Opening Car Code Reader..."
/usr/bin/open "$DEST"
echo "Done. You can close this window."
