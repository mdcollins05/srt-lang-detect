#!/usr/bin/env python3

import argparse
import os
import sys
import re

import chardet
import iso639
import srt

from langid.langid import LanguageIdentifier, model

langid = LanguageIdentifier.from_modelstring(model, norm_probs=True)


def main():
    args = parse_args()

    if len(args.srt) == 0:
        print("No subtitle files or directories specified.")
        return False

    stats = {"renamed_files": 0}

    for srt in args.srt:
        if os.path.isfile(srt):
            lang_detect_srt(
                srt, args.summary, args.dry_run, args.quiet, args.verbose, args
            )
        elif os.path.isdir(srt):
            for root, dirs, files in os.walk(srt):
                for file in files:
                    if file.endswith(".srt"):
                        lang_detect_srt(
                            os.path.join(root, file),
                            args.summary,
                            args.dry_run,
                            args.quiet,
                            args.verbose,
                            args,
                        )
                        if args.verbose or args.summary:
                            print()
        else:
            print("Subtitle file/path '{0}' doesn't exist".format(srt))

# This function is way too long but it stays for now.
def lang_detect_srt(file, summary, dry_run, quiet, verbose, args):
    if dry_run or verbose:
        print("Parsing '{0}'...".format(file))

    subtitles_raw = ""
    try:
        # Try to read the file using UTF-8 encoding
        with open(file, "r", encoding="utf-8") as filehandler:
            subtitles_raw = filehandler.read()
    except:
        # If default encoding fails, try to detect actual encoding
        raw_bytes = b""
        with open(file, "rb") as filehandler:
            raw_bytes = filehandler.read()
        encoding = chardet.detect(raw_bytes)["encoding"]
        try:
            with open(file, "r", encoding=encoding) as filehandler:
                subtitles_raw = filehandler.read()
        except:
            print()
            print("Couldn't open file '{0}'".format(file))
            return False

    subtitles_objs = []
    try:
        subtitles_objs = list(srt.parse(subtitles_raw))
    except:
        print()
        print("Trouble parsing subtitles in '{0}'".format(file))
        return False

    if len(subtitles_objs) == 0:
        if verbose or summary:
            print("No subtitles found in {0}".format(file))
        return True

    subtitles = [sub.content for sub in subtitles_objs]
    subtitles_text = "\n\n".join(subtitles)

    file_language, special_subs, forced_subs = get_filename_language(file)

    sdh_confidence = percent_sdh(subtitles_text) * 100

    classification = langid.classify(subtitles_text)
    new_lang_code = classification[0]
    new_lang_name = to_lang_name(classification[0])
    new_language_confidence = classification[1] * 100

    if verbose or summary:
        file_language_long = to_lang_name(file_language)
        if not file_language_long:
            file_language_long = file_language

        if verbose:
            message = "Filename identified as: {0}".format(file_language_long)
            if special_subs != "":
                message +=" ({0})".format(special_subs)
            if forced_subs:
                message +=" (Forced)"
            print(message)

            print("Subtitles identified as:")
            detect_langs_pretty(
                [{"lang_name": new_lang_name, "confidence": new_language_confidence}]
            )

            print("SDH confidence: {0}%".format(sdh_confidence))

    if new_lang_name == "Unknown":
        if verbose or summary:
            print("Cannot detect language of the subtitles in {0}".format(file))

        # Set a language code so we can continue if we want to keep only certain languages
        if args.three_letter:
            new_language = "unk"
        else:
            new_language = "un"
    else:
        if args.three_letter:
            new_language = to_3_letter_lang(new_lang_code)
        else:
            new_language = to_2_letter_lang(new_lang_code)

    if sdh_confidence >= args.min_sdh_confidence and sdh_confidence <= args.max_sdh_confidence and special_subs != "sdh":
        if verbose:
            print("Marking file as SDH")
            special_subs = "sdh"

    if sdh_confidence <= args.reject_sdh_confidence and special_subs == "sdh":
        if verbose:
            print("Removing SDH flag")
            special_subs = ""

    new_filename = get_new_filename(
        file, new_language, file_language, special_subs, forced_subs, verbose
    )

    if args.keep_only:
        keep_langs = []
        for lang in args.keep_only:
            if args.three_letter:
                l = to_3_letter_lang(lang.lower())
            else:
                l = to_2_letter_lang(lang.lower())

            if l:  # Weed out invalid languages passed in
                keep_langs.append(l)

        if new_language not in keep_langs:
            if int(new_language_confidence) >= args.require_lang_confidence:
                if dry_run:
                    if verbose:
                        print(
                            "Confidence of {0} equal or higher than required value to delete ({1})".format(
                                int(new_language_confidence), args.require_lang_confidence
                            )
                        )
                    print("Would delete file '{0}'".format(new_filename))
                if not dry_run:
                    os.remove(file)  # We haven't yet renamed, so remove the old file
                    if verbose or summary:
                        print("Deleted file '{0}'".format(file))

                return True

    if new_filename == file:
        if verbose or summary:
            print("No changes neccessary to {0}".format(file))
        return True

    if int(new_language_confidence) >= args.require_lang_confidence:
        if dry_run:
            if verbose:
                print(
                    "Confidence of {0} equal or higher than required value to rename ({1})".format(
                        int(new_language_confidence), args.require_lang_confidence
                    )
                )
            print("Would rename '{0}' to '{1}'".format(file, new_filename))
        if not dry_run:
            if new_lang_name != "Unknown":
                os.rename(file, new_filename)
                if verbose or summary:
                    print("Renamed '{0}' to '{1}'".format(file, new_filename))
            else:
                if verbose or summary:
                    print(
                        "Would not rename '{0}' because the language is unknown".format(
                            file
                        )
                    )

    return True


