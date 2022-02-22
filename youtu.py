#!/usr/bin/python

import httplib2
import os
import sys
import toml
import pickle
import argparse

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

config = toml.load(open('secret.toml'))['youtube-client']


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google API Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets


# download from Google Cloud Platform, credentials
CLIENT_SECRETS_FILE = config['CLIENT_SECRET_FILE']

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def insert_video_to_playlist(playlist_id, video_ids, logger=None):
    if logger is not None:
        logger.info('Now insert videos into playlist')
    youtube = _open_youtube_session()

    for video_id in video_ids:
        response = youtube.playlistItems().insert(
            part="snippet",
            body=dict(
                snippet=dict(
                    playlistId=playlist_id,
                    resourceId=dict(
                        kind="youtube#video",
                        videoId=video_id
                    )
                )
            )
        ).execute()

    if logger is not None:
        logger.debug(str(response))


def make_playlist(listname, logger=None):
    if logger is not None:
        logger.info('Now make playlist')

    youtube = _open_youtube_session()

    playlists_insert_response = youtube.playlists().insert(
      part="snippet,status",
      body=dict(
        snippet=dict(
          title=listname,
          description="Garie chan created this wonderful playlist"
        ),
        status=dict(
          privacyStatus="private"
        )
      )
    ).execute()

    if logger is not None:
        logger.debug(playlists_insert_response)

    return playlists_insert_response


def _get_credentials():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
      message=MISSING_CLIENT_SECRETS_MESSAGE,
      scope=YOUTUBE_READ_WRITE_SCOPE)

    OAUTH_TOKEN_JSON = config['OAUTH_TOKEN_JSON']

    storage = Storage(OAUTH_TOKEN_JSON)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flags = argparse.Namespace(noauth_local_webserver=True, logging_level='ERROR')
        credentials = run_flow(flow, storage, flags)

    return credentials


def _open_youtube_session():
    credentials = _get_credentials()

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
      http=credentials.authorize(httplib2.Http()))

    return youtube

if __name__ == '__main__':
    youtube = _open_youtube_session()
