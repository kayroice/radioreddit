# RadioReddit
> RadioReddit library and CLI util - RadioReddit is a wrapper around [[youtube-dl]](https://github.com/rg3/youtube-dl) that provides functionality for querying a subreddit, fetching a link, and creating an mp3 from that link.

## Requirements

* `youtube-dl`. Note that `Debian` `jessie` currently ships with version `2014.08.05`, in my testing did not work. Later versions of `youtube-dl` ship with better support for `avconv` and `avprobe`.

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

## Usage example

* 

```sh
$ radioreddit create -d /tmp/destinstaion_dir -s subreddit_name
```

## Release History

* 0.0.2
    * Update of `README.md`.
* 0.0.1
    * Initial release; includes basic functionality to query a subreddit and create an mp3.
