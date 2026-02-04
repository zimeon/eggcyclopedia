#!/usr/bin/env python3
"""

ott_id for Quercus rubra is 791115
ott_id for Quercus kelloggii is 403375

Dates:
https://github.com/McTavishLab/jupyter_OpenTree_tutorials/blob/master/notebooks/DEMO_DatedTree.ipynb

>>> curl -X POST https://dates.opentreeoflife.org/v4/dates/dated_tree -d '{"node_ids":["ott791115", "ott403375"], "max_age":"180"}' | jsonpp

{
    "dated_trees_newick_list": [
        "((((((ott791115:9.834022)mrcaott316110ott791115:2.744552)mrcaott316110ott494536:2.744552)mrcaott137331ott316110:3.721832)mrcaott137331ott3930379:2.971260)mrcaott137331ott538292:157.983780,(ott403375:21.858711)mrcaott403375ott470257:158.141296)mrcaott137331ott403375:1.000000;"
    ],
    "topology_sources": [
        "ot_2304@tree2",
        "ot_1393@tree8"
    ],
    "date_sources": [
        "ot_2304@tree7",
        "ot_1393@tree8",
        "ot_2304@tree6",
        "ot_1957@tree1"
    ],
    "tar_file_download": "dates.opentreeoflife.org/v4/dates/download_dates_tar/chrono_out_02_03_2026_18_24_22.tar.gz"
}

Chronosynth: https://github.com/OpenTreeOfLife/chronosynth/wiki/Chronosynth-methods-overview

Library for Newick format strings: https://gitlab.mpcdf.mpg.de/dlce-eva/python-newick

"""

import io
import logging
import re

from opentree import OT, OpenTree, OTWebServiceWrapper
from newick import loads

import requests


class DatedTree():

    def __init__(self, api_endpoint="dates.opentreeoflife.org", api_version="v4"):
        self._api_endpoint = api_endpoint
        self._api_version = api_version
        self._api_service = "dates"

    def _make_url(self, method):
        return("https://%s/%s/%s/%s" % (self._api_endpoint, self._api_version, self._api_service, method))

    def dated_tree(self, ott_ids=None, max_age=500.0):
        d = {"ott_ids": ott_ids, "max_age": str(max_age)}

        r = requests.post(self._make_url(method="dated_tree"), data=d)
        print(r.text)

DatedTree().dated_tree(ott_ids=["ott791115", "ott403375"])

#ott_ids = [791115, 403375]
#
#for node in tree[0].walk():
#    age = node.length
#    for desc in node.descendants:
#        print(f"{node} {age} --> {desc}")
