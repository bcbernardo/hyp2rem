# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Hypothes.is object models.

This module provides `Pydantic` models for the most relevant objects exchanged
in Hypothes.is API (v1). It also provides convenience properties that should
be useful when syncing to RemNote.

.. _Pydantic:
   https://pydantic-docs.helpmanual.io/

"""

from datetime import datetime
from operator import attrgetter
from typing import (
    ForwardRef,
    List,
    Literal,
    Mapping,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import log  # type: ignore

# pylint: disable=no-name-in-module
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, PrivateAttr
from pydantic.error_wrappers import ValidationError

AnnotationId = NewType("AnnotationId", str)
"""Unique identifier for a Hypothes.is annotation."""

ApiKey = NewType("ApiKey", str)
"""Personal access token for the Hypothes.is API."""

ClientId = NewType("ClientId", str)
"""OAuth-generated Client Id, for authorized applications."""

ClientSecret = NewType("ClientSecret", str)
"""OAuth-generated Client Secret, for authorized applications."""

DOI = NewType("DOI", str)


GroupId = NewType("GroupId", str)
"""Unique identifier for a Hypothes.is group."""

LinkType = NewType("LinkType", str)

MimeType = NewType("MimeType", str)

OrganizationId = NewType("OrganizationId", str)
"""Unique identifier for a organization registered in Hypothes.is."""

SupportedSelectorType = Literal[
    "RangeSelector", "TextPositionSelector", "TextQuoteSelector"
]

UserId = NewType("UserId", str)
"""Unique identifier for a Hypothes.is user."""

XPath = NewType("XPath", str)


class Permissions(BaseModel):
    """Permission settings for a Hypothes.is annotation."""

    read: List[Union[UserId, str]]
    admin: List[Union[UserId, str]]
    update: List[Union[UserId, str]]
    delete: List[Union[UserId, str]]


class RangeSelector(BaseModel):
    """Describes a range of text by using XPath and TextPosition Selectors."""

    selector_type: Literal["RangeSelector"] = "RangeSelector"
    start_container: XPath
    start_offset: int
    end_container: XPath
    end_offset: int

    class Config:
        fields = {
            "selector_type": "type",
            "start_container": "startContainer",
            "start_offset": "startOffset",
            "end_container": "endContainer",
            "end_offset": "endOffset",
        }


class TextPositionSelector(BaseModel):
    """Describes a range of text by the start and end positions in the stream."""

    selector_type: Literal["TextPositionSelector"] = "TextPositionSelector"
    start: int
    end: int

    class Config:
        fields = {"selector_type": "type"}


class TextQuoteSelector(BaseModel):
    """Describes a range of text by a copy of it, a prefix and a suffix."""

    selector_type: Literal["TextQuoteSelector"] = "TextQuoteSelector"
    exact: str
    prefix: str
    suffix: str

    class Config:
        fields = {"selector_type": "type"}


class Selector(BaseModel):
    """A generic class for selecting between multiple *Selector classes."""

    def __new__(cls, **data):
        selector_type: SupportedSelectorType = data["type"]
        if selector_type == "RangeSelector":
            return RangeSelector(**data)
        elif selector_type == "TextPositionSelector":
            return TextPositionSelector(**data)
        elif selector_type == "TextQuoteSelector":
            return TextQuoteSelector(**data)
        else:
            log.error(f"{selector_type} is not a supported selector.")
            return None


class Target(BaseModel):
    """Target webpage or document for a Hypothes.is annotation."""

    source: Optional[Union[AnyUrl, str]]  # TODO: better support for URN
    selector: Optional[List[Selector]] = None


class Links(BaseModel):
    """Hypermedia links for an annotation."""

    html: Optional[AnyHttpUrl] = None
    in_context: Optional[AnyHttpUrl] = None
    json_: Optional[AnyHttpUrl] = None

    class Config:
        fields = {"in_context": "incontext", "json_": "json"}


class UserInfo(BaseModel):
    """An annotation creator's information (display name)."""

    display_name: Optional[str]


class Moderation(BaseModel):
    flag_count: Optional[int]

    class Config:
        fields = {"flag_count": "flagCount"}


class DC(BaseModel):
    identifier: Optional[List[str]] = None


class Highwire(BaseModel):
    doi: Optional[List[DOI]] = None
    pdf_url: Optional[List[AnyUrl]] = None


