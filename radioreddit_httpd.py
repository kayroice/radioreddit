#!/usr/bin/env python3

import logging
import os
import urllib

from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn


class RadioRedditHandler(BaseHTTPRequestHandler):


    def close_conn(self):
        """
        Close the HTTP connection.
        """
        return http.server.close_request(httpserver.get_request())


    def do_GET(self):
        """
        Respond to a GET request.
        """
        dirname = None
        filename = None
        self.send_response(200)
        self.send_header('Content-type', 'audio/x-scpls')
        self.end_headers()
        qs = urllib.parse.parse_qs(urllib.parse.unquote(self.path))
        filename = self.get_filename_from_qs(qs)
        self.file_exists(filename)
        if filename.endswith('mp3'):
            self.wfile.write(self.get_file_contents(filename, mode='rb'))
        else:
            self.wfile.write(self.get_file_contents(filename).encode())
        self.close_conn()


    def do_HEAD(self):
        """
        Send a generic HTTP header.
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


    def file_exists(self, filename):
        """
        Check whether the given file exists.

        Args:
            filename (str): Path to the file.

        Returns:
            Return True if the given file exists. Send a 404 and close the
            HTTP connection if it does not.
        """
        if not os.path.isfile(filename):
            self.send_error(404, "{} not found".format(filename))
            self.close_conn()
        return True


    def get_file_contents(self, filename, mode='r'):
        """
        Get the contents of a file.

        Args:
            filename (str): Path to the file.
            mode (str): Mode in which to open the file, defaults to 'r'.

        Returns:
            Returns the contents of a file. Sends a 404 if unable to read the
            file.
        """
        try:
            return open(filename, mode).read()
        except Exception as e:
            msg = "Unable to read {}: {}".format(filename, e)
            self.send_error(404, msg)
            self.close_conn()


    def get_filename_from_qs(self, qs):
        """
        Get the name of a file from the HTTP query string. The format of the
        query should be '/file=/path/to/filename'.

        Args:
            qs (dict): The HTTP query string as a dict.

        Returns:
            Returns the filename as a string.
        """
        try:
            return qs['/file'][0]
        except Exception as e:
            msg = "Expecting '/file=/path/to/filename': {}".format(self.path, e)
            self.send_error(404, msg)
            self.close_conn()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    '''Handle http requests in a separate thread.'''
