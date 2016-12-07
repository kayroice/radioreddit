#!/usr/bin/env python3

import fnmatch
import json
import logging
import os
import shutil
import subprocess
import uuid
import urllib.request


class RadioRedditErr(Exception):
    pass


class RadioReddit(object):
    def __init__(self, ytdl_bin=None):
        """
        """
        # TODO: Check if ffprobe or avprobe exist as executables.
        self.ytdl_bin = self.get_ytdl_bin(ytdl_bin)
        self.default_listing_type = 'random'


    def api_uri(self, api_uri=None):
        """
        Get the Reddit API URI.

        Args:
            api_uri (str): Reddit API URI, defaults to 'https://www.reddit.com'.

        Returns:
            Returns the reddit API URI as a string.
        """
        api_uri = api_uri or 'https://www.reddit.com'
        logging.debug("Reddit API URI defined as {}".format(api_uri))
        return api_uri


    def create_mp3(self, url, mp3_dir=None, ytdl_bin=None,
                   create_mp3_dir=True):
        """
        Call 'youtube-dl' to create an mp3 from a URL. Write the mp3 out to
        the given mp3 directory.

        Args:
            create_mp3_dir (bool): A boolean controlling whether or not to
                create mp3 dirs if they don't exist. Defaults to True.
            mp3_dir (str): Directory to write mp3 files out to.
                None.
            url (str): URL to extract mp3 from.
            ytdl_bin (str): Path to youtube-dl binary.

        Returns:
            Returns the path to the mp3 file written out as a string.
        """
        mp3_dir = mp3_dir or self.mp3_dir()
        ytdl_bin = ytdl_bin or self.ytdl_bin
        self.extractor_domain_is_supported(urllib.parse.urlsplit(url)[1])
        self.mp3_dir_exists(mp3_dir, create_mp3_dir)
        ytdl_cmd = self.ytdl_cmd(url, mp3_dir, ytdl_bin)
        rc, out, err = self.exec_shell_cmd(ytdl_cmd)
        if rc:
            for line in err.decode().split('\n'):
                if line.startswith('ERROR'):
                    logging.error(line)
            raise RadioRedditErr(err.decode())
        for line in out.decode().split('\n'):
            if 'Post-process file' in line and line.endswith('skipping'):
                mp3 = line.split(' exists')[0].split()[-1]
                msg = "{} already exists, skipping.".format(mp3)
                raise RadioRedditErr(msg)
            elif '[ffmpeg] Destination:' in line:
                mp3 = line.split(': ')[1]
                logging.debug("Successfully wrote mp3 file {}".format(mp3))
                return mp3
        return None


    def create_mp3_from_subreddit(self, subreddit, mp3_dir=None, api_uri=None,
                                  create_mp3_dir=True, ytdl_bin=None,
                                  listing_type=None):
        """
        Create an mp3 by fetching a listing URL from the given subreddit.

        Args:
            api_uri (str): Reddit API URI.
            create_mp3_dir (bool): A boolean controlling whether or not to
                create mp3 dirs if they don't exist. Defaults to True.
            mp3_dir (str): Directory to write mp3 files out to.
            listing_type (str): Type of listing query to perform, defaults to
                'random'.
            subreddit (str): Subreddit to extract mp3 from.
            ytdl_bin (str): Path to youtube-dl binary.

        Returns:
            Returns the path to the mp3 file written out as a string.
        """
        api_uri = api_uri or self.api_uri(api_uri)
        mp3_dir = mp3_dir or self.mp3_dir()
        url = self.listing_url(subreddit, api_uri, listing_type)
        mp3 = self.create_mp3(url=url, create_mp3_dir=create_mp3_dir,
                              mp3_dir=mp3_dir, ytdl_bin=ytdl_bin)
        return mp3        


    def create_pls(self, mp3_dir=None, pls_file=None, overwrite=True,
                   recurse=False):
        """
        Create a playlist file given a directory to search for audio files.

        https://en.wikipedia.org/wiki/PLS_(file_format)

        Args:
            mp3_dir (str): Directory to write mp3 files out to.
            pls_file (str): Path of the playlist file to be created.
            overwrite (bool): Boolean governing whether to overwrite an existing
                playlist file. Defaults to True.
            recurse (bool): Boolean governing whether to recursively search
                subdirs of the mp3 dir.

        Returns:
            Returns the name of the playlist file as a string.
        """
        mp3_dir = mp3_dir or self.mp3_dir(mp3_dir)
        pls_file = pls_file or self.pls_file(mp3_dir, pls_file)
        if not overwrite and os.path.isfile(pls_file):
            msg = "{} exists, not overwriting."
            raise RadioRedditErr(msg)
        mp3_files = self.find_files(mp3_dir, recurse=recurse)
        num_entries = len(mp3_files)
        try:
            with open(pls_file, 'w') as pls_fd:
                logging.debug("Writing playlist out to {}".format(pls_file))
                pls_fd.write("[playlist]\n")
                pls_fd.write("NumberOfEntries={}\n".format(num_entries))
                for mp3_file in mp3_files:
                    logging.debug("Adding {} to {}".format(mp3_file, pls_file))
                    file_num = mp3_files.index(mp3_file) + 1
                    pls_fd.write("File{}={}\n".format(file_num, mp3_file))
        except Exception as e:
            msg = "Failed to write out playlist file {}: {}".format(pls_file, e)
            raise RadioRedditErr(msg)
        return pls_file


    def exec_shell_cmd(self, shell_cmd):
        """
        Execute a shell command.

        Args:
            shell_cmd (list): A list containing a command and optional arguments
            as additional elements.

        Returns:
            A sequence where the first element is the return code of the
            command and the last two elements are byte objects of the
            command's stdout and stderr.
        """
        logging.info("Executing: {}".format(' '.join(shell_cmd)))
        shell_cmd_exec = subprocess.Popen(shell_cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
        shell_cmd_out, shell_cmd_err = shell_cmd_exec.communicate()
        shell_cmd_rc = shell_cmd_exec.returncode
        logging.debug("Return code of {}: {}".format(' '.join(shell_cmd),
                                                              shell_cmd_rc))
        if shell_cmd_out and not shell_cmd_out.isspace():
            logging.debug("Shell command STDOUT: {}".format(shell_cmd_out))
        if shell_cmd_err and not shell_cmd_err.isspace():
            logging.debug("Shell command STDERR: {}".format(shell_cmd_err))
        return shell_cmd_rc, shell_cmd_out, shell_cmd_err


    def extractor_domain_is_supported(self, domain, ytdl_bin=None):
        """
        Check if the given domain is a supported extractor domain.

        Args:
            domain (str): Domain name to be checked.
            ytdl_bin (str): Path to youtube-dl binary.

        Returns:
            Returns True if extraction domain is supported, otherwise raises
            an exception.
        """
        ytdl_bin = ytdl_bin or self.ytdl_bin
        logging.debug("Checking if domain {} is supported.".format(domain))
        extractor_domains = self.extractor_domains(ytdl_bin)
        for extractor_domain in extractor_domains:
            msg = "Checking if {} in {}".format(extractor_domain, domain)
            logging.debug(msg)
            # We remove '.' from the domain to be checked because some URLs
            # use shorteners, such as 'youtu.be', and won't match the supported
            # extractor domains, e.g. 'youtube'.
            if extractor_domain in domain.replace('.', ''):
                msg = "Extraction domain {} is supported.".format(domain)
                logging.debug(msg)
                return True
        msg = "Extraction domain {} is not supported.".format(domain)
        raise RadioRedditErr(msg)


    def extractor_domains(self, ytdl_bin=None):
        """
        Execute 'youtube-dl --list-extractors' to discover the list of available
        extractor domains.

        Args:
            ytdl_bin (str): Path to youtube-dl binary.

        Returns:
            Returns a list of extractor domains. The output of the 'youtube-dl'
            command has been modified to downcase all domains, and split on the
            first ':'. We do this to make it easier to match against the
            extraction domain.
        """
        ytdl_bin = ytdl_bin or self.ytdl_bin
        extractor_domains = []
        stdout = self.exec_shell_cmd([ytdl_bin, '--list-extractors'])[1]
        for line in stdout.decode().split("\n"):
            if line:
                # We downcase all extractor domains because the output of
                # '--list-extractors' has mixed case domain names, for
                # example 'AdultSwim'.
                extractor_domain = line.split(':')[0].lower()
                extractor_domains.append(extractor_domain)
        return extractor_domains


    def find_files(self, dirname, extension='mp3', recurse=False):
        files = []
        logging.debug("Searching for files in {}".format(dirname))
        for root, dirnames, filenames in os.walk(dirname):
            for filename in fnmatch.filter(filenames, "*.{}".format(extension)):
                logging.debug("Found file {}".format(filename))
                files.append(os.path.join(root, filename))
            if not recurse:
                logging.debug("Directory recursion set to: {}".format(recurse))
                break
        return files


    def get_ytdl_bin(self, ytdl_bin=None):
        """
        Get the path to the 'youtube-dl' binary. First check that the file
        exists, and then if it does check that it is executable.

        Args:
            ytdl_bin (str): Path to youtube-dl binary. Defaults to None.

        Returns:
            Returns the absolute path of 'youtube-dl' as a string.
        """
        # TODO: shutil.which is available in >= python-3.4, this method should
        # probably be updated to be backwards compatible with olders versions
        # of python3.
        ytdl_bin = ytdl_bin or shutil.which('youtube-dl')
        if os.path.isfile(ytdl_bin):
            if os.access(ytdl_bin, os.X_OK):
                msg = "youtube-dl binary defined as {}".format(ytdl_bin)
                logging.debug(msg)
                return ytdl_bin
            else:
                msg = "{} is not executable: {}".format(ytdl_bin)
                raise RadioRedditErr(msg)
        msg = "File not found: {}".format(ytdl_bin)
        raise RadioRedditErr(msg)


    def listing_url(self, subreddit, api_uri=None, listing_type=None):
        """
        Get the URL for a specific listing in a subreddit by listing type.

        Args:
            api_uri (str): Reddit API URI, defaults to None.
            listing_type (str): Type of listing query to perform, defaults to
                'random'.
            subreddit (str): Name of subreddit to fetch listing from.

        Returns:
            Returns the URL for a listing as a string.
        """
        api_uri = api_uri or self.api_uri(api_uri)
        listing_data = self.listing_data(subreddit, api_uri, listing_type)
        try:
            listing_url = listing_data['url']
            logging.debug("Found listing URL {}".format(listing_url))
            return listing_url
        except Exception as e:
            msg = "Unable to determine listing URL from {}".format(listing_data,
                                                                   e)
            raise RadioRedditErr(msg)
            

    def listing_data(self, subreddit, api_uri=None, listing_type=None):
        """
        Get the data for a specific listing in a subreddit by listing type.

        Args:
            api_uri (str): Reddit API URI, defaults to None.
            listing_type (str): Type of listing query to perform, defaults to
                'random'.
            subreddit (str): Name of subreddit to fetch listing from.

        Returns:
            Returns a dict describing the listing.
        """
        api_uri = api_uri or self.api_uri(api_uri)
        listing_type = listing_type or self.default_listing_type
        subreddit_data = self.subreddit_data(subreddit, api_uri, listing_type)
        msg = "Indexing into {} listing data for {}.".format(listing_type,
                                                             subreddit)
        if listing_type == 'random':
            listing_data = subreddit_data[0]['data']['children'][0]['data']
        elif listing_type == 'top': 
            listing_data = subreddit_data['data']['children'][0]['data']
        else:
            msg = "Listing type {} not supported.".format(listing_type)
            raise RadioRedditErr(msg)
        return listing_data


    def mk_mp3_dir(self, mp3_dir):
        """
        Make the given mp3 directory.

        Args:
            mp3_dir (str): Directory to write mp3 files out to.

        Returns:
            Attempts to create the given directory; returns the directory name
            as a string if successful.
        """
        msg = "Attempting to create {}".format(mp3_dir)
        logging.debug(msg)
        try:
            os.makedirs(mp3_dir, exist_ok=True)
            logging.debug("Created directory {}".format(mp3_dir))
            return mp3_dir
        except Exception as e:
            msg = "Failed to create {}: {}".format(mp3_dir, e)
            raise RadioRedditErr(msg)


    def mp3_dir(self, mp3_dir):
        """
        Get the mp3 directory for writing mp3s out to.

        Args:
            mp3_dir (str): Directory to write mp3 files out to.

        Returns:
            Returns the mp3 directory as a string.
        """
        msg = "Destination directory defined as {}".format(mp3_dir)
        logging.debug(msg)
        return mp3_dir


    def mp3_dir_exists(self, mp3_dir, create_mp3_dir=True):
        """
        Check if the mp3 directory exists. If 'create_mp3_dir' is True,
        and the mp3 dir does not exist, then attempt to create it.

        Args:
            create_mp3_dir (bool): A boolean controlling whether or not to
                create mp3 dirs if they don't exist. Defaults to True.
            mp3_dir (str): Directory to write mp3 files out to.

        Returns:
            Returns a boolean; True if the mp3 dir exists or was created
            if it didn't exist, False if the mp3 dir does not exist or
            was not created.           
        """
        if not os.path.isdir(mp3_dir):
            msg = "Destination directory {} does not exist.".format(mp3_dir)
            logging.error(msg)
            if create_mp3_dir:
                self.mk_mp3_dir(mp3_dir)
                return True
        return False


    def pls_file(self, mp3_dir=None, pls_file=None):
        """
        Get the name of the playlist file. 

        Args:
            mp3_dir (str): Directory to write mp3 files out to.
            pls_file (str): Path of the playlist file to be created.
            overwrite (bool): Boolean governing whether to overwrite an existing
                playlist file. Defaults to True.
            recurse (bool): Boolean governing whether to recursively search
                subdirs of the mp3 dir.

        Returns:
            Returns the playlist as a string.
        """
        mp3_dir = mp3_dir or self.mp3_dir(mp3_dir)
        pls_file = pls_file or "{}/{}.pls".format(mp3_dir,
                                                  os.path.basename(mp3_dir))
        logging.debug("Playlist file defined as {}".format(pls_file))
        return pls_file


    def subreddit_data(self, subreddit, api_uri=None, listing_type=None):
        """
        Get subreddit data by listing type. The Reddit listing API is described
        here:

        https://www.reddit.com/dev/api/#section_listings

        Args:
            api_uri (str): Reddit API URI, defaults to None.
            listing_type (str): Type of listing query to perform, defaults to
                'random'.
            subreddit (str): Name of subreddit to fetch listing from.

        Returns:
            Returns a dict describing the listing.
        """
        api_uri = api_uri or self.api_uri(api_uri)
        url = self.subreddit_url(subreddit, api_uri, listing_type)
        user_agent = "RadioReddit/{}".format(uuid.uuid4().hex)
        logging.debug("User-agent defined as {}".format(user_agent))
        headers = { 'User-Agent' : user_agent }
        try:
            logging.debug("Opening request to {}".format(url))
            req = urllib.request.Request(url, headers=headers)
            logging.debug("Reading response from {}".format(url))
            response = urllib.request.urlopen(req).read().decode()
        except Exception as e:
            msg = "Unable to fetch response from {}: {}".format(url, e)
            raise RadioRedditErr(msg)
        try:
            logging.debug("Loading JSON data from {}".format(url))
            return json.loads(response)
        except Exception as e:
            msg = "Unable to decode JSON response from {}: {}".format(url, e)
            raise RadioRedditErr(msg)


    def subreddit_url(self, subreddit, api_uri=None, listing_type=None):
        """
        Get the subreddit url for listings.

 
        Args:
            api_uri (str): Reddit API URI, defaults to None.
            listing_type (str): Type of listing query to perform, defaults to
                'random'.
            subreddit (str): Name of subreddit to fetch listing from.

        Returns:
            Returns the subreddit listing URL as a string, ex.
            'https://www.reddit.com/r/all/random.json'.
        """
        api_uri = api_uri or self.api_uri(api_uri)
        listing_type = listing_type or self.default_listing_type
        msg = "Getting URL for {} posts in subreddit {}".format(listing_type,
                                                                subreddit)
        logging.debug(msg)
        # TODO: Add additional parameters to pass to top.json.
        url = "{}/r/{}/{}.json".format(api_uri, subreddit, listing_type)
        msg = "URL for subreddit {} defined as {}".format(subreddit, url)
        logging.debug(msg)
        return url


    def ytdl_cmd(self, url, mp3_dir, ytdl_bin=None):
        """
        Get a list defining the 'youtube-dl' command to be executed.

        Args:
            mp3_dir (str): Directory to write mp3 files out to.
            ytdl_bin (str): Path to youtube-dl binary.

        Returns:
            Returns a list where the first element is the absolute path to
            'youtube-dl', and subsequent elements are arguments to the command.
        """
        ytdl_bin = ytdl_bin or self.ytdl_bin
        ytdl_cmd = [
            ytdl_bin,
            '--audio-format=mp3',
            '--extract-audio',
            '--output={}/%(title)s.%(ext)s'.format(mp3_dir),
            '--restrict-filenames',
            '--verbose',
            url
        ]
        msg = "youtube-dl command defined as: {}".format(' '.join(ytdl_cmd))
        logging.debug(msg)
        return ytdl_cmd
