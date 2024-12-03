#
# Open tree of life web APIs:
# https://github.com/OpenTreeOfLife/germinator/wiki/Open-Tree-of-Life-Web-APIs
#
# Python code:
# https://opentree.readthedocs.io/en/latest/notebooks.html
#
# Examples:
# https://github.com/snacktavish/OpenTree_SSB2020/blob/master/notebooks/DEMO_OpenTree.ipynb
#
import csv
import gzip
import json
import logging
import re

from opentree import OT

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
        if species in common_names:
            if common_names[species] == "":
                logging.warning("No common name for %s in USDA database", species) 
            else:
                trees[species]['common_name'] = common_names[species]
        else:
            logging.warning("Species %s not found in USDA database", species)

            
with open('trees.json', 'r') as fh:
    trees = json.load(fh)

lookup_common_names(trees)

ott_ids = []
for species in trees.keys():
    m = OT.tnrs_match([species])
    id = m.response_dict['results'][0]['matches'][0]['taxon']['ott_id']
    print("ott_id for %s is %d" % (species, id))
    ott_ids.append(id)
    
# Get the synthetic tree from OpenTree
output = OT.synth_induced_tree(ott_ids=ott_ids, label_format='name')
output.tree.print_plot(width=100)
#treefile = "outfile.tree"
#output.tree.write(path = treefile, schema = "newick")

