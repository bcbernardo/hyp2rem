# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""RemNote upload logic.

This module provides Python interfaces to upload Rem's to the RemNote backend
API.

Warning:
    RemNote's API is currently unstable (v0), and can break at any time. Check
    the API documentation (<https://www.remnote.io/api>) and release updates
    (<https://www.remnote.io/updates>) for possible changes that may cause this
    module to became inoperative.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, List, NewType, Optional, Union

import log  # type: ignore
import requests

REM_BASE_URL: str = "https://api.remnote.io/api/v0"


RemId = NewType("RemId", str)
"""Rem Id's are alphanumeric strings generated automatically by RemNote."""


class RemType(Enum):
    """Enumeration of possible Rem types"""

    concept: str = "concept"
    descriptor: str = "descriptor"
    no_content: str = "no_content"


@dataclass
class Rem:
    """Data representation of a RemNote Rem."""

    rem_id: RemId
    children: List[RemId]
    name: List[Any]
    name_md: str
    content: List[Any]
    content_md: str
    source: List[str]
    rem_type: RemType
    is_document: bool
    visible_in: List[RemId]
    updated: datetime
    created: datetime
    tags: List[RemId]
    tag_children: List[RemId]
    parent: Optional[RemId] = None


def get_rem_by_id(
    api_key: str, user_id: str, rem_id: RemId
) -> Union[Rem, None]:
    """Get a Rem by its ID."""
    log.info(f"Searching Rem (Id '{rem_id}')...'")
    # define request
    endpoint = REM_BASE_URL + "/get"
    data = {
        "apiKey": api_key,
        "userId": user_id,
        "remId": rem_id,
    }
    # post data
    response = requests.post(endpoint, data)
    # check response status
    if response.status_code != 200:
        log.error("Failed to fetch Rem. Error " + str(response.status_code))
        raise requests.HTTPError
    try:
        response_body = response.json()
        assert response_body["found"]
    except (KeyError, AssertionError):
        log.error(f"No Rem found with Id '{rem_id}' in current scope.")
        return None
    log.debug(json.dumps(response_body))
    rem = Rem(
        rem_id=response_body["_id"],
        parent=response_body.get("parent"),
        children=response_body["children"],
        name=response_body["name"],
        name_md=response_body["nameAsMarkdown"],
        content=response_body.get("content", ""),
        content_md=response_body.get("contentAsMarkdown", ""),
        source=response_body["source"],
        rem_type=RemType(response_body["remType"]),
        is_document=response_body["isDocument"],
        visible_in=response_body["visibleRemOnDocument"],
        updated=datetime.fromtimestamp(response_body["updatedAt"] / 1000),
        created=datetime.fromtimestamp(response_body["createdAt"] / 1000),
        tags=response_body["tagParents"],
        tag_children=response_body["tagChildren"],
    )
    log.debug(f"Found Rem: '{rem.name}', id '{rem.rem_id}'.")
    return rem


def get_rem_by_name(
    api_key: str,
    user_id: str,
    name: str,
    parent_id: Optional[RemId] = None,
) -> Union[Rem, None]:
    """Get a Rem by its name."""
    log.info(f"Searching Rem (name '{name}')...'")
    # define request
    endpoint = REM_BASE_URL + "/get_by_name"
    data = {
        "apiKey": api_key,
        "userId": user_id,
        "name": name,
        "parentId": parent_id,
    }
    # post data
    response = requests.post(endpoint, data)
    # check response status
    if response.status_code != 200:
        log.error("Failed to fetch Rem. Error " + str(response.status_code))
        raise requests.HTTPError
    try:
        response_body = response.json()
        assert response_body["found"]
    except (KeyError, AssertionError):
        log.error(f"No Rem found with name '{name}' in current scope.")
        return None
    log.debug(json.dumps(response_body))
    rem = Rem(
        rem_id=response_body["_id"],
        parent=response_body.get("parent"),
        children=response_body["children"],
        name=response_body["name"],
        name_md=response_body["nameAsMarkdown"],
        content=response_body.get("content", ""),
        content_md=response_body.get("contentAsMarkdown", ""),
        source=response_body["source"],
        rem_type=RemType(response_body["remType"]),
        is_document=response_body["isDocument"],
        visible_in=response_body["visibleRemOnDocument"],
        updated=datetime.fromtimestamp(response_body["updatedAt"] / 1000),
        created=datetime.fromtimestamp(response_body["createdAt"] / 1000),
        tags=response_body["tagParents"],
        tag_children=response_body["tagChildren"],
    )
    log.debug(f"Found Rem: '{rem.name}', id '{rem.rem_id}'.")
    return rem


def create_rem(
    api_key: str,
    user_id: str,
    text: str,
    parent: Optional[str] = None,
    position: Optional[int] = None,
    edit_later: Optional[bool] = None,
    is_document: Optional[bool] = None,
    source: Optional[str] = None,
) -> RemId:
    """Create a new Rem from provided data, and return its ID."""
    log.info(f"Creating new Rem: '{text[0:16]}...'")
    # define request
    endpoint = REM_BASE_URL + "/create"
    data = {
        "apiKey": api_key,
        "userId": user_id,
        "text": text,
        "parentId": parent,
        "positionAmongstSiblings": position,
        "addToEditLater": edit_later,
        "isDocument": is_document,
        "source": source,
    }
    data = {key: value for (key, value) in data.items() if value is not None}
    print(data)
    # post data
    response = requests.post(endpoint, data)
    # check response status
    if response.status_code != 200:
        log.error("Failed to create Rem. Error " + str(response.status_code))
        raise requests.HTTPError
    rem_id: RemId = response.json()["remId"]
    log.debug(f"Created Rem (Id {rem_id})")
    return rem_id


def update_rem(
    api_key: str,
    user_id: str,
    rem_id: RemId,
    parent: Optional[str] = None,
    name: Optional[str] = None,
    content: Optional[str] = None,
    source: Optional[str] = None,
) -> RemId:
    """Update a Rem from provided data, and return its ID."""
    log.info(f"Updating Rem (Id {rem_id})...'")
    # define request
    endpoint = REM_BASE_URL + "/update"
    data = {
        "apiKey": api_key,
        "userId": user_id,
        "remId": rem_id,
        "parent": parent,
        "name": name,
        "content": content,
        "source": source,
    }
    # post data
    response = requests.post(endpoint, data)
    # check response status
    if response.status_code != 200:
        log.error("Failed to update Rem. Error " + str(response.status_code))
        raise requests.HTTPError
    log.debug("Updated Rem successfully.")
    return rem_id


def delete_rem(
    api_key: str,
    user_id: str,
    rem_id: RemId,
) -> None:
    """Delete a Rem."""
    log.info(f"Deleting Rem (Id {rem_id})...'")
    # define request
    endpoint = REM_BASE_URL + "/delete"
    data = {"apiKey": api_key, "userId": user_id, "remId": rem_id}
    # post data
    # !!!
    # BUG: won't work. '500 Internal server error'
    response = requests.post(endpoint, data)
    # check response status
    if response.status_code != 200:
        log.error("Failed to delete Rem. Error " + str(response.status_code))
        raise requests.HTTPError
    log.debug(f"Deleted Rem with Id '{rem_id}'.")
