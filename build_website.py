#!/usr/bin/env python3
"""Build Eggcyclopedia of Wood website.

Process a mix of verbatim and processed content.
"""
import argparse
import json
import logging
import os
import re
import shutil
import sys

import frontmatter  # python-frontmatter
from liquid import CachingFileSystemLoader, Environment, Mode
import markdown
from markdown.extensions.tables import TableExtension

from eggcyc.trees import load_tree_list

class FileProcessor():
    """Class to process a single file, whether it be render or copy.

    Keeps track of Liquid rendering environment (including cache) and
    also counts the number and types of updates made.
    """

    def __init__(self, src_dir, config):
        """Initialize FileProcessor object.

        src_dir - Source directory for root of directory structure.
        """
        self.src_dir = src_dir
        # Extract what we need from config
        self.files_to_ignore = config['files_to_ignore']
        self.files_to_ignore_regex = re.compile(config['files_to_ignore_regex'])
        self.site_variables = config['site_variables']
        self.templates_dir = os.path.join(src_dir, '_templates')
        self.exts_to_scan = ['.md', '.html']
        self.copied = 0
        self.processed = 0
        self.unchanged = 0
        self.new_dst_files = set()  # All files wanted under dst_dir
        self.setup_liquid()

    def setup_liquid(self):
        """Set up the Liquid template engined with a loader and site variables.

        Call this again if the site variables are updated.
        """
        # Set up liquid template engie
        loader = CachingFileSystemLoader(self.templates_dir, ext='.html', cache_size=100)
        self.liquid_env = Environment(loader=loader, tolerance=Mode.STRICT, globals={'site': self.site_variables})

    def ignore_file(self, filename):
        """File should be ignored if True.

        Arguments:
            filename (str) - the file name of the file to check
        """
        if filename in self.files_to_ignore:
            logging.debug("ignore_file: Ignoring file %s by name", filename)
            return True
        if self.files_to_ignore_regex.search(filename):
            logging.debug("ignore_file: Ignoring file %s by pattern", filename)
            return True
        return False

    def extract_frontmatter(self, filename, md):
        """Extract frontmatter if present, warn if not.

        Frontmatter is Jeklyll styles, see https://jekyllrb.com/docs/front-matter/.
        Adds extracted data to md dict with all page information added
        as page.*.

        Will return True if there is frontmatter (or it is empty), else False.
        """
        logging.debug("Scanning frontmatter for %s", filename)
        try:
            with open(filename, 'r', encoding='utf-8') as fh:
                fm = frontmatter.load(fh)
                logging.debug("yaml: %s", fm.metadata)
                md['page'].update(fm.metadata)
                md['content'] = fm.content
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.warning("Error - problem reading frontmatter from %s, will treat as if file had none (%s)", filename, e)
            return False
        return len(fm.metadata) > 0

    def process_file(self, filename, dst_root, dst_name, md=None):
        """Check one file and process, copy or ignore as necessary.

        Parameters
        ----------
        filename : str
            Source file name
        dst_root : str
            Directory path for output file
        dst_name : str
            Output file name in `dst_root`
        md : dict
            Default metadata, will be added to and may be overridded.
        """
        basename = os.path.basename(filename)
        if self.ignore_file(basename):
            return
        logging.debug("Checking %s", filename)
        ext = os.path.splitext(basename)[1]
        if ext in self.exts_to_scan:
            if md is None:
                md = {}
            if 'page' not in md:
                md['page'] = {}
            md['page']['layout'] = 'page'
            md['page']['source_format'] = ext
            if self.extract_frontmatter(filename, md):
                # If there is frontmatter then render
                self.render(filename, dst_root, dst_name, md)
                return
        # We didn't ignore or render, so copy
        self.copy(filename, dst_root, dst_name)

    def copy(self, src_filename, dst_root, dst_name):
        """Copy one file from the source to destination tree."""
        dst_filename = os.path.normpath(os.path.join(dst_root, dst_name))
        if not os.path.exists(dst_root):
            os.makedirs(dst_root)
        # Keep a record that we want this file under dst_dir
        self.new_dst_files.add(dst_filename)
        if (os.path.exists(dst_filename)
                and os.path.getsize(src_filename) == os.path.getsize(dst_filename)
                and os.path.getmtime(src_filename) <= os.path.getmtime(dst_filename)):
            logging.info("Unchanged %s -> %s", src_filename, dst_filename)
            self.unchanged += 1
        else:
            logging.info("Copying %s -> %s", src_filename, dst_filename)
            shutil.copy2(src_filename, dst_filename)
            self.copied += 1

    def render(self, src_filename, dst_root, dst_name, md):
        """Render source to HTML in dst_root.

        Parameters:
        * src_filename - used just for reporting
        * dst_root - director that output file with go in
        * dst_name - file name of output, will be adjusted to have .html extension
        * md - metadata context for this page
            md['page']['source_format'] either '.md' or '.html'
        """
        dst_name = os.path.splitext(dst_name)[0] + '.html'  # Replace ext with .html
        dst_filename = os.path.normpath(os.path.join(dst_root, dst_name))
        # Keep a record that we want this file under dst_dir
        self.new_dst_files.add(dst_filename)
        if not os.path.exists(dst_root):
            os.makedirs(dst_root)
        logging.warning("Rendering %s -> %s", src_filename, dst_filename)
        # FIXME - Would need to check template dates in order to safely do this
        # if (os.path.exists(dst_filename)
        #        and os.path.getmtime(src_filename) < os.path.getmtime(dst_filename)):
        #    logging.info("Unchanged %s -> %s", src_filename, dst_filename)
        #    self.unchanged += 1
        #    return
        if md['page']['source_format'] == '.md':
            # Might be nice to use newline-to-break 'nl2br' extension for new
            # material but I have a whole bunc of old stuff that expects
            # newlines not to be significant.
            md['content'] = markdown.markdown(
                md['content'],
                extensions=['toc', 'smarty', 'attr_list', TableExtension(), ],
                extension_configs={'smarty': {
                    'substitutions': {
                        'left-single-quote': "‘",
                        'right-single-quote': "’",
                        'left-double-quote': "“",
                        'right-double-quote': "”",
                        'ellipsis': "…",
                        'ndash': "–"
                    }
                }})
        template = self.liquid_env.get_template(md['page']['layout'])
        with open(dst_filename, 'w', encoding='utf-8') as fh:
            fh.write(template.render(**md))
        self.processed += 1

    def render_md_page(self, dst_root, dst_name, md, template="gallery"):
        """Render content in md to HTML in dst_root.

        Arguments:
            dst_root - director that output file with go in
            dst_name - file name of output, will be adjusted to have .html extension
            md - metadata context for this page
               md['page']['source_format'] either '.md' or '.html'
            template - template to render with
        """
        dst_name = os.path.splitext(dst_name)[0] + '.html'  # Replace ext with .html
        dst_filename = os.path.normpath(os.path.join(dst_root, dst_name))
        dst_path = os.path.dirname(dst_filename)
        # Keep a record that we want this file under dst_dir
        self.new_dst_files.add(dst_filename)
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        logging.warning("Rendering %s", dst_filename)
        if md['page']['source_format'] == '.md' and "content" in md:
            md['content'] = markdown.markdown(
                md['content'],
                extensions=['toc', 'smarty', 'attr_list', TableExtension(), ],
                extension_configs={'smarty': {
                    'substitutions': {
                        'left-single-quote': "‘",
                        'right-single-quote': "’",
                        'left-double-quote': "“",
                        'right-double-quote': "”",
                        'ellipsis': "…",
                        'ndash': "–"
                    }
                }})
        template = self.liquid_env.get_template(template)
        with open(dst_filename, 'w', encoding='utf-8') as fh:
            fh.write(template.render(**md))
        self.processed += 1

    def stats(self):
        """Statistics about files copied, processed, etc..

        Returns:
            str: description string
        """
        return "%d copied, %d processed, %d unchanged" % (self.copied, self.processed, self.unchanged)


