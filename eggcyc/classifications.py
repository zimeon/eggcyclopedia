"""Eggcyclopedia of Wood classification data handling class."""

import logging


class Classifications():
    """Classifications handling class."""

    def __init__(self):
        """Initialize Classficiations object."""
        self.RANKS = ["KINGDOM", "PHYLUM", "CLASS", "ORDER", "FAMILY", "GENUS", "SPECIES"]

    def write_classifications_table(self, trees, class_table_filename="src/_includes/class_table.html"):
        """Write an HTML table that represents the tree of classifications from GBIF species data.

        Arguments:
            trees (Trees) - a Trees object with data about all tree species to
                be considered.
        """
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
        # Write table
        logging.info("Writing %s..." % class_table_filename)
        with open(class_table_filename, "w", encoding="utf-8") as fh:
            fh.write("""<div class="classification">\n<table>\n""")
            fh.write("<tr>\n")
            styles = {}
            for rank in self.RANKS:
                if rank in ("KINGDOM", "PHYLUM", "CLASS"):
                    style = "writing-mode: vertical-lr; text-orientation: mixed; transform: rotate(180deg);"
                else:
                    style = ""
                styles[rank] = style
                fh.write("""<th><div class="rotated">""" + rank + """</div></th>\n""")
            fh.write("</tr>\n")
            for row in range(entries):
                fh.write("<tr>\n")
                for rank in self.RANKS:
                    if table[rank][row] is not None:
                        name = table[rank][row]
                        fh.write("""<td rowspan="%d" style="%s">%s</td>\n""" % (name_counts[name], styles[rank], trees.display_name(name)))
                fh.write("</tr>\n")
            fh.write("</table>\n</div>\n")
