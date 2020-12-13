# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Hypothes.is connection logic.

This module provides Python interfaces to the Hypothes.is groups and
annotations APIs.
"""

import json
from typing import Any, List, Mapping, Union

import log  # type: ignore
import requests

HYP_BASE_URL: str = "https://hypothes.is/api"


def get_group_by_name(key: str, name: str) -> Union[Mapping[str, Any], None]:
    """Search for a group in Hypothes.is by name, and return its data.

    Args:
        key (str): Hypothes.is API key.
        name (str): Name of the annotation group (case-sensitive).

    Returns:
        Union[dict, None]: A dictionary containing data for the group, if it
        is found; or None, if the group does not exist in the given permission
        space.

    Raises:
        requests.HTTPError: If the request returns an error
    """
    log.info("Requesting a list of annotation groups...")
    # define request
    endpoint: str = HYP_BASE_URL + "/groups"
    headers: Mapping[str, str] = {"Authorization": "Bearer " + key}
    groups_response: requests.Response = requests.get(
        endpoint,
        headers=headers,
    )
    # check response status
    if groups_response.status_code != 200:
        log.error(
            "Failed to get a list of Hypothes.is group. Error "
            + str(groups_response.status_code)
        )
        raise requests.HTTPError
    # get groups in response and compare their names with the targeted one
    groups: List = groups_response.json()
    log.info(
        f"{len(groups)} groups returned. "
        + "Checking names to see if any matches..."
    )
    for group in groups:
        if group["name"] == name:
            log.info(f"Found {name} group (id {group['id']}).")
            return group
    log.warn(f"No group named '{name}' was found in this account.")
    return None


def get_annotations(key: str = "", **payload) -> List[Mapping[str, Any]]:
    """Search annotations.

    Args:
        key: Hypothes.is API key.
        **kwargs: Additional parameters for searching annotations, as defined
        in <https://h.readthedocs.io/en/latest/api-reference/>.

    Returns:
        List[dict]:  A list of annotations that match the specified parameters.
    """
    log.info("Requesting the list of annotations...")
    # define request
    endpoint: str = HYP_BASE_URL + "/search"
    headers: Mapping[str, str] = {"Authorization": "Bearer " + key}
    annotations_response: requests.Response = requests.get(
        endpoint,
        payload,
        headers=headers,
    )
    log.debug("Request body: " + json.dumps(annotations_response.request.body))
    # check response status
    if annotations_response.status_code != 200:
        log.error(
            "Failed to get a list of annotations. Error "
            + str(annotations_response.status_code)
        )
        raise requests.HTTPError
    # get groups in response and compare their names with the targeted one
    total: int = annotations_response.json()["total"]
    log.info(f"Found {total} annotations.")
    annotations: List = annotations_response.json()["rows"]
    log.debug(f"Unpacked {len(annotations)}/{total} annotations.")
    sort: str = payload.get("sort", "updated")
    order: str = payload.get("order", "desc")
    limit: int = payload.get("limit", 20)
    while len(annotations) < total:
        if order == "asc":
            payload["search_after"] = max([a[sort] for a in annotations])
            log.debug(
                f"Requesting next {limit} annotations {sort} after "
                + f"{payload['search_after']}..."
            )
        elif order == "desc":
            payload["search_after"] = min([a[sort] for a in annotations])
            log.debug(
                f"Requesting next {limit} annotations {sort} before "
                + f"{payload['search_after']}..."
            )
        response: requests.Response = requests.get(
            endpoint,
            payload,
            headers=headers,
        )
        annotations += response.json()["rows"]
        log.debug(f"Unpacked {len(annotations)}/{total} annotations.")
    return annotations