class SiteProcessor():
    """Class to handle processing of an entire site.

    Keeps counts etc. as it goes through.
    """

    def __init__(self, src_dir, dst_dir, config):
        """Initialize SiteProcessor object."""
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.config = config
        self.dirs_to_ignore = config['dirs_to_ignore']
        self.dirs_to_ignore_regex = re.compile(config['dirs_to_ignore_regex'])
        self.root_dirs_to_ignore = config['root_dirs_to_ignore']
        self.site_variables = config['site_variables']
        self.fp = FileProcessor(src_dir=self.src_dir, config=config)
        self.old_dst_files = set()
        self.removed = 0

    def scan_dst(self):
        """Scan destination directory returning all relevant file names.

        Store a list of all files under self.dst_dir so that we can later
        check against was added or didn't need to be updated using the
        cleanup_dst() method.
        """
        filenames = set()
        for root, dirs, files in os.walk(self.dst_dir):
            for file in files:
                if not self.fp.ignore_file(file):
                    logging.debug("scan_dst: Adding %s", file)
                    filenames.add(os.path.join(root, file))
            for dir in dirs.copy():  # copy() so loop not messed up by removes
                if root == self.dst_dir and dir in self.root_dirs_to_ignore:
                    logging.debug("scan_dst: Ignoring root dir %s", os.path.join(root, dir))
                    dirs.remove(dir)
                if dir in self.dirs_to_ignore or self.dirs_to_ignore_regex.search(dir):
                    logging.debug("scan_dst: Ignoring dir %s", os.path.join(root, dir))
                    dirs.remove(dir)
        logging.info("Scanned %d files in dst dir", len(filenames))
        self.old_dst_files = filenames

    def cleanup_dst(self):
        """Clean outdated file from the destination tree.

        Compare the sets of filenames that were present in the dst_dir
        before the build, with those that were either written or would have
        been written if not already up-to-date.
        """
        for dst_filename in self.old_dst_files - self.fp.new_dst_files:
            logging.info("Would delete old file %s", dst_filename)
            # os.remove(dst_filename)
            # self.removed += 1

    def process_file(self, file):
        """Scan one source file in given directory under src_dir.

        Arguments:
            file (str) - file path under source directory
        """
        filename = os.path.join(self.src_dir, file)
        root, name = os.path.split(filename)
        dst_root = os.path.join(self.dst_dir, os.path.relpath(root, self.src_dir))
        self.fp.process_file(filename, dst_root, name)

    def process_source(self, directory=''):
        """Scan all files in given directory under the src_dir.

        If the `directory` parameter is left empty then the entire source
        tree will be processed.
        """
        logging.warning("\n\n############# process_source(%s)...", directory)
        directory = directory if directory else self.src_dir
        for root, dirs, files in os.walk(directory):
            logging.warning("##### %s %s %s", root, dirs, files)
            # Work out equivalent root in dst_dir
            dst_root = os.path.join(self.dst_dir, os.path.relpath(root, start=self.src_dir))
            in_root_dir = root == self.src_dir
            for dir in dirs.copy():  # copy() so loop not messed up by removes
                if dir in self.dirs_to_ignore:
                    dirs.remove(dir)
                    logging.debug("Ignoring source dir by name %s", dir)
                elif self.dirs_to_ignore_regex.search(dir):
                    dirs.remove(dir)
                    logging.debug("Ignoring source dir by pattern %s", dir)
                elif in_root_dir and (dir in self.root_dirs_to_ignore):
                    dirs.remove(dir)
                    logging.info("Skipping top-level source dir %s", dir)
                else:
                    logging.debug("Dir map: %s / %s -> %s / %s ", root, dir, dst_root, dir)
            for file in files:
                filename = os.path.join(root, file)
                logging.info("Processing file %s %s %s", filename, dst_root, file)
                self.fp.process_file(filename, dst_root, file)

    def species_page(self, trees, species):
        """Species page URL path relative to web root."""
        if "common_name" not in trees[species]:
            logging.error("Missing common name for {species}")
            sys.exit(1)
        return os.path.join("sp", re.sub(" " , "_", trees[species]["common_name"].lower()) + ".html")

    def species_egg_base(self, trees, species):
        """Species egg base URL path relative to web root.

        Does not include the suffix {#}{a|b|c}.jpg, e.g. "1a.jpg"
        """
        if "common_name" not in trees[species]:
            logging.error("Missing common name for {species}")
            sys.exit(1)
        return os.path.join("photos", "egg_" + re.sub(" " , "_", trees[species]["common_name"].lower()) + "_")

    def build_species_pages(self):
        """Build pages for each species.

        Create pages {dst}/sp/{common_name}.html for each species where
        I have an egg. Include up to three photos of the egg.
        """
        trees = load_tree_list()
        species_pages = {}   # species -> species_page
        for species in trees:
            page = self.species_page(trees, species)
            output_file = os.path.join(self.dst_dir, page)
            logging.debug(">>> creating %s and %s", page, output_file)
            egg_base = self.species_egg_base(trees, species)
            eggs = []
            for ext in ("1a.jpg", "1b.jpg", "1c.jpg"):
                egg_photo = egg_base + ext
                if os.path.isfile(os.path.join(self.dst_dir, egg_photo)):
                    eggs.append(egg_photo)
            if len(eggs) == 0:
                logging.debug(">>> No egg photos, skipping")
                continue
            logging.debug(">>> got %s eggs", eggs)
            # Now build page
            common_name = trees[species]["common_name"]
            md = {"page": trees[species]}
            md['page']['source_format'] = '.md'
            md['page']['title'] = common_name
            figures = ""
            for egg in eggs:
                figures += "\n<figure>\n"
                figures += '  <img src="/%s" alt="%s egg photo"/>\n' % (egg, common_name)
                figures += '  <figcaption>%s %s</figcaption>\n' % (common_name, egg)
                figures += "</figure>\n"
            md["figures"] = figures
            self.fp.render_md_page(self.dst_dir, page, md)
            species_pages[species] = page
        #
        # And now write the species.html page
        md = {"page": {"source_format": ".md"}}
        md['page']['title'] = "Species"
        list = "<ul>\n"
        for species in trees:
            text = "%s (<i>%s<i>)" % (trees[species]["common_name"], species)
            if species in species_pages:
                text = '<a href="' + species_pages[species] + '">' + text + "</a>"
            list += "  <li>" + text + "</li>\n"
        list += "</ul>"
        md["list"] = list
        self.fp.render_md_page(self.dst_dir, "species.html", md, template="species")

    def build_site(self):
        """Build site."""
        self.scan_dst()
        self.process_source()
        self.build_species_pages()
        self.cleanup_dst()
        logging.warning("Done: %s, %d old files removed", self.fp.stats(), self.removed)


