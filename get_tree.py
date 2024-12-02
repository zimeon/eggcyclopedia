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
from opentree import OT

trees = ["Quercus rubra", "Quercus alba", "Buxus sempervirens", "Salix nigra", "Acer saccharum"]

ott_ids = []
for species in trees:
    m = OT.tnrs_match([species])
    id = m.response_dict['results'][0]['matches'][0]['taxon']['ott_id']
    print("ott_id for %s is %d" % (species, id))
    ott_ids.append(id)
    
treefile = "outfile.tree"
#Get the synthetic tree from OpenTree
output = OT.synth_induced_tree(ott_ids=ott_ids,  label_format='name')
output.tree.write(path = treefile, schema = "newick")
output.tree.print_plot(width=100)
