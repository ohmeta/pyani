#!/usr/bin/env python

import argparse
import logging
import logging.handlers
import time
import os
import sys
from pyani import (
    anim,
    pyani_files
)
from pyani import __version__ as VERSION
from pyani.pyani_config import ALIGNDIR


def main():
    parser = argparse.ArgumentParser('parser pyani nucmer output')
    parser.add_argument(
        '-o',
        '--outdir',
        dest="outdirname",
        action='store',
        default=None,
        required=True,
        help='Output directory (required)'
    )
    parser.add_argument(
        '-i',
        '--indir',
        dest='indirname',
        action='store',
        default=None,
        required=True,
        help='Iuput directory name (required)'
    )
    parser.add_argument(
        '-l',
        '--logfile',
        dest='logfile',
        action='store',
        default=None,
        help='Lofile location'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        dest='verbose',
        action='store_true',
        default=False,
        help='Give verbose output'
    )
    args = parser.parse_args()

    logger = logging.getLogger("pyani_wrapper.py: %s" % time.asctime())
    t0 = time.time()
    logger.setLevel(logging.DEBUG)
    err_handler = logging.StreamHandler(sys.stderr)
    err_formatter = logging.Formatter("%(levelname)s: %(message)s")
    err_handler.setFormatter(err_formatter)

    if args.logfile is not None:
        try:
            logstream = open(args.logfile, 'w')
            err_handler_file = logging.StreamHandler(logstream)
            err_handler_file.setFormatter(err_formatter)
            err_handler_file.setLevel(logging.INFO)
            logger.addHandler(err_handler_file)
        except:
            logger.error("Could not open %s for logging", args.logfile)
            sys.exit(1)

    if args.verbose:
        err_handler.setLevel(logging.INFO)
    else:
        err_handler.setLevel(logging.WARNING)
    logger.addHandler(err_handler)

    logger.info("pyani version: %s", VERSION)
    logger.info(args)
    logger.info("command-line: %s", " ".join(sys.argv))

    if args.indirname is None:
        logger.error("No inpurt directory name (exiting)")
        sys.exit(1)
    logger.info("Input directory: %s", args.indirname)
    if args.outdirname is None:
        logger.error("No output directory name (exiting)")
        sys.exit(1)

    logger.info("Identifying FASTA files in %s", args.indirname)
    infiles = pyani_files.get_fasta_files(args.indirname)
    logger.info("Input files:\n\t%s", "\n\t".join(infiles))

    logger.info("Processing input sequence lengths")
    org_lengths = pyani_files.get_sequence_lengths(infiles)
    logger.info(
        "Sequence lengths:\n"
        + os.linesep.join(
            ["\t%s: %d" % (k, v) for k, v in list(org_lengths.items())]
        )
    )
    deltadir = os.path.join(args.outdirname, ALIGNDIR["ANIm"])
    logger.info("Processing NUCmer .delta files.")
    results = anim.process_deltadir(deltadir, org_lengths, logger=logger)

    for dfr, filestem in results.data:
        out_csv = os.path.join(args.outdirname, filestem) + ".tab"
        logger.info("\t%s", filestem)
        dfr.to_csv(out_csv, index=True, sep="\t")

    logger.info("Done: %s.", time.asctime())
    logger.info("Time taken: %.2fs", (time.time() - t0))


if __name__ == '__main__':
    main()
