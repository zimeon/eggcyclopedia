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

from eggcyc.trees import Trees


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


def main():
    """CLI handler."""
    args = parse_args()

    if args.lookup or args.lookup_all:
        trees = Trees(filename="trees.json")
        trees.expand_crosses()
        if args.lookup:
            trees_processed = Trees(filename="trees_processed.json")
            trees.merge_data_from(trees_processed)
        trees.lookup_common_names()
        trees.lookup_ott_ids()
        if args.lookup and trees.trees == trees_processed.trees:
            print("No new data, not updating trees_processed.json")
        else:
            trees.write_tree_list()
    else:
        trees = Trees(filename="trees_processed.json")

    if args.tree:
        ott_ids = trees.extract_ott_ids()
        # Get the synthetic tree from OpenTree
        output = OT.synth_induced_tree(ott_ids=ott_ids, label_format='name_and_id')
        # Get ASCII tree with labels "name (common name)"
        # FIXME - How to get and ASCII tree without grabbing it from print_plot?
        buf = io.StringIO()
        with redirect_stdout(buf):
            output.tree.print_plot(width=100)
        t = buf.getvalue()
        # Add common names by replacing ott ids
        for species in trees.trees:
            if "ott_id" not in trees.trees[species] or "common_name" not in trees.trees[species]:
                continue
            t = re.sub(" ott" + str(trees.trees[species]["ott_id"]) + r"\b", " (" + trees.trees[species]["common_name"] + ")", t)
        print(t)
        with open("trees_tree.txt", 'w', encoding="utf-8") as fh:
            fh.write(t)
        # treefile = "outfile.tree"
        # output.tree.write(path = treefile, schema = "newick")


if __name__ == "__main__":
    main()
