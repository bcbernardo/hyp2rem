# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Hypothes.is connection logic.

This module provides Python interfaces to the Hypothes.is groups and
annotations APIs.
"""

import functools
import json
from datetime import datetime
from logging import info
from typing import Any, List, Literal, Mapping, Optional, Union

import log  # type: ignore

# pylint: disable=no-name-in-module
from pydantic import AnyUrl, HttpUrl, validate_arguments
from pylru import lrucache, lrudecorator
from requests import HTTPError, Response, Session
from requests.auth import HTTPBasicAuth

from hyp2rem.exceptions import MissingAuthorizationTokenError
from hyp2rem.hypothesis.models import (
    Annotation,
    AnnotationId,
    ApiKey,
    ClientId,
    ClientSecret,
    Document,
    Group,
    GroupId,
    MimeType,
    Permissions,
    Target,
    UserId,
    UserProfile,
)
from hyp2rem.utils import HTTPBearerAuth


class HypothesisV1Client(object):
    """Client for Hypothes.is Annotations API (v1).

    Args:
        group_name: An optional name of the group to filter annotations by.
        key: A developer token for accessing the Hypothes.is API
        client_id: An OAuth-generated ClientId.
        client_secret: An OAuth-generated ClientSecret.
        **kwargs: Additional parameters for the ``search_annotations`` method.

    Note:
        You must provide either a ``key``, or a ``client_id`` and
        ``client_secret`` pair in order to authorize requests to the server.

    Attributes:
        annotations: A list of ``Annotation`` objects representing the
    """

    base_url: HttpUrl = "https://hypothes.is/api"
    media_type: MimeType = MimeType("application/vnd.hypothesis.v1+json")

    def __init__(
        self,
        group_name: Optional[str] = None,
        key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        **kwargs,
    ):

        # set up session with authorization scheme
        self._session: Session = Session()
        self._session.headers["Accept"] = HypothesisV1Client.media_type
        self._set_auth_scheme(key, client_id, client_secret)

        # a custom implementation of LRU Cache is necessary for memoizing the
        # annotations retrived by `search_annotations()` method.
        self._annotation_cache = lrucache(256)

        # retrieve annotations for given kwargs
        if group_name is not None:
            group = self.get_group_by_name(group_name)
        self.annotations: List[Annotation] = self.search_annotations(
            group_id=group.group_id, **kwargs
        )

    def _set_auth_scheme(
        self,
        key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        """Set authentication scheme object for use with Requests package.

        Raises:
            TypeError: If credentials are neither a ``key`` or a pair of
            ``client_id`` and ``client_secret`` were provided.
        """

        auth: Union[HTTPBearerAuth, HTTPBasicAuth]

        # authenticate with a personal token
        if key:
            auth = HTTPBearerAuth(ApiKey(key))

        # authenticate with Basic Auth
        elif client_id and client_secret:
            auth = HTTPBasicAuth(
                ClientId(client_id), ClientSecret(client_secret)
            )

        # no credentials provided
        else:
            log.error(
                "Missing authorization credentials. "
                + "Please provide either a `key` parameter, "
                + "or both a `client_id` and a `client_user`."
            )
            raise MissingAuthorizationTokenError

        # set authentication scheme
        self._session.auth = auth

    @functools.cached_property
    def user_profile(self) -> UserProfile:
        """Fetch profile information for the currently-authenticated useresponse."""
        # pylint: disable=attribute-defined-outside-init

        endpoint: HttpUrl = HypothesisV1Client.base_url + "/profile"
        response: Response = self._session.get(endpoint)
        user_profile = UserProfile(**response.json())
        return user_profile

    @validate_arguments
    def get_group_by_name(self, name: str) -> Union[Group, None]:
        """Search for a group in Hypothes.is by name, and return its data.

        Parameters:
            name: Name of the annotation group (case-sensitive).

        Returns:
            A ``Group`` object containing the representation of the group, if
            it is found; or None, if the group does not exist in the given
            permission space.
        """

        target_group: Optional[Group] = None
        for group in self.groups:
            if group.name == name:
                log.debug(f"Found {name} group (id {group.group_id}).")
                target_group = group
        log.warn(f"No group named '{name}' was found in this account.")
        return target_group

    @functools.cached_property
    def groups(self):
        """List of Hypothes.is ``Groups`` that this account has access to."""
        log.debug("Requesting a list of annotation groups...")
        # define request
        endpoint: HttpUrl = HypothesisV1Client.base_url + "/groups"
        response: Response = self._session.get(endpoint)
        # check response status
        if response.status_code != 200:
            log.error(
                "Failed to get a list of Hypothes.is group. "
                + f"Error {response.status_code}"
            )
            raise HTTPError
        # unpack and validate groups in response
        groups: List[Group] = [
            Group(**group_dict) for group_dict in response.json()
        ]
        log.debug(f"Got {len(groups)} groups.")

        return groups

    def create_group(
        self,
        name: str,
        description: Optional[str] = None,
        authority_group_id: Optional[GroupId] = None,
    ) -> Group:
        """Create a new, private group for the currently-authenticated user."""

        # post request to create a new group
        log.debug(f"Creating group '{name}'...")
        endpoint: HttpUrl = HypothesisV1Client.base_url + "/groups"
        response: Response = self._session.post(
            endpoint,
            data={
                "name": name,
                "description": description,
                "groupid": authority_group_id,
            },
        )

        # check response status
        if response.status_code != 200:
            log.error(f"Failed to create group. Error {response.status_code}")
            raise HTTPError

        # return group
        return Group(**response.json())

    @lrudecorator(256)
    @validate_arguments
    def search_annotations(
        self,
        any_of: Optional[str] = None,
        group_id: Optional[GroupId] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        order: Literal["asc", "desc"] = "asc",
        quote: Optional[str] = None,
        references: Optional[AnnotationId] = None,
        search_after: Optional[datetime] = None,
        sort: Literal["created", "updated"] = "created",
        tag: Optional[str] = None,
        tags: Optional[List[str]] = None,
        text: Optional[List] = None,
        uri: Optional[AnyUrl] = None,
        uri_parts: Optional[str] = None,
        url: Optional[AnyUrl] = None,
        user: Optional[UserId] = None,
        wildcard_uri: Optional[str] = None,
    ) -> List[Annotation]:
        """Search annotations.

        Returns:
            A list of annotations that match the specified parameters.
        """
        log.debug("Requesting the list of annotations...")

        # make request for first batch of annotations
        if search_after:
            search_after = search_after.isoformat()
        payload = {
            "any": any_of,
            "limit": limit,
            "offset": offset,
            "order": order,
            "quote": quote,
            "references": references,
            "search_after": search_after,
            "sort": sort,
            "tag": tag,
            "tags": tags,
            "text": text,
            "group": group_id,
            "uri": uri,
            "uri_parts": uri_parts,
            "url": url,
            "user": user,
            "wildcard_uri": wildcard_uri,
        }
        endpoint: HttpUrl = HypothesisV1Client.base_url + "/search"
        response: Response = self._session.get(endpoint, params=payload)

        # check response status
        if response.status_code != 200:
            log.error(
                f"Failed to get a list of annotations. Error {response.status_code}"
            )
            raise HTTPError

        # define total number of annotations
        total: int = response.json()["total"]
        log.debug(f"Found {total} annotations.")

        # unpack annotations in response
        annotations: List[Annotation] = [
            Annotation(context=self, **row) for row in response.json()["rows"]
        ]
        log.debug(f"Unpacked {len(annotations)}/{total} annotations.")

        # make new requests until all annotations are retrieved
        while len(annotations) < total:
            if order == "asc":
                search_after = max(getattr(a, sort) for a in annotations)
                log.debug(
                    f"Requesting next {limit} annotations {sort} after "
                    + f"{search_after}..."
                )
            elif order == "desc":
                search_after = min(getattr(a, sort) for a in annotations)
                log.debug(
                    f"Requesting last {limit} annotations {sort} before "
                    + f"{search_after}..."
                )
            payload["search_after"] = search_after
            response: Response = self._session.get(endpoint, data=payload)
            log.debug("Request body: " + json.dumps(response.request.body))
            annotations += [
                Annotation(context=self, **row)
                for row in response.json()["rows"]
            ]
            log.debug(f"Unpacked {len(annotations)}/{total} annotations.")

        # add retrieved annotations to cache
        for annotation in annotations:
            self._annotation_cache[annotation.annotation_id] = annotation

        # return
        return annotations

    @validate_arguments
    def get_annotation_by_id(
        self, annotation_id: AnnotationId
    ) -> Union[Annotation, None]:
        """Fetch a single annotation by its id.

        Returns:
            An Annotation object representing the retrived annotation; or None,
            if no annotation was found in the current scope.
        """
        log.debug(f"Searching annotation #{annotation_id}...")

        # search in custom cache
        try:
            annotation = self._annotation_cache[annotation_id]
            log.debug(f"Found annotation: '{annotation.text[0:10]}...'")
            return annotation
        except KeyError:
            # not in cache
            log.debug("Annotation not in cache; requesting from server...")

        # make request to Hypothes.is API
        endpoint: HttpUrl = HypothesisV1Client + "/annotations/"
        response: Response = self._session.get(endpoint + annotation_id)

        # check response status
        if response.status_code == 200:
            # found desired annotation
            log.debug(f"Found annotation: '{annotation.content[0,20]}...'")
            annotation: Annotation = Annotation(
                context=self, **response.json()
            )

            # save in cache and return
            self._annotation_cache[annotation.annotation_id] = annotation
            return annotation

        elif response.status_code == 404:
            # annotation does not exist, or is forbidden for current user
            log.warn(f"No annotation with id #{annotation_id} found in scope.")

        else:
            # some other error
            log.error(
                f"Failed to get a list of annotations. Error {response.status_code}"
            )
            raise HTTPError

    @validate_arguments
    def create_annotation(
        self,
        uri: AnyUrl,
        document: Optional[Document] = None,
        text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        group: Optional[GroupId] = None,
        permissions: Optional[Permissions] = None,
        target: Optional[Target] = None,
        references: Optional[List[AnnotationId]] = None,
    ) -> Annotation:
        """Create a new annotation with provided parameters.

        Note:
            While the API accepts arbitrary Annotation selectors in the
            ``target.selector`` property, the Hypothesis client currently
            supports ``TextQuoteSelector``, ``RangeSelector`` and
            ``TextPositionSelector`` selectors.

        Returns:
            The created `Annotation`_ object.
        """

        # post a request to Hypothes.is creating the annotation
        log.debug(f"Creating annotation: '{text[0:20]}...'")
        endpoint: HttpUrl = HypothesisV1Client + "/annotations"
        data: Mapping[str, Any] = {
            "uri": uri,
            "document": document.dict(),
            "text": text,
            "tags": tags,
            "group": group,
            "permissions": permissions.dict(),
            "target": target.dict(include="selector"),
            "references": references,
        }
        response: Response = self._session.post(endpoint, data)

        # check response status
        if response.status_code != 200:
            log.error(
                f"Failed to get a list of annotations. Error {response.status_code}"
            )
            raise HTTPError
            # found desired annotation

        annotation: Annotation = Annotation(context=self, **response.json())
        log.debug(f"Annotation created with id #{response.json()['id']}")

        # save in cache and return
        self._annotation_cache[annotation.annotation_id] = annotation
        return annotation
