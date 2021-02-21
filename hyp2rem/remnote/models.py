# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Hypothes.is object models.

This module provides dataclasses and pydantic models for the most relevant
objects exchanged in RemNote API (v0).

Warning:
    RemNote's API is currently unstable (v0), and can break at any time. Check
    the API documentation (<https://www.remnote.io/api>) and release updates
    (<https://www.remnote.io/updates>) for possible changes that may cause this
    module to became inoperative.
"""

from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Mapping, NewType, Optional, Union

import log

# pylint: disable=no-name-in-module
from pydantic import AnyUrl, BaseModel, PrivateAttr
from pydantic.error_wrappers import ValidationError

ApiKey = NewType("ApiKey", str)
"""A RemNote-provided secret key for interacting with their API."""

RemId = NewType("RemId", str)
"""Rem Id's are alphanumeric strings generated automatically by RemNote."""

UserId = NewType("UserId", str)
"""Unique alphanumeric identifier for a RemNote user."""

RichText = List[Union[str, Mapping[str, Any]]]  # TODO: enhance definition


class RemType(str, Enum):
    """Enumeration of possible Rem types"""

    concept: Literal["concept"] = "concept"
    descriptor: Literal["descriptor"] = "descriptor"
    no_content: Literal["no_content"] = "no_content"


class Rem(BaseModel):
    """Representation of a Rem returned by RemNote's V0 get_by_* methods."""

    children: List[RemId]
    created: datetime
    name: RichText
    name_md: str
    rem_id: RemId
    rem_type: RemType
    source: RichText
    tag_children: List[RemId]
    updated: datetime
    visible_in: List[RemId]
    content: Optional[RichText] = None
    content_md: Optional[str] = None
    is_document: bool = False
    parent: Optional[RemId] = None
    tags: Optional[List[RemId]] = None
    _source_urls: List[AnyUrl] = PrivateAttr([])

    def __init__(self, **data):
        for date_field in ["createdAt", "updatedAt"]:
            data[date_field] /= 1000  # milliseconds to seconds
        try:
            super().__init__(**data)
        except ValidationError:
            log.error("Error while validating Rem!")
            log.debug(str(data))
            raise

    class Config:
        """Pydantic scheme configuration."""

        fields = {
            "content_md": "contentAsMarkdown",
            "created": "createdAt",
            "is_document": "isDocument",
            "rem_id": "_id",
            "name_md": "nameAsMarkdown",
            "rem_type": "remType",
            "tag_children": "tagChildren",
            "updated": "updatedAt",
            "visible_in": "visibleRemOnDocument",
        }

    @property
    def source_urls(self) -> List[AnyUrl]:
        """URLs available in Rem's ``source`` attribute rich text."""
        source_urls: List[AnyUrl] = [
            component["url"]
            for component in self.source
            if isinstance(component, dict) and "url" in component
        ]
        self._source_urls: List[AnyUrl] = source_urls
        return self._source_urls
