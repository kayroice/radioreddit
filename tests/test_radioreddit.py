import os
import pytest
import uuid


from radioreddit.radioreddit import RadioReddit
from radioreddit.radioreddit import RadioRedditErr

rr = RadioReddit()


def test_api_uri():
    api_uri = rr.api_uri()
    assert api_uri
    assert type(api_uri) == str


def test_extractor_domain_is_supported():
    domain = 'youtube.com'
    assert rr.extractor_domain_is_supported(domain=domain) == True


def test_extractor_domain_is_not_supported():
    domain = 'asdf.asdf'
    with pytest.raises(RadioRedditErr):
        rr.extractor_domain_is_supported(domain=domain)


def test_extractor_domains():
    extractor_domains = rr.extractor_domains()
    assert extractor_domains
    assert type(extractor_domains) == list
    assert len(extractor_domains) > 0


def test_get_ytdl_bin():
    ytdl_bin = rr.get_ytdl_bin()
    assert ytdl_bin
    assert type(ytdl_bin) == str


def test_listing_url():
    subreddit = 'jazznoir'
    listing_url = rr.listing_url(subreddit)
    assert listing_url
    assert type(listing_url) == str


def test_listing_data():
    subreddit = 'jazznoir'
    listing_data = rr.listing_data(subreddit)
    assert listing_data
    assert type(listing_data) == dict


def test_mk_mp3_dir():
    target_dirname = "/tmp/{}".format(uuid.uuid4().hex)
    dirname = rr.mk_mp3_dir(target_dirname)
    assert type(dirname) == str
    assert target_dirname == dirname
    os.rmdir(dirname)


def test_mp3_dir():
    target_dirname = '/path/to/mp3_dir'
    dirname = rr.mp3_dir(target_dirname)
    assert type(dirname) == str
    assert target_dirname == dirname


def test_mp3_dir_exists():
    dirname = '/'
    exists = rr.mp3_dir_exists(dirname, create_mp3_dir=False)
    assert type(exists) == bool
    assert exists == True


def test_mp3_dir_does_not_exist():
    dirname = '/DOES_NOT_EXIST'
    exists = rr.mp3_dir_exists(dirname, create_mp3_dir=False)
    assert type(exists) == bool
    assert exists == False


def test_pls_file():
    mp3_dir = '/tmp'
    pls_file = rr.pls_file(mp3_dir=mp3_dir)
    assert pls_file
    assert type(pls_file) == str


def test_subreddit_data():
    subreddit = 'jazznoir'
    subreddit_data = rr.subreddit_data(subreddit)
    assert subreddit_data
    assert type(subreddit_data) == dict


def test_subreddit_url():
    subreddit = 'jazznoir'
    subreddit_url = rr.subreddit_url(subreddit)
    assert subreddit_url
    assert type(subreddit_url) == str


def test_ytdl_cmd():
    url = 'https://extractor.domain/path/to/source'
    mp3_dir = '/path/to/mp3_dir'
    ytdl_bin = '/path/to/youtube-dl'
    ytdl_cmd = rr.ytdl_cmd(url, mp3_dir, ytdl_bin)
    assert ytdl_cmd
    assert type(ytdl_cmd) == list
    assert ytdl_cmd.index(ytdl_bin) == 0
    assert ytdl_cmd[-1] == url