def command_line_script():
    """Run from command line."""
    p = argparse.ArgumentParser()
    p.add_argument("-q", "--quiet", action="store_true",
                   help="Don't show normal warnings")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Show verbose details (use --debug for even more)")
    p.add_argument("--debug", action="store_true",
                   help="Show extremely verbose debugging information (implies --verbose too)")
    p.add_argument("--src", action="store", default="src",
                   help="Source directory, ")
    p.add_argument("--dst", action="store", default="docs",
                   help="Destination directory for web pages")
    p.add_argument("--file", action="store",
                   help="Process just specified file in source directory")
    p.add_argument("--config", action="store", default="build_website_config.json",
                   help="JSON configuration file.")
    args = p.parse_args()

    # Logging
    logging.basicConfig(level=(logging.ERROR if args.quiet else (
        logging.DEBUG if args.debug else (
            logging.INFO if args.verbose else logging.WARN))),
        format='%(message)s')

    with open(args.config, 'r', encoding='utf-8') as fh:
        config = json.load(fh)

    if not os.path.isdir(args.dst):
        logging.error("Destination directory %s must already exist", args.dst)
        sys.exit()

    processor = SiteProcessor(src_dir=args.src, dst_dir=args.dst, config=config)
    if args.file:
        # Is the src_dir prepended? If so, stip it before passing in
        file = args.file
        if os.path.commonpath([args.src, file]) == args.src:
            file = os.path.relpath(file, start=args.src)
        logging.warning("Examining source file/dir %s", file)
        processor.process_file(file=file)
    else:
        processor.build_site()


if __name__ == "__main__":
    command_line_script()
