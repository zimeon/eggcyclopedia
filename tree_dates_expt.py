#!/usr/bin/env python3
"""Test Data Tree API.

ott_id for Quercus rubra is 791115
ott_id for Quercus kelloggii is 403375

Dates:
https://github.com/McTavishLab/jupyter_OpenTree_tutorials/blob/master/notebooks/DEMO_DatedTree.ipynb

Library for Newick format strings: https://gitlab.mpcdf.mpg.de/dlce-eva/python-newick
"""
import logging
import json
import requests

import newick


class DatedTree():
    """Synthetic tree of life with dated nodes.

    Uses the OpenTree Chronosynth API as desceibed at
    <https://github.com/OpenTreeOfLife/chronosynth/wiki/Draft-API-docs>.

    Example call from command line:
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
    """

    def __init__(self, api_endpoint="dates.opentreeoflife.org", api_version="v4"):
        """Initialize DatedTree."""
        self._api_endpoint = api_endpoint
        self._api_version = api_version
        self._api_service = "dates"

    def _make_url(self, method):
        """URL for this method."""
        return ("https://%s/%s/%s/%s" % (self._api_endpoint, self._api_version, self._api_service, method))

    def dated_tree(self, ott_ids=None, max_age=180):
        """Dated tree for the given ids."""
        d = {"node_ids": ott_ids, "max_age": str(max_age)}
        data_str = json.dumps(d)
        logging.debug("dated_tree call data: %s", data_str)
        try:
            ret = requests.post(self._make_url(method="dated_tree"), data=data_str, timeout=10)
        except requests.exceptions.Timeout:
            logging.error("Request timed out.")
        except requests.exceptions.RequestException as e:
            logging.error("Call error occurred: %s", str(e))
        dret = json.loads(ret.text)
        return dret["dated_trees_newick_list"][0]


dated_tree = DatedTree().dated_tree(ott_ids=["ott791115", "ott403375"])
print(dated_tree)
trees = newick.loads(dated_tree)
for node in trees[0].walk():
    age = node.length
    for desc in node.descendants:
        print(f"{node} {age} --> {desc}")