def parse_args():
    argsparser = argparse.ArgumentParser(
        description="Detect the language of subtitle(srt) file(s)"
    )
    argsparser.add_argument(
        "srt", nargs="*", help="One or more subtitle files or directories to operate on"
    )
    argsparser.add_argument(
        "--rename-files",
        "-r",
        action="store_false",
        dest="dry_run",
        help="The default is to do a dry-run. You must specify this option to rename files!",
    )
    argsparser.add_argument(
        "--keep-only",
        "-k",
        action="append",
        help="One or more languages to only keep. If `--rename-files` is specified, this will delete any subtitle files that don't match the languages specified!",
    )
    # Not implemented yet
    # argsparser.add_argument(
    #     "--keep-only-one",
    #     action="append",
    #     help="Keep only one file of each language specified in `--keep-only`. If `--rename-files` is specified, this will delete any additional files beyond the first one!",
    # )
    argsparser.add_argument(
        "--require-lang-confidence",
        "-c",
        default=50,
        type=check_valid_percentage,
        help="Require a confidence percentage equal or higher than the provided value to delete or rename a file based on language (default 50) (valid range 0-100)",
    )
    argsparser.add_argument(
        "--min-sdh-confidence",
        default=5,
        type=check_valid_percentage,
        help="Minimum SDH confidence to consider a file as SDH (default 5) (valid range 0-100)",
    )
    argsparser.add_argument(
        "--max-sdh-confidence",
        default=85,
        type=check_valid_percentage,
        help="Maximum SDH confidence to consider a file as SDH (default 85) (valid range 0-100)",
    )
    argsparser.add_argument(
        "--reject-sdh-confidence",
        default=1,
        type=check_valid_percentage,
        help="Reject SDH confidence to remove SDH flag (default 1) (valid range 0-100)",
    )
    two_three_group = argsparser.add_mutually_exclusive_group()
    two_three_group.add_argument(
        "--two-letter", "-2", action="store_true", help="Prefer 2 letter language code"
    )
    two_three_group.add_argument(
        "--three-letter",
        "-3",
        action="store_true",
        help="Prefer 3 letter language code",
    )
    argsparser.add_argument(
        "--summary", "-s", action="store_true", help="Provide a summary of the changes"
    )
    v_q_group = argsparser.add_mutually_exclusive_group()
    v_q_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet output. Only errors will be printed on screen",
    )
    v_q_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output. Lines that have been modified will be printed on screen",
    )

    return argsparser.parse_args()


