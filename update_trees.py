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
import io
import logging
import re

from opentree import OT

from eggcyc.trees import load_tree_list, write_tree_list, lookup_common_names


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
            trees_processed = load_tree_list()
        else:
            trees_processed = {}  # don't use existing data
        trees = load_tree_list(filename="trees.json")
        lookup_common_names(trees, trees_processed)
        lookup_ott_ids(trees)
        if trees == trees_processed:
            print("No new data, not updating trees_processed.json")
        else:
            write_tree_list(trees)
    else:
        trees = load_tree_list()

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
