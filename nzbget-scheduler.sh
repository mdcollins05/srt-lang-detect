#!/bin/bash

##############################################################################
### NZBGET SCHEDULER SCRIPT                                                ###

# SRT Lang Detect scheduler script.
#
# Detects the language in subtitles and optionally renames the SRT files.
#

##############################################################################
### OPTIONS                                                                ###

# Path to directory that contains the srtlangdetect.py file
#
# No trailing slash
#SRTLANGDETECT_PATH=

# Script arguments
#
#SCRIPT_ARGS=-s -q

# Directories to scan
#
# Space seperated directories to scan for SRT files to process
#
#SCAN_DIRECTORIES=/data/media/TV /data/media/Movies

# Maximum age
#
# Maximum age of SRT files to process in minutes
#
#MAX_AGE=28800

### NZBGET SCHEDULER SCRIPT                                                ###
##############################################################################

read -r -a script_args <<< "$NZBPO_SCRIPT_ARGS"
read -r -a scan_directories <<< "$NZBPO_SCAN_DIRECTORIES"

echo "Running scheduled srt-lang-detect on files..."
find "${scan_directories[@]}" -name \*.srt -cmin "-${NZBPO_MAX_AGE}" -exec "${NZBPO_SRTLANGDETECT_PATH}/srtlangdetect.py" -r "${script_args[@]}" "{}" \;

# Exit good no matter what
exit 93
