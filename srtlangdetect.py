#!/usr/bin/env python3

import argparse
import os
import sys

import charset_normalizer
import iso639


def main():
    args = parse_args()

    if len(args.srt) == 0:
        print("No subtitle files or directories specified.")
        return False

    stats = {"renamed_files": 0}

    for srt in args.srt:
        if os.path.isfile(srt):
            action_taken = lang_detect_srt(
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
                            args
                        )
                        if args.verbose or args.summary:
                            print()
        else:
            print("Subtitle file/path '{0}' doesn't exist".format(srt))


def lang_detect_srt(file, summary, dry_run, quiet, verbose, args):
    if dry_run or verbose:
        print("Parsing '{0}'...".format(file))

    try:
        charset_matches = charset_normalizer.from_path(file)
    except OSError:
        print()
        print("Couldn't open file '{0}'".format(file))
        return False

    is_file_empty = len(charset_matches) == 1 and len(charset_matches[0].raw) == 0
    if is_file_empty:
        if verbose or summary:
            print("No subtitles found in {0}".format(file))
        return True

    file_language, forced_subs, numbered_file = get_filename_language(file)
    sub_detection_results = parse_charset_matches(charset_matches)

    if verbose or summary:
        file_language_long = to_lang_name(file_language)
        if not file_language_long:
            file_language_long = file_language

        if verbose:
            if forced_subs:
                print("Filename identified as: {0} (Forced)".format(file_language_long))
            else:
                print("Filename identified as: {0}".format(file_language_long))

            print("Subtitles identified as:")
            detect_langs_pretty(sub_detection_results)

    new_lang_name = sub_detection_results[0]["lang_name"]
    new_language_confidence = sub_detection_results[0]["confidence"]

    # Commented out because this doesn't do whatever I'd hoped it would do and instead ignores the detected language :facepalm:
    ## Try not to change the language in the filename if we can avoid it
    #if file_language != "Unknown":
    #    new_language = file_language

    if new_lang_name == "Unknown":
        if verbose or summary:
            print("Cannot detect language of the subtitles in {0}".format(file))
        return True

    if args.three_letter:
        new_language = to_3_letter_lang(new_lang_name)
    else:
        new_language = to_2_letter_lang(new_lang_name)

    new_filename = get_new_filename(
        file, new_language, file_language, forced_subs, numbered_file, verbose
    )

    if args.keep_only:
        keep_langs = []
        for lang in args.keep_only:
            if args.three_letter:
                l = to_3_letter_lang(lang.lower())
            else:
                l = to_2_letter_lang(lang.lower())

            if l: # Weed out invalid languages passed in
                keep_langs.append(l)

        if new_language not in keep_langs:
            if int(new_language_confidence) >= args.require_confidence:
                if dry_run:
                    if verbose:
                        print(
                            "Confidence of {0} equal or higher than required value to delete ({1})".format(
                                int(new_language_confidence), args.require_confidence
                            )
                        )
                    print(
                        "Would delete file '{0}'".format(new_filename)
                    )
                if not dry_run:
                    os.remove(file) # We haven't yet renamed, so remove the old file
                    if verbose or summary:
                        print(
                            "Deleted file '{0}'".format(file)
                        )

                return True

    if new_filename == file:
        if verbose or summary:
            print("No changes neccessary to {0}".format(file))
        return True

    if int(new_language_confidence) >= args.require_confidence:
        if dry_run:
            if verbose:
                print(
                    "Confidence of {0} equal or higher than required value to rename ({1})".format(
                        int(new_language_confidence), args.require_confidence
                    )
                )
            print(
                "Would rename '{0}' to '{1}'".format(
                    file, new_filename
                )
            )
        if not dry_run:
            os.rename(file, new_filename)
            if verbose or summary:
                print(
                    "Renamed '{0}' to '{1}'".format(
                        file, new_filename
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
    argsparser.add_argument(
        "--require-confidence",
        "-c",
        default=50,
        type=check_valid_percentage,
        help="Require a confidence percentage equal or higher than the provided value to delete or rename a file (default 50) (valid range 1-100)",
    )
    two_three_group = argsparser.add_mutually_exclusive_group()
    two_three_group.add_argument(
        "--two-letter", "-2", action="store_true", help="Prefer 2 letter language code"
    )
    two_three_group.add_argument(
        "--three-letter", "-3", action="store_true", help="Prefer 3 letter language code"
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
    if 1 <= ivalue <= 100:
        raise argparse.ArgumentTypeError("{0} is an invalid value".format(value))
    return ivalue


def get_filename_language(full_path):
    filename = os.path.basename(full_path).split(".")

    forced = False
    numbered = False
    sub_lang = filename[-2].lower()

    if sub_lang == "forced":
        forced = True
        sub_lang = filename[-3].lower()
        if sub_lang.isnumeric():
            numbered = True
            sub_lang = filename[-4].lower()
    elif sub_lang.isnumeric():
        numbered = True
        sub_lang = filename[-3].lower()

    if len(sub_lang) == 2 or len(sub_lang) == 3:
        if not iso639.is_valid639_1(sub_lang) and not iso639.is_valid639_2(sub_lang):
            sub_lang = "Unknown"
    else:
        sub_lang = "Unknown"

    return (sub_lang, forced, numbered)


def get_new_filename(full_path, language, file_language, forced, numbered, verbose):
    # Our file output should look like:
    # showormovietitle.(count).(lang).(forced).srt
    # count and forced may or may not be included as needed
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path).split(".")

    index = -3

    if not forced:
        index = -2
        if numbered:
            del filename[-2] #Remove the number from the filename
    else:
        if numbered:
            del filename[-3]

    if file_language != language:
        if file_language == "Unknown":
            filename.insert(index+1 , language)
            adjusted_for_unknown = True
        else:
            filename[index] = language

    # We do not want to overwrite any existing files, so check if a file exists on disk with the proposed name
    # and increment if it already does
    i = 0

    while True:
        if i == 0:
            index -= 1
            if len(filename[index]) == 1 and filename[index].isdigit():
                del filename[index]
        elif i == 1:
            filename.insert(index+1, str(i))
        elif i >= 2:
            filename[index] = str(i)

        new_filename = os.path.join(directory, ".".join(filename))

        if full_path == new_filename:
            break

        if not os.path.exists(new_filename):
            if verbose:
                print("{0} does not exist on disk".format(os.path.basename(new_filename)))
            break
        else:
            if verbose:
                print("{0} already exists".format(os.path.basename(new_filename)))
            i += 1

    return os.path.join(directory, ".".join(filename))


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


def parse_charset_matches(charset_matches):
    results = []
    for match in charset_matches:
        lang_name = match.language
        confidence = charset_normalizer.detect(match.raw)["confidence"]
        confidence_percent = round(float(confidence) * 100, 2)
        results.append({"lang_name": lang_name, "confidence": confidence_percent})

    return results


def detect_langs_pretty(results):
    for result in results:
        print("{0}: {1}%".format(result["lang_name"], result["confidence"]))


if __name__ == "__main__":
    sys.exit(main())
