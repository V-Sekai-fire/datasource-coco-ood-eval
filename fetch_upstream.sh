#!/usr/bin/env bash
# Fetch a large Google Drive file through the virus-scan interstitial.
# Drive serves a confirmation HTML page for big files; the real download needs
# the uuid/confirm pair carried from that page.
#
# This is how the upstream SDPose-OOD archives were obtained before they were filtered to the
# 523 licence-clean images and written as parquet. Kept because it is the only record of that
# route, and because the file ids are NOT recorded anywhere: they were passed by hand. Anyone
# re-fetching the full 5,000-image sets needs to find them again from SDPose-OOD.
#
# Note what re-fetching gets you. The full sets restyle all 5,000 val2017 images, and only 523
# are commercial-and-derivatives safe, so the remainder is not redistributable. See README.
set -euo pipefail
fid="$1"; out="$2"
page=$(curl -sL "https://drive.google.com/uc?export=download&id=${fid}")
uuid=$(printf '%s' "$page" | grep -oE 'name="uuid" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//')
if [ -z "$uuid" ]; then echo "no uuid token; file may be small or restricted" >&2; exit 1; fi
curl -L --progress-bar \
  "https://drive.usercontent.google.com/download?id=${fid}&export=download&confirm=t&uuid=${uuid}" \
  -o "$out"
