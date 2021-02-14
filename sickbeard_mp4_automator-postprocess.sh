#!/bin/bash
set -euo pipefail

# Run srt-lang-detect against any subtitle files included for sickbeard_mp4_automator

SCRIPT_PATH="/home/matt/srt-lang-detect" #EDIT ME!
SCRIPT_ARGS="-r -q -s -2 -k eng" #EDIT ME!

files="${SMA_FILES:=${MH_FILES:=[]}}" # Support old and new env variable from Sickbeard MP4 Automator

echo "${files}" | jq -c '.[]' | while read -r file; do
  file=$(sed -e 's/"//g' <<<"${file}")
  if [[ $file == *srt ]]; then
    ${SCRIPT_PATH}/srtlangdetect.py ${SCRIPT_ARGS} "${file}"
  fi
done
