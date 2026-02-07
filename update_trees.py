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
    parser.add_argument("--classification", "-c", action="store_true",
                        help="generate classification table")
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
        trees.lookup_gbif_ids()
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

    if args.classification:
        # Assemble data
        # Build lookup of rank to higher
        RANKS = ["KINGDOM", "PHYLUM", "CLASS", "ORDER", "FAMILY", "GENUS", "SPECIES"]
        last_rank = "KINGDOM"
        rank_to_lower = {}
        rank_to_higher = {}
        for rank in RANKS:
            if rank == "KINGDOM":
                continue
            rank_to_lower[last_rank] = rank
            rank_to_higher[rank] = last_rank
            # print("## %s -> %s" % (last_rank, rank))
            last_rank = rank
        # A each rank, build a map of names to names at the next
        # lower rank
        rank_name_to_lower_set = {}
        name_counts = {}  # Num species for each name (assume all names unique)
        for rank in RANKS:
            if rank == "SPECIES":
                continue
            rank_name_to_lower_set[rank] = {}
        # Now look at data for each species
        entries = 0
        for species in trees.trees:
            if "gbif_classification" in trees.trees[species]:
                entries += 1
                # Build map of rank -> name for this species
                names = {}
                for r in trees.trees[species]["gbif_classification"]:
                    name = r["name"]
                    names[r["rank"]] = name
                    if name not in name_counts:
                        name_counts[name] = 0
                    name_counts[name] += 1
                # Now look up tha map from name to name at next rank
                for rank in RANKS:
                    if rank == "SPECIES":
                        continue
                    name = names[rank]
                    lower_name = names[rank_to_lower[rank]]
                    if name not in rank_name_to_lower_set[rank]:
                        rank_name_to_lower_set[rank][name] = set()
                    rank_name_to_lower_set[rank][name].add(lower_name)
        # Find the complete set of table entries indexed by [rank][row_num]
        # where row_num starts at zero. Entries are either a name or None. The
        # rows must align so that they describe he correct classification for
        # the species at the end.
        table = {}
        last_rank = []
        next_rank = []
        for rank in RANKS:
            table[rank] = [None for i in range(entries)]
            count = 0
            if rank == "KINGDOM":
                for name in rank_name_to_lower_set[rank]:
                    table[rank][count] = name
                    next_rank += [name for i in range(name_counts[name])]
                    count += name_counts[name]
            else:
                next_rank = []
                # print(rank)
                count = 0
                while count < entries:
                    # print(str(count) + " < " + str(entries))
                    higher_name = last_rank[count]
                    higher_rank = rank_to_higher[rank]
                    for name in sorted(rank_name_to_lower_set[higher_rank][higher_name]):
                        # print("%s (%d)" % (higher_name, name_counts[higher_name]))
                        # print(" --> " + name)
                        table[rank][count] = name
                        next_rank += [name for i in range(name_counts[name])]
                        # print("table[%s][%d] = %s" % (rank,count,name))
                        count += name_counts[name]
            last_rank = next_rank
        # Write table
        with open("trees_by_classification.html", "w", encoding="utf-8") as fh:
            fh.write("""<table style="
            xborder-collapse: collapse;
            border: 2px solid black;">\n""")
            fh.write("<tr>\n")
            styles = {}
            for rank in RANKS:
                if rank in ("KINGDOM", "PHYLUM", "CLASS"):
                    style = "writing-mode: vertical-lr; text-orientation: mixed; transform: rotate(180deg);"
                else:
                    style = ""
                styles[rank] = style
                fh.write("""<th style="border-collapse: collapse; border: 1px solid black; background-color: #eff;"><div style=" """ + style + """ ">""" + rank + """</div></th>\n""")
            fh.write("</tr>\n")
            for row in range(entries):
                fh.write("<tr>\n")
                for rank in RANKS:
                    if table[rank][row] is not None:
                        name = table[rank][row]
                        fh.write("""<td rowspan="%d" style="border: 2px solid black; background-color: #ffd;%s">%s</td>\n""" % (name_counts[name], styles[rank], name))
                fh.write("</tr>\n")
            fh.write("</table>\n")


if __name__ == "__main__":
    main()
