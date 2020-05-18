#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Run srt-lang-detect against any subtitle files included with video file for Radarr

# shellcheck disable=SC2154
DESTINATION=${radarr_movie_path}
SCRIPT_PATH="/home/matt/srt-lang-detect" #EDIT ME!

${SCRIPT_PATH}/srtlangdetect.py -r -s -q "${DESTINATION}"
