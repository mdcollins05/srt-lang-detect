#!/bin/bash

##############################################################################
### NZBGET POST-PROCESSING SCRIPT                                          ###

# SRT Lang Detect post-process script.
#
# Detects the language in subtitles and optionally renames the SRT files.
#

##############################################################################
#### OPTIONS                                                               ###

# Path to directory that contains the srtlangdetect.py file
#
# No trailing slash
#SRTLANGDETECT_PATH=

# Script arguments
#SCRIPT_ARGS=-s -q

### NZBGET POST-PROCESSING SCRIPT                                          ###
##############################################################################

read -r -a script_args <<< "$NZBPO_SCRIPT_ARGS"

echo "Running post-process srt-lang-detect on files..."
"${NZBPO_SRTLANGDETECT_PATH}/srtlangdetect.py" -r "${script_args[@]}" "${NZBPP_DIRECTORY}"

# Exit good no matter what
exit 93
