#!/usr/bin/env python3

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


    def create_mp3(self, url, dest_dir, ytdl_bin=None, create_dest_dir=True):
        """
        Call 'youtube-dl' to create an mp3 from a URL. Write the mp3 out to
        the given destination directory.

        Args:
            create_dest_dir (bool): A boolean controlling whether or not to
                create destination dirs if they don't exist. Defaults to True.
            dest_dir (str): Directory to write mp3 files out to.
                None.
            url (str): URL to extract mp3 from.
            ytdl_bin (str): Path to youtube-dl binary.

        Returns:
            Returns the path to the mp3 file written out as a string.
        """
        dest_dir = dest_dir or self.dest_dir()
        ytdl_bin = ytdl_bin or self.ytdl_bin
        self.extractor_domain_is_supported(urllib.parse.urlsplit(url)[1])
        self.dest_dir_exists(dest_dir, create_dest_dir)
        ytdl_cmd = self.ytdl_cmd(url, dest_dir, ytdl_bin)
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


    def create_mp3_from_subreddit(self, subreddit, dest_dir, api_uri=None,
                                  create_dest_dir=True, ytdl_bin=None,
                                  listing_type=None):
        """
        Create an mp3 by fetching a listing URL from the given subreddit.

        Args:
            api_uri (str): Reddit API URI.
            create_dest_dir (bool): A boolean controlling whether or not to
                create destination dirs if they don't exist. Defaults to True.
            dest_dir (str): Directory to write mp3 files out to.
            listing_type (str): Type of listing query to perform, defaults to
                'random'.
            subreddit (str): Subreddit to extract mp3 from.
            ytdl_bin (str): Path to youtube-dl binary.

        Returns:
            Returns the path to the mp3 file written out as a string.
        """
        api_uri = api_uri or self.api_uri(api_uri)
        dest_dir = dest_dir or self.dest_dir()
        url = self.listing_url(subreddit, api_uri, listing_type)
        mp3 = self.create_mp3(url=url, create_dest_dir=create_dest_dir,
                              dest_dir=dest_dir, ytdl_bin=ytdl_bin)
        return mp3        


    def dest_dir(self, dest_dir):
        """
        Get the destination directory for writing mp3s out to.

        Args:
            dest_dir (str): Directory to write mp3 files out to.

        Returns:
            Returns the destination directory as a string.
        """
        msg = "Destination directory defined as {}".format(dest_dir)
        logging.debug(msg)
        return dest_dir


    def dest_dir_exists(self, dest_dir, create_dest_dir=True):
        """
        Check if the destination directory exists. If 'create_dest_dir' is True,
        and the destination dir does not exist, then attempt to create it.

        Args:
            create_dest_dir (bool): A boolean controlling whether or not to
                create destination dirs if they don't exist. Defaults to True.
            dest_dir (str): Directory to write mp3 files out to.

        Returns:
            Returns a boolean; True if the destination dir exists or was created
            if it didn't exist, False if the destination dir does not exist or
            was not created.           
        """
        if not os.path.isdir(dest_dir):
            msg = "Destination directory {} does not exist.".format(dest_dir)
            logging.error(msg)
            if create_dest_dir:
                self.mk_dest_dir(dest_dir)
                return True
        return False


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


    def get_ytdl_bin(self, ytdl_bin=None):
        """
        Get the path to the 'youtube-dl' binary. First check that the file
        exists, and then if it does check that it is executable.

        Args:
            ytdl_bin (str): Path to youtube-dl binary. Defaults to None.

        Returns:
            Returns the absolute path of 'youtube-dl' as a string.
        """

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


    def mk_dest_dir(self, dest_dir):
        """
        Make the given destination directory.

        Args:
            dest_dir (str): Directory to write mp3 files out to.

        Returns:
            Attempts to create the given directory; returns the directory name
            as a string if successful.
        """
        msg = "Attempting to create {}".format(dest_dir)
        logging.debug(msg)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            logging.debug("Created directory {}".format(dest_dir))
            return dest_dir
        except Exception as e:
            msg = "Failed to create {}: {}".format(dest_dir, e)
            raise RadioRedditErr(msg)


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


    def ytdl_cmd(self, url, dest_dir, ytdl_bin=None):
        """
        Get a list defining the 'youtube-dl' command to be executed.

        Args:
            dest_dir (str): Directory to write mp3 files out to.
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
            '--output={}/%(title)s.%(ext)s'.format(dest_dir),
            '--restrict-filenames',
            '--verbose',
            url
        ]
        msg = "youtube-dl command defined as: {}".format(' '.join(ytdl_cmd))
        logging.debug(msg)
        return ytdl_cmd
