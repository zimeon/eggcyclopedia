#!/usr/bin/env python3
"""Eggcyclopedia of Wood Tree Data Handling Module."""
import csv
import gzip
import json
import logging
import re
import sys

from opentree import OT
from pygbif import species as gbif_species


class Trees():
    """Set of trees of interest."""

    def __init__(self, filename=None):
        """Initialize Trees object."""
        self.trees = {}
        if filename is not None:
            self.load_tree_list(filename)

    def load_tree_list(self, filename="trees_processed.json"):
        """Load list of trees that we are generating pages for.

        By default it loads the set of processed tree data but the
        filename may be specified to load the manual data from
        "trees.json".

        Arguments:
            filename (str) - filename of JSON file in local directory that
                has tree data.

        Returns:
            dict - dictionary of tree that is indexed by species name. The is a
                reference to self.trees and likely only used then the Trees
                object is not persisted.
        """
        with open(filename, "r", encoding="utf-8") as fh:
            self.trees = json.load(fh)
        logging.info("Read %d trees from %s", len(self.trees), filename)
        return self.trees

    def write_tree_list(self, filename="trees_processed.json"):
        """Write JSON file of all trees with data added.

        Write in pretty-print format so that diffs show up nicely between
        git copies of the file.

        Arguments:
            trees (dict): tree data
            filename (str): name of file to write
        """
        print(f"Writing {filename}")
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(self.trees, fh, indent=2, sort_keys=True)

    def expand_crosses(self):
        """Expand tree to include species for crosses.

        Modifies trees data in-place.
        """
        # Expand any crosses to add the original species if not
        # already present
        to_add = []
        for species in self.trees:
            if "cross_between" in self.trees[species]:
                if len(self.trees[species]["cross_between"]) != 2:
                    logging.error("cross_between information for %s should have 2 species names", species)
                    sys.exit(1)
                for parent in self.trees[species]["cross_between"]:
                    if parent not in self.trees[species]:
                        to_add.append(parent)
        for species in to_add:
            self.trees[species] = {}

    def merge_data_from(self, trees_processed):
        """Merge in data from past processing.

        Arguments:
            trees_processed - another Trees object with previously processed
                data to be reused where it does not conflict.

        Rules:
            species in trees_processed but not self - ignore
            species in self but not trees_processed - nothing to do as no data
                to add
            species in self and in trees_processed - add in any data from that
                does not conflict with existing data
        """
        for species in trees_processed.trees:
            if species in self.trees:
                for key in trees_processed.trees[species]:
                    if key not in self.trees[species]:
                        self.trees[species][key] = trees_processed.trees[species][key]
                self.trees[species] = trees_processed.trees[species]

    def lookup_common_names(self):
        """Use USDA database to lookup the common names for all tress.

        Will add common_name key to dict for each tree. If tress_processed is
        passed in then will data from there if present.
        """
        common_names = {}
        with gzip.open("usda_db_2024-12-02.csv.gz", "rt") as fh:
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
        # Now lookup all trees
        for species in self.trees:
            if "common_name" in self.trees[species]:
                # Don"t do a lookup of the config already has a
                # common name defined
                continue
            if species in common_names:
                if common_names[species] == "":
                    logging.warning("No common name for %s in USDA database", species)
                else:
                    self.trees[species]["common_name"] = common_names[species]
            else:
                logging.warning("Species %s not found in USDA database", species)

    def lookup_ott_ids(self):
        """Lookup Open Tree of Life Taxonomy ids.

        Open Tree of Life Taxonomy (OTT from now on).

        Adds data to the "ott_id" attribute for each species in the trees dict that
        does not already have the attribute.
        """
        # Now go through and lookup ids
        for species in self.trees:
            if "ott_id" in self.trees[species]:
                continue
            if "skip" in self.trees[species] or "cross_between" in self.trees[species]:
                # FIXME: How to handle crosses (e.g. Common lime)
                continue
            # Look it up
            try:
                m = OT.tnrs_match([species])
                id = m.response_dict['results'][0]['matches'][0]['taxon']['ott_id']
                print("ott_id for %s is %d" % (species, id))
                self.trees[species]["ott_id"] = id
            except Exception as e:  # pylint: disable=broad-exception-caught
                logging.warning("Failed lookup for %s (%s)", species, str(e))

    def lookup_gbif_ids(self):
        """Lookup GBIF ids for any entries that don't have them.

        Uses the Opentree lookup from ott_id to GBIF id.
        """
        for species in self.trees:
            gbif = gbif_species.name_backbone(scientificName=species, taxonRank="SPECIES", strict=True)
            if "usage" not in gbif:
                logging.warning("GBIF lookup for %s failed: %s", species, str(gbif))
                continue
            if gbif["diagnostics"]["matchType"] != "EXACT":
                logging.warning("GBIF lookup for %s not EXACT: %s", species, str(gbif))
            self.trees[species]["gbif_id"] = gbif["usage"]["key"]
            self.trees[species]["gbif_classification"] = gbif["classification"]

    def extract_ott_ids(self):
        """Extract list of defined OTT ids.

        Returns:
            list: of integer ott_ids.
        """
        ott_ids = []
        for species in self.trees:
            if "ott_id" in self.trees[species]:
                ott_ids.append(self.trees[species]["ott_id"])
        return ott_ids
