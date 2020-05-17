#!/usr/bin/env python3

import argparse
import os.path
import sys

import iso639
import srt
from langdetect import detect_langs


def main():
    args = parse_args()

    if len(args.srt) == 0:
        print("No subtitle files or directories specified.")
        return False

    stats = {"renamed_files": 0}

    for srt in args.srt:
        if os.path.isfile(srt):
            action_taken = lang_detect_srt(srt, args.summary, args.dry_run, args.quiet, args.verbose)
        elif os.path.isdir(srt):
            for root, dirs, files in os.walk(srt):
                for file in files:
                    if file.endswith(".srt"):
                        pass
                        # lang_detect_srt(
                        #     os.path.join(root, file),
                        #     args.summary,
                        #     args.dry_run,
                        #     args.quiet,
                        #     args.verbose,
                        # )
        else:
            print("Subtitle file/path '{0}' doesn't exist".format(args.srt))


def lang_detect_srt(file, summary, dry_run, quiet, verbose):
    if dry_run or verbose or summary:
        print("Parsing '{0}'...".format(file))

    try:
        original_subtitles = None
        with open(file, "r", encoding="utf-8") as filehandler:
            original_subtitles = filehandler.read()
    except:
        print()
        print("Couldn't open file '{0}'".format(file))
        return False

    try:
        original_subtitles = list(srt.parse(original_subtitles))
    except:
        print()
        print("Trouble parsing subtitles in '{0}'".format(file))
        return False

    full_subtitle_text = ""

    for i in range(len(original_subtitles)):
        full_subtitle_text += original_subtitles[i].content

    file_language, forced_subs = get_filename_language(file)
    sub_detection_results = parse_detect_langs(detect_langs(full_subtitle_text))
    if verbose:
        file_language_long = to_lang_name(file_language)
        if not file_language_long:
            file_language_long = file_language

        if forced_subs:
            print("Filename identified as: {0} (Forced)".format(file_language_long))
        else:
            print("Filename identified as: {0}".format(file_language_long))

        print("Subtitles identified as:")
        detect_langs_pretty(sub_detection_results)

    new_language = sub_detection_results[0][0]

    if args.two_letter:
        new_language = to_2_letter_cc(new_language)
    elif args.three_letter:
        new_language = to_3_letter_cc(new_language)

    new_filename = get_new_filename(file, new_language, file_language, forced_subs)
    print(new_filename)
    # if sub_detection_results[0][0] >= args.require_confidence:
    #     # rename file
    #     pass

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
        "--require-confidence",
        "-c",
        default=50,
        type=check_valid_percentage,
        help="Require a confidence percentage equal or higher than the provided value to rename (default 50) (valid range 1-100)"
    )
    two_three_group = argsparser.add_mutually_exclusive_group()
    two_three_group.add_argument(
        "--two-letter", "-2", action="store_true", help="Prefer 2 letter country code"
    )
    two_three_group.add_argument(
        "--three-letter", "-3", action="store_true", help="Prefer 3 letter country code"
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
    sub_lang = filename[-2].lower()

    if sub_lang == "forced":
        forced = True
        sub_lang = filename[-3].lower()

    if len(sub_lang) == 2 or len(sub_lang) == 3:
        if not iso639.is_valid639_1(sub_lang) and not iso639.is_valid639_2(sub_lang):
            sub_lang = "Unknown"
    else:
        sub_lang = "Unknown"

    return (sub_lang, forced)


def get_new_filename(full_path, language, file_language, forced):
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path).split(".")

    adjusted_for_unknown = False

    if file_language != language:
        if forced:
            if file_language == "Unknown" and not adjusted_for_unknown:
                filename.insert(-2, language)
                adjusted_for_unknown = True
            else:
                filename[-3] = language
        else:
            if file_language == "Unknown" and not adjusted_for_unknown:
                filename.insert(-1, language)
                adjusted_for_unknown = True
            else:
                filename[-2] = language

    new_filename = os.path.join(directory, '.'.join(filename))

    # We do not want to overwrite any existing files, so increment by 1 until we find a filename not taken
    i = 0
    while True:
        if i == 1:
            if forced:
                filename.insert(-3, i)
            else:
                filename.insert(-2, i)
        elif i >= 2:
            if forced:
                filename[-4] = i
            else:
                filename[-3] = i
        if not os.path.exists(new_filename):
            break
        else:
            i += 1


    return os.path.join(directory, '.'.join(filename))


def to_2_letter_cc(cc):
    if len(cc) == 2:
        if iso639.is_valid639_1(cc):
            return cc

    if len(cc) == 3:
        if iso639.is_valid639_2(cc):
            return iso639.to_iso639_1(cc)

    return False


def to_3_letter_cc(cc):
    if len(cc) == 2:
        if iso639.is_valid639_1(cc):
            return iso639.to_iso639_2(cc)

    if len(cc) == 3:
        if iso639.is_valid639_2(cc):
            return cc

    return False


def to_lang_name(cc):
    if is_valid_cc(cc):
        return iso639.to_name(cc)
    else:
        return False


def is_valid_cc(cc):
    if len(cc) == 2:
        if iso639.is_valid639_1(cc):
            return True
    elif len(cc) == 3:
        if iso639.is_valid639_2(cc):
            return True
    else:
        return False


def parse_detect_langs(results):
    new_results = []
    for result in results:
        result = str(result).split(":")
        lang_name = to_2_letter_cc(result[0])
        confidence = round(float(result[1]) * 100, 2)
        new_results.append((lang_name, confidence))

    return new_results


def detect_langs_pretty(results):
    for result in results:
        lang_name = to_lang_name(result[0])
        confidence = result[1]
        print("{0}: {1}%".format(lang_name, confidence))


if __name__ == "__main__":
    sys.exit(main())
