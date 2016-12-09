# RadioReddit
> RadioReddit library, CLI and webserver - RadioReddit is a wrapper around [youtube-dl](https://github.com/rg3/youtube-dl) that provides functionality for querying a subreddit, fetching a link, creating an mp3 from that link, and also serving out mp3s and playlist files.

## Requirements

* `youtube-dl`. Note that `Debian` `jessie` currently ships with version `2014.08.05`; in my testing this version did not work on `jessie` due to poor support for `avconv` and `avprobe`. Later versions of `youtube-dl` ship with better support for `avconv` and `avprobe`.

```sh
$ youtube-dl --version
2016.11.27
```

* `python3`.

```sh
$ python3 --version
Python 3.4.2
```

## Installation

* For now simply `curl` or `wget` the `radioreddit` lib and script to the directory of your choice.

```sh
$ curl https://github.com/kayroice/radioreddit/blob/master/radioreddit -o /path/to/rr/radioreddit ; chmod 755 /path/to/rr/radioreddit
$ curl https://github.com/kayroice/radioreddit/blob/master/radioreddit.py -o /path/to/rr/radioreddit.py
```

### Systemd config and usage for HTTP server.

* First, edit the value of `ExecStart` to reflect the absolute path to the `radioreddit` script.

```sh
$ grep ExecStart radioreddit-httpd.service 
ExecStart=/path/to/radioreddit/radioreddit httpd --start
```

* You may also want to change the user and group that radioreddit runs as:

```sh
$ egrep 'User|Group' radioreddit-httpd.service 
Group=nogroup
User=nobody
```

* Copy `radioreddit-httpd.service` to `/etc/systemd/system`.

```sh
# cp radioreddit-httpd.service /etc/systemd/system/
```

* Enable the service using `systemctl enable radioreddit-httpd`:

```sh
# systemctl enable radioreddit-httpd
```

* Updating the file after enabling it will require reloading the `systemd` daemon:

```sh
# sudo systemctl daemon-reload
```

* Start the service using `systemctl start radioreddit-httpd`:

```sh
# systemctl start radioreddit-httpd
```

* Check the status using `systemctl status radioreddit-http -l`

```sh
$ systemctl status radioreddit-httpd -l
```


## Usage example

### Create mode

* Create an mp3 in the destination directory `/tmp/mp3_dir` from the subreddit `subreddit_name`:

```sh
$ radioreddit create --mp3dir /tmp/mp3_dir --subreddit subreddit_name
```

* Create a playlist file named `my.pls` in `/tmp` by searching the directory `/tmp/mp3_dir` for mp3 files. The playlist file will specify the absolute path to the mp3 files, and is strictly for local streaming.

```sh
$ radioreddit create --playlist /tmp/my.pls --mp3dir /tmp/mp3_dir
```

* Create a playlist file with a URI for streaming mp3 files. The URI `http://$ip:$port/file=` specifies the path that is compatible with the RadioReddit HTTP server in order to remotely stream mp3 files.

```sh
$ radioreddit create --playlist /tmp/my.pls -mp3dir /tmp/mp3_dir -uri http://10.0.0.123:30080/file=
```

### HTTPd mode

* Start an HTTP server for serving out playlist and mp3 files.

```sh
$ radioreddit httpd --start
```

* Start an HTTP server and bind to a specific ip address and port. By default radioreddit's HTTP server will bind to `0.0.0.0:30080`.

```sh
$ radioreddit httpd --start --addr 10.0.0.123 --port 12345
```

## Release History

* 0.0.3
    * Added support for creating playlists, including a python based webserver to serve playlist files and mp3s.
* 0.0.2
    * Update of `README.md`.
* 0.0.1
    * Initial release; includes basic functionality to query a subreddit and create an mp3.
