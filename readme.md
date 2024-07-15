# SRTLangDetect

Automatically detect the language of the subtitles in a file and rename if necessary.

This script can also change from 2 to 3 letter language codes or back. It will also re-number subtitle files if possible. (See the `--two-letter` or `--three-letter` arguments).

Naming of the subtitles is based off of [Plex's guide for subtitle naming](https://support.plex.tv/articles/200471133-adding-local-subtitles-to-your-media/).

I've tried to be as flexible as possible in determining the parts of an existing subtitle file but I've mostly tested with files already renamed by Sonarr or Radarr, following [Trash Guides](https://trash-guides.info/) recommended naming for [Sonarr](https://trash-guides.info/Sonarr/Sonarr-recommended-naming-scheme/) and [Radarr](https://trash-guides.info/Radarr/Radarr-recommended-naming-scheme/). This script doesn't require the above naming schemes to be used but be aware that some formats may produce weird results when using this script.

## Installation

1. Clone the repo
2. Install dependencies (`pip3 install -r requirements.txt`)
3. Optionally, install a post-process script by copying it to the appropriate folder and editing the file (except for nzbget scripts)

## Manual usage

You can manually run `srtlangdetect.py` from the command line.

```
$ ./srtlangdetect.py --help
usage: srtlangdetect.py [-h] [--rename-files] [--keep-only KEEP_ONLY]
                        [--require-lang-confidence REQUIRE_LANG_CONFIDENCE] [--min-sdh-confidence MIN_SDH_CONFIDENCE]
                        [--max-sdh-confidence MAX_SDH_CONFIDENCE] [--reject-sdh-confidence REJECT_SDH_CONFIDENCE]
                        [--two-letter | --three-letter] [--summary] [--quiet | --verbose]
                        [srt ...]

Detect the language of subtitle(srt) file(s)

positional arguments:
  srt                   One or more subtitle files or directories to operate on

options:
  -h, --help            show this help message and exit
  --rename-files, -r    The default is to do a dry-run. You must specify this option to rename files!
  --keep-only KEEP_ONLY, -k KEEP_ONLY
                        One or more languages to only keep. If `--rename-files` is specified, this will delete any
                        subtitle files that don't match the languages specified!
  --require-lang-confidence REQUIRE_LANG_CONFIDENCE, -c REQUIRE_LANG_CONFIDENCE
                        Require a confidence percentage equal or higher than the provided value to delete or rename a
                        file based on language (default 50) (valid range 0-100)
  --min-sdh-confidence MIN_SDH_CONFIDENCE
                        Minimum SDH confidence to consider a file as SDH (default 5) (valid range 0-100)
  --max-sdh-confidence MAX_SDH_CONFIDENCE
                        Maximum SDH confidence to consider a file as SDH (default 85) (valid range 0-100)
  --reject-sdh-confidence REJECT_SDH_CONFIDENCE
                        Reject SDH confidence to remove SDH flag (default 1) (valid range 0-100)
  --two-letter, -2      Prefer 2 letter language code
  --three-letter, -3    Prefer 3 letter language code
  --summary, -s         Provide a summary of the changes
  --quiet, -q           Quiet output. Only errors will be printed on screen
  --verbose, -v         Verbose output. Lines that have been modified will be printed on screen
```

Please note, the default action is a dry-run! You _must_ specify `--rename-files` to rename the subtitle file(s).
