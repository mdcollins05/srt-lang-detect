#!/bin/bash
set -euo pipefail

# Run srt-lang-detect against any subtitle files included for sickbeard_mp4_automator

SCRIPT_PATH="/home/matt/srt-lang-detect" #EDIT ME!

# shellcheck disable=SC2001
files=$(echo "${MH_FILES%%,*}" | sed 's/[]"[]//g')

for file in "${files%%.*}"* ; do
  if [[ $file == *srt ]];
  then
    ${SCRIPT_PATH}/srtlang-detect.py -r -q -s "${file}"
  fi
done
