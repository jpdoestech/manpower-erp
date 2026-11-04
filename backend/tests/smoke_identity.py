"""HTTP smoke against disposable Compose CI only; credentials come from CI env."""

import json
import os
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener


def main() -> None:
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    base = "http://127.0.0.1:5173/api/auth"
    body = json.dumps(
        {"username": "ci-user", "password": os.environ["ERP_CI_PASSWORD"]}
    ).encode()
    with opener.open(
        Request(
            base + "/login",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Origin": "http://127.0.0.1:5173",
            },
        ),
        timeout=10,
    ) as response:
        account = json.load(response)
        assert response.headers["Cache-Control"] == "no-store"
    with opener.open(base + "/me", timeout=10) as response:
        assert json.load(response)["id"] == account["id"]
    with opener.open(
        Request(
            base + "/logout",
            data=b"",
            headers={
                "X-CSRF-Token": account["csrf_token"],
                "Origin": "http://127.0.0.1:5173",
            },
        ),
        timeout=10,
    ) as response:
        assert response.status == 204
    try:
        opener.open(base + "/me", timeout=10)
    except HTTPError as error:
        assert error.code == 401
        error.close()
    else:
        raise AssertionError("Logged-out session remained usable")
    print("PASS: identity HTTP sign-in/me/logout/replay smoke")


if __name__ == "__main__":
    main()
