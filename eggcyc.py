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
import csv
import gzip
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
                        help="run lookup on raw data (else use processed)")
    parser.add_argument("--tree", "-t", action="store_true",
                        help="generate tree")
    args = parser.parse_args()
    return args


def load_tree_list(filename='trees.json'):
    """Load list of trees that we are generating pages for.

    Returns dict that is indexed by species name.
    """
    with open(filename, 'r') as fh:
        trees = json.load(fh)
    logging.info("Read %d trees from %s", len(trees), filename)
    return trees


def write_tree_list(tree, filename='trees_processed.json'):
    with open(filename, 'w') as fh:
        trees = json.dump(tree, fh)


def lookup_common_names(trees):
    """Use USDA database to lookup the common names for all tress.

    Will add common_name key to dict for each tree.
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
                    #print(', '.join(row))
                    #print(species + " -- " + common_name)
    # Now lookup all trees
    for species in trees:
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
    """
    ott_ids = []
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
        except Exception as e:
            logging.warning("Failed lookup for %s (%s)", species, str(e))


def extract_ott_ids(trees):
    """The list of defined OTT ids """
    ott_ids = []
    for species in trees:
        if "ott_id" in trees[species]:
            ott_ids.append(trees[species]["ott_id"])
    return ott_ids

def main():
    args = parse_args()

    if args.lookup:
        trees = load_tree_list()
        lookup_common_names(trees)
        lookup_ott_ids(trees)
        write_tree_list(trees)
    else:
        trees = load_tree_list(filename="trees_processed.json")

    if args.tree:
        ott_ids = extract_ott_ids(trees)
        # Get the synthetic tree from OpenTree
        output = OT.synth_induced_tree(ott_ids=ott_ids, label_format='name')
        output.tree.print_plot(width=100)
        # treefile = "outfile.tree"
        # output.tree.write(path = treefile, schema = "newick")


if __name__ == "__main__":
    main()
