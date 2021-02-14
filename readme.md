# SRTLangDetect

Automatically detect the language of the subtitles in a file and rename if necessary.

This script can also change from 2 to 3 letter language codes or back. It will also re-number subtitle files if possible. (See the `--two-letter` or `--three-letter` arguments)

## Installation

1. Clone the repo
2. Install dependencies (`pip3 install -r requirements.txt`)
3. Optionally, install a post-process script by copying it to the appropriate folder and editing the file (except for nzbget scripts)

## Manual usage

You can manually run `srtlangdetect.py` from the command line.

```
$ ./srtlangdetect.py --help
usage: srtlangdetect.py [-h] [--rename-files] [--keep-only KEEP_ONLY]
                        [--require-confidence REQUIRE_CONFIDENCE]
                        [--two-letter | --three-letter] [--summary]
                        [--quiet | --verbose]
                        [srt [srt ...]]

Detect the language of subtitle(srt) file(s)

positional arguments:
  srt                   One or more subtitle files or directories to operate
                        on

optional arguments:
  -h, --help            show this help message and exit
  --rename-files, -r    The default is to do a dry-run. You must specify this
                        option to rename files!
  --keep-only KEEP_ONLY, -k KEEP_ONLY
                        One or more languages to only keep. If `--rename-
                        files` is specified, this will delete any subtitle
                        files that don't match the languages specified!
  --require-confidence REQUIRE_CONFIDENCE, -c REQUIRE_CONFIDENCE
                        Require a confidence percentage equal or higher than
                        the provided value to delete or rename a file (default
                        50) (valid range 1-100)
  --two-letter, -2      Prefer 2 letter language code
  --three-letter, -3    Prefer 3 letter language code
  --summary, -s         Provide a summary of the changes
  --quiet, -q           Quiet output. Only errors will be printed on screen
  --verbose, -v         Verbose output. Lines that have been modified will be
                        printed on screen
```

Please note, the default action is a dry-run! You _must_ specify `--rename-files` to rename the subtitle file(s).
