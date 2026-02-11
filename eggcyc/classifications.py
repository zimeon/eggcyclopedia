"""Eggcyclopedia of Wood classification data handling class."""

import json
import logging
import requests

import pygbif


class Classifications():
    """Classifications handling class."""

    def __init__(self):
        """Initialize Classficiations object."""
        self.RANKS = ["KINGDOM", "PHYLUM", "CLASS", "ORDER", "FAMILY", "GENUS", "SPECIES"]
        self.higher_taxa = None

    def html_label(self, name, trees=None):
        """HTML label with common and scientific names."""
        html = "<i>" + name + "</i>"
        if name in self.higher_taxa and "common_name" in self.higher_taxa[name]:
            return self.higher_taxa[name]["common_name"] + " (" + html + ")"
        if trees is not None and name in trees.trees and "common_name" in trees.trees[name]:
            return trees.trees[name]["common_name"] + " (" + html + ")"
        return html

    def load_higher_taxa(self, filename="higher_taxa_processed.json"):
        """Load list of higher_taxa that we need for tree classifications.

        Arguments:
            filename (str) - filename of JSON file in local directory that
                has tree data.

        Returns:
            dict - dictionary of information is indexed by taxa name. This is a
                reference to self.higher_taxa and likely only used then the
                Classification object is not persisted.
        """
        with open(filename, "r", encoding="utf-8") as fh:
            self.higher_taxa = json.load(fh)
        logging.info("Read %d taxa from %s", len(self.higher_taxa), filename)
        return self.higher_taxa

    def write_higher_taxa(self, filename="higher_taxa_processed.json"):
        """Write JSON file of all higher_taxa with data added.

        Write in pretty-print format so that diffs show up nicely between
        git copies of the file.

        Arguments:
            filename (str): name of file to write
        """
        print(f"Writing higher taxa data to {filename}")
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(self.higher_taxa, fh, indent=2, sort_keys=True)

    def get_higher_taxa_common_names(self, trees):
        """Get common names for GENUS and higher rank taxa in the tree from GBIF.

        Arguments:
            trees (Trees) - a Trees object with data about all tree species to
                be considered.
        """
        self.load_higher_taxa()
        to_look_up = {}
        for species in trees.trees:
            if "gbif_classification" in trees.trees[species]:
                for r in trees.trees[species]["gbif_classification"]:
                    if r["rank"] == "SPECIES":
                        continue
                    name = r["name"]
                    key = r["key"]
                    if name in self.higher_taxa and "common_name" in self.higher_taxa[name]:
                        print("Have data for %s" % (name))
                    else:
                        to_look_up[name] = key
        # Do lookups where data missing
        print("Need to lookup " + str(to_look_up))
        try:
            num_added = 0
            for name in to_look_up:
                key = to_look_up[name]
                gbif = pygbif.species.name_usage(key=key, language="en")
                if ("key" not in gbif) or (int(gbif["key"]) != int(key)) or ("vernacularName" not in gbif):
                    logging.warning("GBIF lookup for %s (key=%s) failed: %s", name, key, gbif)
                    continue
                if name not in self.higher_taxa:
                    self.higher_taxa[name] = {}
                self.higher_taxa[name]["gbif_id"] = int(key)
                self.higher_taxa[name]["common_name"] = gbif["vernacularName"]
                num_added += 1
        except requests.exceptions.ConnectionError as e:
            logging.warning("GBIF lookup failed: %s", e)
        # Write out if updated
        if num_added > 0:
            self.write_higher_taxa()

    def write_classifications_table(self, trees, class_table_filename="src/_includes/class_table.html"):
        """Write an HTML table that represents the tree of classifications from GBIF species data.

        Arguments:
            trees (Trees) - a Trees object with data about all tree species to
                be considered.
        """
        self.get_higher_taxa_common_names(trees)
        last_rank = "KINGDOM"
        rank_to_lower = {}
        rank_to_higher = {}
        for rank in self.RANKS:
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
        for rank in self.RANKS:
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
                    if r["rank"] == "SPECIES":
                        name = species  # use our species name in pref to GBIF
                    else:
                        name = r["name"]
                    names[r["rank"]] = name
                    if name not in name_counts:
                        name_counts[name] = 0
                    name_counts[name] += 1
                # Now look up tha map from name to name at next rank
                for rank in self.RANKS:
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
        for rank in self.RANKS:
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
        #
        # Write table
        logging.info("Writing %s..." % class_table_filename)
        with open(class_table_filename, "w", encoding="utf-8") as fh:
            fh.write("""<div class="classification">\n<table>\n""")
            fh.write("<tr>\n")
            for rank in self.RANKS:
                fh.write("""<th><div class="rotated">""" + rank + """</div></th>\n""")
            fh.write("</tr>\n")
            for row in range(entries):
                fh.write("<tr>\n")
                for rank in self.RANKS:
                    if table[rank][row] is not None:
                        name = table[rank][row]
                        if rank in ("KINGDOM", "PHYLUM", "CLASS"):
                            # rotated
                            fh.write("""<td rowspan="%d"><div class="rotated">%s</div></td>\n""" % (name_counts[name], self.html_label(name, trees)))
                        else:
                            fh.write("""<td rowspan="%d">%s</td>\n""" % (name_counts[name], self.html_label(name, trees)))
                fh.write("</tr>\n")
            fh.write("</table>\n</div>\n")
