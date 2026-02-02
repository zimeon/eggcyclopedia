#!/usr/bin/env python3
"""Eggcyclopedia of Wood Builder.

Open tree of life web APIs:
https://github.com/OpenTreeOfLife/germinator/wiki/Open-Tree-of-Life-Web-APIs

Python code:
https://opentree.readthedocs.io/en/latest/notebooks.html

Examples:
https://github.com/snacktavish/OpenTree_SSB2020/blob/master/notebooks/DEMO_OpenTree.ipynb
"""
import argparse
from contextlib import redirect_stdout
import csv
import gzip
import io
import json
import logging
import re

from opentree import OT


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Eggcyclopedia of Wood Builder.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--lookup", "-l", action="store_true",
                        help="run lookup on anything not already in processed")
    parser.add_argument("--lookup-all", "-L", action="store_true",
                        help="run lookup on raw data (don't use processed at all)")
    parser.add_argument("--tree", "-t", action="store_true",
                        help="generate tree")
    args = parser.parse_args()
    return args


def load_tree_list(filename='trees.json'):
    """Load list of trees that we are generating pages for.

    Returns dict that is indexed by species name.
    """
    with open(filename, 'r', encoding="utf-8") as fh:
        trees = json.load(fh)
    logging.info("Read %d trees from %s", len(trees), filename)
    return trees


def write_tree_list(trees, filename='trees_processed.json'):
    """Write JSON file of all trees with data added.

    Arguments:
        trees (dict): tree data
        filename (str): name of file to write
    """
    print(f"Writing {filename}")
    with open(filename, 'w', encoding="utf-8") as fh:
        json.dump(trees, fh)


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
    with gzip.open('usda_db_2024-12-02.csv.gz', 'rt') as fh:
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
            # Don't do a lookup of the config already has a
            # common name defined
            continue
        if species in common_names:
            if common_names[species] == "":
                logging.warning("No common name for %s in USDA database", species)
            else:
                trees[species]['common_name'] = common_names[species]
        else:
            logging.warning("Species %s not found in USDA database", species)


def lookup_ott_ids(trees):
    """Lookup Open Tree of Life Taxonomy ids.

    Open Tree of Life Taxonomy (OTT from now on).

    Arguments:
        trees (dict): tree data

    Adds data to the "ott_id" attribute for each species in the trees dict that
    does not already have the attribute.
    """
    for species in trees:
        if "ott_id" in trees[species]:
            continue
        if "skip" in trees[species]:
            # FIXME: How to handle crosses (e.g. Common lime)
            continue
        # Look it up
        try:
            m = OT.tnrs_match([species])
            id = m.response_dict['results'][0]['matches'][0]['taxon']['ott_id']
            print("ott_id for %s is %d" % (species, id))
            trees[species]["ott_id"] = id
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.warning("Failed lookup for %s (%s)", species, str(e))


def extract_ott_ids(trees):
    """Extract list of defined OTT ids.

    Arguments:
        trees (dict): tree data
    """
    ott_ids = []
    for species in trees:
        if "ott_id" in trees[species]:
            ott_ids.append(trees[species]["ott_id"])
    return ott_ids


def main():
    """CLI handler."""
    args = parse_args()

    if args.lookup or args.lookup_all:
        if args.lookup:
            trees_processed = load_tree_list(filename="trees_processed.json")
        else:
            trees_processed = {}  # don't use existing data
        trees = load_tree_list()
        lookup_common_names(trees, trees_processed)
        lookup_ott_ids(trees)
        if trees == trees_processed:
            print("No new data, not updating trees_processed.json")
        else:
            write_tree_list(trees)
    else:
        trees = load_tree_list(filename="trees_processed.json")

    if args.tree:
        ott_ids = extract_ott_ids(trees)
        # Get the synthetic tree from OpenTree
        output = OT.synth_induced_tree(ott_ids=ott_ids, label_format='name_and_id')
        # Get ASCII tree with labels "name (common name)"
        # FIXME - How to get and ASCII tree without grabbing it from print_plot?
        buf = io.StringIO()
        with redirect_stdout(buf):
            output.tree.print_plot(width=100)
        t = buf.getvalue()
        # Add common names by replacing ott ids
        for species in trees:
            if "ott_id" not in trees[species] or "common_name" not in trees[species]:
                continue
            t = re.sub(" ott" + str(trees[species]["ott_id"]) + r"\b", " (" + trees[species]["common_name"] + ")", t)
        print(t)
        with open("trees_tree.txt", 'w', encoding="utf-8") as fh:
            fh.write(t)
        # treefile = "outfile.tree"
        # output.tree.write(path = treefile, schema = "newick")


if __name__ == "__main__":
    main()