class DocumentLink(BaseModel):
    href: Optional[AnyUrl] = None
    link_type: Optional[LinkType] = None

    class Config:
        fields = {"link_type": "type"}


class Document(BaseModel):
    title: Optional[List[str]] = None
    dc: Optional[DC] = None
    highwire: Optional[Highwire] = None
    link: Optional[DocumentLink] = None


class Annotation(BaseModel):
    """A Hypothes.is annotation.

    Full representation of Annotation resource and applicable relationships,
    according to Hypothes.is' v1 API specifications.

    """

    # FIXME: should be "context: HypothesisV1Client", but it causes a mess
    context: object
    annotation_id: AnnotationId
    created: datetime
    updated: datetime
    user_id: UserId
    text: str
    tags: List[str]
    group_id: GroupId
    permissions: Optional[Permissions]
    links: Links
    hidden: bool
    flagged: bool
    uri: Optional[Union[AnyUrl, str]] = None  # TODO: better support for URN
    document: Optional[Document] = None
    moderation: Optional[Moderation] = None
    references: List[AnnotationId] = []
    target: List[Target] = []
    user_info: Optional[UserInfo] = None
    _older_sibling: "Annotation" = PrivateAttr()
    _parent: "Annotation" = PrivateAttr()
    _root: "Annotation" = PrivateAttr()
    _siblings: List["Annotation"] = PrivateAttr()
    _text_position: Tuple[int, int] = PrivateAttr()

    class Config:
        fields = {
            "annotation_id": "id",
            "user_id": "user",
            "group_id": "group",
        }
        arbitrary_types_allowed = True

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError:
            log.error("Error while validating Annotation!")
            log.debug(str(data))
            raise

    @property
    def content(self) -> str:
        """Content of the annotation."""

        # proper annotations
        if self.text and len(self.text) > 0:
            _content: str = self.text

        # highlights
        else:
            _content = next(
                selector.exact
                for selector in getattr(self.target[0], "selector")
                if selector and isinstance(selector, TextQuoteSelector)
            )

        return _content

    @property
    def depth(self) -> int:
        """Indicator of how nested the annotation is within a hierarchy.

        Returns
            A positive integer that increases by one unit for every level the
            annotation is buried inside a hierarchy of replies.

            Returns 0 if the annotation is already a top-level (root)
            annotation.

        See also:
            `Annotation.is_reply`_: a convenience method for telling whether
                ``depth`` is greater than 0.
        """
        _depth: int = len(self.references)
        return _depth

    @property
    def is_reply(self) -> bool:
        """Whether the annotation is a reply.

        Convenience property to check whether the annotation is a reply to
        another (parent) annotation (True), or whether it is a top-level
        annotation (False). If True, is an alias to `Annotation.depth`_ == 0.

        Returns:
            True if the annotation is a reply to another annotation,
                False if the annotation is a top-level annotation.
        """
        return self.depth != 0

    @property
    def parent(self) -> Union["Annotation", None]:
        """Another annotation that the current annotation replies to.

        Returns:
            The annotation that is directly referenced by this reply; or None,
            if it is already a top-level annotation.
        """

        # make sure to compute property only when it is first accessed
        if getattr(self, "_parent", None) is None:

            parent: Optional[Annotation]

            # annotation only references a parent if it is a reply
            if self.is_reply:
                parent_id: AnnotationId = self.references[-1]
                parent = self.context.get_annotation_by_id(parent_id)

            # if it isn't a reply, than return None as parent
            else:
                parent = None

            # store internal variable for answering later calls
            self._parent: Optional[Annotation] = parent

        # returned generated or stored value
        return self._parent

    @property
    def root(self) -> "Annotation":
        """Top-level annotation for a (possibly nested) reply.

        Returns:
            Itself if is already a top-level annotation, or the top-level
            annotation for a hierarchy of replies.
        """

        # make sure to compute property only when it is first accessed
        if getattr(self, "_root", None) is None:

            # climb up the replies hierarchy until reaching the top level
            higher_annotation: "Annotation" = self
            while higher_annotation.is_reply:
                higher_annotation = higher_annotation.parent

            # store internal variable for answering later calls
            self._root: "Annotation" = higher_annotation

        # returned generated or stored value
        return self._root

    @property
    def text_position(self) -> Tuple[int, int]:
        """Start and end position of the selected text.

        Convenience property that retrieves starting and ending positions for
        the annotated text, otherwise nested inside the list of
        `Annotation.target.selectors`_ for top-level annotations.

        Returns:
            A tuple of (starting postion, ending position) if the
        """

        # make sure to compute property only when it is first accessed
        if getattr(self, "_text_position", None) is None:

            # search in annotation's selectors list for a TextPositionSelector
            text_position_selector: TextPositionSelector = next(
                selector
                for selector in self.root.target[0].selector
                if isinstance(selector, TextPositionSelector)
            )

            # unpack starting and ending positions
            start, end = (
                text_position_selector.start,
                text_position_selector.end,
            )

            # store internal variable for answering later calls
            self._text_position: Tuple[int, int] = (start, end)

        # returned generated or stored value
        return self._text_position

    @property
    def siblings(self) -> List["Annotation"]:
        """List of annotations that reply to the same source or annotation.

        Returns:
            A list of top-level annotations that reference the same source
            document, or a list of replies to the same annotation.
        """

        # make sure to compute property only when it is first accessed
        if getattr(self, "_siblings", None) is None:

            # get all annotations that reference this annotation's parent,
            # directly (itself and its siblings) or indirectly ("children" and
            # "nephew" annotations)
            family_branch: List[
                "Annotation"
            ] = self.context.search_annotations(
                uri=self.uri,
                references=getattr(self.parent, "annotation_id", None),
            )

            # filter only direct children of the same document (when it is a
            # top level annotation) or parent annotation (when it is a reply)
            siblings: List["Annotation"] = [
                member
                for member in family_branch
                if member.parent == self.parent and member.depth == self.depth
            ]

            # sort hierarchically by position in text and creation time
            siblings.sort(key=attrgetter("text_position", "created"))

            # store internal variable for answering later calls
            self._siblings: List["Annotation"] = siblings

        # returned generated or stored value
        return self._siblings

    @property
    def position_amongst_siblings(self) -> int:
        """Index of the annotation within a sorted list of sibling annotations.

        Returns:
            The index of the annotation in a list of sibling annotations,
            sorted ascendently by the position of the referenced text in the
            source annotation, when siblings are top-level annotations; or by
            creation date and time.
        """
        siblings = self.siblings
        return siblings.index(self)

    @property
    def older_sibling(self) -> "Annotation":
        """Annotation that comes immediately before this one.

        Returns:
            Another ``Annotation`` that references a text portion of the
            source right before the one referenced by current instance, or that
            was created before it (if both are replies).

            None, if the annotation is already the first in its hierarchical
            lever.
        """

        # make sure to compute property only when it is first accessed
        if getattr(self, "_older_sibling", None) is None:

            # annotation only have an older sibling if it is not the first in
            # its hierarchicall level
            if self.position_amongst_siblings > 0:
                older_sibling: "Annotation" = self.siblings[
                    self.position_amongst_siblings - 1
                ]

            # annotation is the first in its hierarchical level; set to None
            else:
                older_sibling: None = None

            # store internal variable for answering later calls
            self._older_sibling: Optional["Annotation"] = older_sibling
        return self._older_sibling


class Organization(BaseModel):
    organization_id: OrganizationId
    default: bool
    name: str
    logo: Optional[AnyHttpUrl] = None

    class Config:
        fields: {"organization_id": "id"}


class Scopes(BaseModel):
    enforced: bool
    uri_patterns: List[str]


class Group(BaseModel):
    group_id: GroupId
    name: str
    links: Links
    scopes: Optional[Scopes]
    group_type: Literal["private", "open", "restricted"]
    authority_group_id: Optional[GroupId] = None
    organization: Union[OrganizationId, Organization, None] = None
    public: Optional[bool] = None

    class Config:
        fields = {
            "group_id": "id",
            "authority_group_id": "groupid",
            "group_type": "type",
        }

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError:
            log.error("Error while validating Group!")
            log.debug(str(data))
            raise


class UserProfile(BaseModel):
    """Profile information for an authenticated user."""

    authority: str
    features: Mapping[str, bool]
    preferences: Mapping[str, bool]
    user_id: UserId

    class Config:
        fields: {"user_id": "userid"}
