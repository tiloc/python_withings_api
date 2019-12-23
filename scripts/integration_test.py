#!/usr/bin/env python3
"""Integration test."""
import argparse
from os import path
import pickle
from unittest.mock import MagicMock
from urllib import parse

import arrow
from withings_api import AuthScope, WithingsApi, WithingsAuth

CREDENTIALS_FILE = path.abspath(
    path.join(path.dirname(path.abspath(__file__)), "../.credentials")
)


def main() -> None:
    """Run main function."""
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--client-id",
        dest="client_id",
        help="Client id provided by withings.",
        required=True,
    )
    parser.add_argument(
        "--consumer-secret",
        dest="consumer_secret",
        help="Consumer secret provided by withings.",
        required=True,
    )
    parser.add_argument(
        "--callback-uri",
        dest="callback_uri",
        help="Callback URI configured for withings application.",
        required=True,
    )

    args = parser.parse_args()

    if path.isfile(CREDENTIALS_FILE):
        print("Using credentials saved in:", CREDENTIALS_FILE)
        with open(CREDENTIALS_FILE, "rb") as file_handle:
            credentials = pickle.load(file_handle)
    else:
        print("Attempting to get credentials...")
        auth = WithingsAuth(
            client_id=args.client_id,
            consumer_secret=args.consumer_secret,
            callback_uri=args.callback_uri,
            mode="demo",
            scope=(
                AuthScope.USER_ACTIVITY,
                AuthScope.USER_METRICS,
                AuthScope.USER_INFO,
                AuthScope.USER_SLEEP_EVENTS,
            ),
        )

        authorize_url = auth.get_authorize_url()
        print("Goto this URL in your browser and authorize:", authorize_url)
        print(
            "Once you are redirected, copy and paste the whole url"
            "(including code) here."
        )
        redirected_uri = input("Provide the entire redirect uri: ")
        redirected_uri_params = dict(
            parse.parse_qsl(parse.urlsplit(redirected_uri).query)
        )
        auth_code = redirected_uri_params["code"]

        print("Getting credentials with auth code", auth_code)
        credentials = auth.get_credentials(auth_code)
        with open(CREDENTIALS_FILE, "wb") as file_handle:
            pickle.dump(credentials, file_handle)

    refresh_cb = MagicMock()
    api = WithingsApi(credentials, refresh_cb=refresh_cb)

    print("Getting devices...")
    assert api.measure_get_meas() is not None

    print("Refreshing token...")
    refresh_cb.reset_mock()
    api.refresh_token()
    refresh_cb.assert_called_once()

    print("Getting measures...")
    assert (
        api.measure_get_meas(
            startdate=arrow.utcnow().shift(days=-21), enddate=arrow.utcnow()
        )
        is not None
    )

    print("Getting activity...")
    assert (
        api.measure_get_activity(
            startdateymd=arrow.utcnow().shift(days=-21), enddateymd=arrow.utcnow()
        )
        is not None
    )

    print("Getting sleep...")
    assert (
        api.sleep_get(startdate=arrow.utcnow().shift(days=-2), enddate=arrow.utcnow())
        is not None
    )

    print("Getting sleep summary...")
    assert (
        api.sleep_get_summary(
            startdateymd=arrow.utcnow().shift(days=-2), enddateymd=arrow.utcnow()
        )
        is not None
    )

    print("Getting subscriptions...")
    assert api.notify_list() is not None

    print("Successfully finished.")


if __name__ == "__main__":
    main()
