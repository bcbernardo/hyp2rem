# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""RemNote connection logic.

This module provides Python interfaces to create, read, update and delete Rems
using the RemNote backend API.
"""

from typing import Any, Mapping, Optional, Union

import log  # type: ignore

# pylint: disable=no-name-in-module
from pydantic import AnyUrl, HttpUrl, validate_arguments
from pylru import lrucache
from requests import HTTPError, Response, Session

from hyp2rem.remnote.models import ApiKey, Rem, RemId, UserId


class RemNoteV0Client(object):
    """Client for exchanging data with RemNote's V0 API.

    Args:
        key: RemNote client key/token for accessing the API.
        user_id: RemNote unique client id.

    Warning:
        RemNote's API is currently unstable (v0), and can break at any time.
        Check the API documentation (<https://www.remnote.io/api>) and release
        updates (<https://www.remnote.io/updates>) for possible changes that
        may cause this client to become inoperative.
    """

    base_url: HttpUrl = "https://api.remnote.io/api/v0"

    def __init__(
        self,
        key: str,
        user_id: str,
    ):
        # set requests Session and auth data
        self._session: Session = Session()
        self._key: ApiKey = ApiKey(key)
        self._user_id: UserId = UserId(user_id)

        self._rem_cache: lrucache = lrucache(256)

    @validate_arguments
    def get_rem_by_id(self, rem_id: RemId) -> Union[Rem, None]:
        """Get a Rem by its ID."""

        rem: Optional[Rem] = None

        log.debug(f"Searching Rem (Id '{rem_id}')...'")

        # search in cache
        try:
            rem = self._rem_cache[rem_id]
            assert rem
        except KeyError:
            pass
        else:
            log.debug(f"Got Rem: '{rem.name[0]}' (#{rem.rem_id}) from cache.")
            return rem

        # define request
        endpoint: HttpUrl = RemNoteV0Client.base_url + "/get"
        data = {
            "apiKey": self._key,
            "userId": self._user_id,
            "remId": rem_id,
        }
        # post data
        response: Response = self._session.post(endpoint, data)
        # check response status
        if response.status_code != 200:
            log.error(f"Failed to fetch Rem. Error {response.status_code}")
            raise HTTPError
        found = response.json().pop("found", False)
        if not found:
            log.warn(f"No Rem found with Id '{rem_id}' in current scope.")
        else:
            rem = Rem(**response.json())
            self._rem_cache[rem.rem_id] = rem  # add to cache
            log.debug(f"Got Rem: '{rem.name[0]}' (#{rem.rem_id}) from server.")
        return rem

    @validate_arguments
    def get_rem_by_name(
        self,
        name: str,
        parent_id: Optional[RemId] = None,
    ) -> Union[Rem, None]:
        """Get a Rem by its name."""

        rem: Optional[Rem] = None

        log.debug(f"Searching Rem (name '{name}')...'")

        # search in cache
        try:
            rem = next(
                rem
                for rem in self._rem_cache.values()
                if name in rem.name
                # NOTE: Rems usually have their texts altered by RemNote, and
                # should not match - even if the original name is identical
            )
            assert rem
            # force change in cache order
            self._rem_cache[rem.rem_id]  # pylint: disable=pointless-statement
        except StopIteration:
            pass
        else:
            log.debug(f"Got Rem: '{rem.name[0]}' (#{rem.rem_id}) from cache.")
            return rem

        # define request
        endpoint: HttpUrl = HttpUrl(RemNoteV0Client.base_url + "/get_by_name")
        data = {
            "apiKey": self._key,
            "userId": self._user_id,
            "name": name,
            "parentId": parent_id,
        }
        # post data
        response: Response = self._session.post(endpoint, data)
        # check response status
        if response.status_code != 200:
            log.error(f"Failed to fetch Rem. Error {response.status_code}")
            raise HTTPError
        found = response.json().pop("found", False)
        if not found:
            log.warn(f"No Rem found with name '{name}' in current scope.")
        else:
            rem = Rem(**response.json())
            self._rem_cache[rem.rem_id] = rem  # add to cache
            log.debug(f"Got Rem: '{rem.name[0]}' (#{rem.rem_id}) from server.")
        return rem

    @validate_arguments
    def get_rem_by_source(
        self,
        source: AnyUrl,
        parent_id: Optional[RemId] = None,
    ) -> Union[Rem, None]:
        """Get a Rem by the source URL it is linked to."""

        rem: Optional[Rem] = None

        log.debug(f"Searching Rem linked to source <{source}>)...'")

        # search in cache
        try:
            rem = next(
                rem
                for rem in self._rem_cache.values()
                if source in rem.source_urls
            )
            assert rem
            # force change in cache order
            self._rem_cache[rem.rem_id]  # pylint: disable=pointless-statement
        except StopIteration:
            pass
        else:
            log.debug(f"Got Rem: '{rem.name[0]}' (#{rem.rem_id}) from cache.")
            return rem

        # define request
        endpoint: HttpUrl = RemNoteV0Client.base_url + "/get_by_source_url"
        data = {
            "apiKey": self._key,
            "userId": self._user_id,
            "url": source,
            "parentId": parent_id,
        }
        # post data
        response: Response = self._session.post(endpoint, data)
        # check response status
        if response.status_code != 200:
            log.error(f"Failed to fetch Rem. Error {response.status_code}")
            raise HTTPError
        found = response.json().pop("found", False)
        if not found:
            log.warn(f"No Rem found with source <{source}> in current scope.")
        else:
            rem = Rem(**response.json())
            self._rem_cache[rem.rem_id] = rem  # add to cache
            log.debug(f"Got Rem: '{rem.name[0]}' (#{rem.rem_id}) from server.")
        return rem

    @validate_arguments
    def create_rem(
        self,
        text: str,
        parent_id: Optional[RemId] = None,
        position_amongst_siblings: Optional[int] = None,
        edit_later: Optional[bool] = None,
        is_document: Optional[bool] = None,
        source: Optional[str] = None,
    ) -> Rem:
        """Create a new Rem from provided data, and return its representation."""

        log.debug(f"Creating new Rem: '{text[0:16]}...'")

        # define request
        endpoint = RemNoteV0Client.base_url + "/create"
        data: Mapping[str, Any] = {
            "apiKey": self._key,
            "userId": self._user_id,
            "text": text,
            "parentId": parent_id,
            "positionAmongstSiblings": position_amongst_siblings,
            "addToEditLater": edit_later,
            "isDocument": is_document,
            "source": source,
        }
        data = {key: value for key, value in data.items() if value is not None}

        # post data
        response: Response = self._session.post(endpoint, data)

        # check response status
        if response.status_code != 200:
            log.error(f"Failed to create Rem. Error {response.status_code}")
            raise HTTPError

        # unpack retrieved id
        rem_id: RemId = response.json()["remId"]
        log.debug(f"Created Rem (Id {rem_id})")

        # retrieve full representation for created Rem
        self._rem_cache.pop(rem_id, None)  # clean previous records in cache
        rem: Rem = self.get_rem_by_id(rem_id)  # type: ignore

        return rem

    @validate_arguments
    def update_rem(
        self,
        rem_id: RemId,
        parent_id: Optional[RemId] = None,
        name: Optional[str] = None,
        content: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Rem:
        """Update a Rem from provided data, and return its representation."""

        log.debug(f"Updating Rem #{rem_id}...")

        # define request
        endpoint = RemNoteV0Client.base_url + "/update"
        data = {
            "apiKey": self._key,
            "userId": self._user_id,
            "remId": rem_id,
            "parent": parent_id,
            "name": name,
            "content": content,
            "source": source,
        }
        data = {key: value for key, value in data.items() if value is not None}

        # post data
        response: Response = self._session.post(endpoint, data)

        # check response status
        if response.status_code != 200:
            log.error(f"Failed to create Rem. Error {response.status_code}")
            raise HTTPError
        log.debug("Updated Rem successfully.")

        # retrieve full representation for updated Rem
        self._rem_cache.pop(rem_id, None)  # clean previous records in cache
        rem: Rem = self.get_rem_by_id(rem_id)  # type: ignore

        return rem

    def delete_rem(self, rem_id: RemId):
        """Delete a Rem."""

        log.debug(f"Deleting Rem #{rem_id}...'")

        # define request
        endpoint = RemNoteV0Client.base_url + "/delete"
        data = {"apiKey": self._key, "userId": self._user_id, "remId": rem_id}

        # post data
        # BUG: won't work. '500 Internal server error'
        response: Response = self._session.post(endpoint, data)

        # check response status
        if response.status_code != 200 and response != 204:
            log.error(f"Failed to delete Rem. Error {response.status_code}")
            raise HTTPError
        log.debug(f"Deleted Rem with Id '{rem_id}'.")

        # delete from cache
        self._rem_cache.pop(rem_id, None)
