#!/usr/bin/env python3
"""Eggcyclopedia of Wood Tree Data Handling Module."""
import csv
import gzip
import json
import logging
import re


def load_tree_list(filename="trees_processed.json"):
    """Load list of trees that we are generating pages for.

    By default it loads the set of processed tree data but the
    filename may be specified to load the manual data from
    "trees.json".

    Arguments:
        filename (str) - filename of JSON file in local directory that
            has tree data.

    Returns dict that is indexed by species name.
    """
    with open(filename, "r", encoding="utf-8") as fh:
        trees = json.load(fh)
    logging.info("Read %d trees from %s", len(trees), filename)
    return trees


def write_tree_list(trees, filename="trees_processed.json"):
    """Write JSON file of all trees with data added.

    Write in pretty-print format so that diffs show up nicely between
    git copies of the file.

    Arguments:
        trees (dict): tree data
        filename (str): name of file to write
    """
    print(f"Writing {filename}")
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(trees, fh, indent=2, sort_keys=True)


def lookup_common_names(trees, trees_processed):
    """Use USDA database to lookup the common names for all tress.

    Arguments:
        trees (dict): tree data with species name as key. This data is modified.
        trees_processed (dict): tree data that has previosly been processed. Used
            only to look up existing processed data.

    Will add common_name key to dict for each tree. If tress_processed is
    passed in then will data from there if present.
    """
    common_names = {}
    with gzip.open("usda_db_2024-12-02.csv.gz", "rt") as fh:
        for row in csv.reader(fh):
            # Ignore lines with secondary code
            if row[1] not in ("", "MADO4"):
                continue
            # Ignore lines not matching capitalized word (genus) then lowercase word (species)
            m = re.match(r"""([A-Z][a-z]+\s[a-z]+)\b""", row[2])
            if m:
                species = m.group(1)
                if species not in common_names:
                    common_name = row[3].capitalize()
                    common_names[species] = common_name
    # Now lookup all trees
    for species in trees:
        if species in trees_processed:
            trees[species] = trees_processed[species]
            continue
        if "common_name" in trees[species]:
            # Don"t do a lookup of the config already has a
            # common name defined
            continue
        if species in common_names:
            if common_names[species] == "":
                logging.warning("No common name for %s in USDA database", species)
            else:
                trees[species]["common_name"] = common_names[species]
        else:
            logging.warning("Species %s not found in USDA database", species)