def check_valid_percentage(value):
    ivalue = int(value)
    if 0 <= ivalue <= 100:
        raise argparse.ArgumentTypeError("{0} is an invalid value".format(value))
    return ivalue


def get_filename_language(full_path):
    # Split the filename by periods and reverse it so we can check the last parts first
    filename = os.path.basename(full_path).split(".")[::-1]

    forced = False
    special = ""
    sub_lang = "Unknown"

    # Check each part of the filename for the language, forced, sdh, or numbering.
    # Break out of the loop if none of those are found, as we assume everything else is
    # part of the title
    for part in filename:
        if part.lower() == "srt":
            continue
        if part.lower() == "forced":
            forced = True
            continue
        elif part.lower() == "cc":
            special = "cc"
            continue
        elif part.lower() == "sdh":
            special = "sdh"
            continue
        elif len(part) == 2 or len(part) == 3:
            sub_lang = part.lower()
            continue
        elif re.match(r"\d+", part):
            continue
        else:
            break

    if len(sub_lang) == 2 or len(sub_lang) == 3:
        if not iso639.is_valid639_1(sub_lang) and not iso639.is_valid639_2(sub_lang):
            sub_lang = "Unknown"
    else:
        sub_lang = "Unknown"

    return (sub_lang, special, forced)


def get_new_filename(full_path, language, file_language, special, forced, verbose):
    # Our file output should look like:
    # showormovietitle.(count).(lang).(special).(forced).srt
    # count, special and forced may or may not be included as needed
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path).split(".")[::-1]

    # Remove all the parts we will reconstruct
    # Use a copy of the list, because modifying it while iterating will cause issues
    for part in filename[:]:
        if part.lower() == "srt":
            filename.remove(part)
        elif part.lower() == "forced":
            filename.remove(part)
        elif re.match(r"^\d{1,2}$", part):
            # Remove if 1 or 2 digits long, as it may be the count of unique subtitles
            # Longer numbers are assumed to be part of the title or otherwise should be kept
            filename.remove(part)
        elif part.lower() == "sdh":
            filename.remove(part)
        elif part.lower() == "cc":
            filename.remove(part)
        elif part == file_language:
            filename.remove(part)
        elif part == language:
            filename.remove(part)
        else:
            # We want to be as careful as possible, so once we reach parts we don't recognize, we bail
            break

    # Flip it and reverse it
    filename = filename[::-1]

    # We do not want to overwrite any existing files, so check if a file exists on disk with the proposed name
    # and increment if it already does
    i = 0

    while True:
        new_filename = filename.copy()

        if i >= 1:
            new_filename.append(str(i))
        
        new_filename.append(language)
        
        if special:
            new_filename.append(special)

        if forced:
            new_filename.append("forced")
        
        new_filename.append("srt")

        new_filename = os.path.join(directory, ".".join(new_filename))

        if full_path == new_filename:
            break

        if not os.path.exists(new_filename):
            if verbose:
                print(
                    "  {0} does not exist on disk".format(os.path.basename(new_filename))
                )
            break
        else:
            if verbose:
                print("  {0} already exists".format(os.path.basename(new_filename)))
            i += 1

    return new_filename

def percent_sdh(input_text):
    sdh_regex = re.compile(r"(\[.*\]|<.*>|\(.*\))")

    # Remove empty lines
    input_text = re.sub(r"\n\s*\n", "\n", input_text)

    sdh_count = 0
    total_count = 0

    for line in input_text.split("\n"):
        total_count += 1
        if sdh_regex.match(line):
            sdh_count += 1

    return round(sdh_count / total_count, 2)

def to_2_letter_lang(lang):
    try:
        return iso639.to_iso639_1(lang)
    except iso639.NonExistentLanguageError:
        return False


def to_3_letter_lang(lang):
    try:
        return iso639.to_iso639_2(lang)
    except iso639.NonExistentLanguageError:
        return False


def to_lang_name(lang):
    try:
        return iso639.to_name(lang)
    except iso639.NonExistentLanguageError:
        return False


def detect_langs_pretty(results):
    for result in results:
        print("  {0}: {1}%".format(result["lang_name"], result["confidence"]))


if __name__ == "__main__":
    sys.exit(main())
