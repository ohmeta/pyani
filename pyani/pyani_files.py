# Copyright 2013-2017, The James Hutton Insitute
# Author: Leighton Pritchard
#
# This code is part of the pyani package, and is governed by its licence.
# Please see the LICENSE file that should have been included as part of
# this package.

"""Code to help handle files for average nucleotide identity calculations."""

import os

from Bio import SeqIO


# Get a list of FASTA files from the input directory
def get_fasta_files(dirname, recurse=False):
    """Returns a list of FASTA files in the passed directory

    - dirname - path to input directory
    - recurse - if True, recurse into subdirectories
    """
    infiles = get_input_files(
        dirname, ".fasta", ".fas", ".fa", ".fna", ".fsa_nt", recurse=recurse
    )
    return infiles


# Get list of FASTA files in a directory
def get_input_files(dirname, *ext, recurse=False):
    """Returns files in passed directory, filtered by extension.

    - dirname - path to input directory
    - recurse - if True, recurse into subdirectories
    - *ext - list of arguments describing permitted file extensions
    """
    files = []
    if recurse:
        for root, dirnames, filenames in os.walk(dirname):
            print([os.path.join(root, _) for _ in filenames])
            files.extend(
                [
                    os.path.join(root, _)
                    for _ in filenames
                    if os.path.splitext(_)[-1] in ext
                ]
            )
    else:
        filelist = [f for f in os.listdir(dirname) if os.path.splitext(f)[-1] in ext]
        files = [os.path.join(dirname, f) for f in filelist]
    return files


# Get lengths of input sequences
def get_sequence_lengths(fastafilenames):
    """Returns dictionary of sequence lengths, keyed by organism.

    Biopython's SeqIO module is used to parse all sequences in the FASTA
    file corresponding to each organism, and the total base count in each
    is obtained.

    NOTE: ambiguity symbols are not discounted.
    """
    tot_lengths = {}
    for fn in fastafilenames:
        tot_lengths[os.path.splitext(os.path.split(fn)[-1])[0]] = sum(
            [len(s) for s in SeqIO.parse(fn, "fasta")]
        )
    return tot_lengths
