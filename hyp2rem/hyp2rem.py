# Copyright 2020 The Hyp2Rem Authors

# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


"""Main logic for Hypothes.is to RemNote connection.

This module includes the Bridge class, that handles the process of syncing
Hypothes.is annotations and RemNote Rems.
"""

import re
from datetime import datetime, timezone
from operator import attrgetter
from typing import List, Mapping, Optional, Union

import log  # type: ignore
from pydantic import AnyUrl  # pylint: disable=no-name-in-module

from hyp2rem.exceptions import ParentNotSyncedError, SiblingNotSyncedError
from hyp2rem.hypothesis.clients import HypothesisV1Client
from hyp2rem.hypothesis.models import Annotation
from hyp2rem.remnote.clients import RemNoteV0Client
from hyp2rem.remnote.models import Rem, RemId
from hyp2rem.utils import UpdatePolicy


class Bridge(object):
    """Class that handles the upload of a list of annotations as RemNote Rems."""

    source_url_statement_template = (
        "Imported from Hypothes.is: < {source_url} >. "
    )
    source_sync_statement_template = "Last sync: {last_sync_iso}"
    source_statement_template = (
        source_url_statement_template + source_sync_statement_template
    )

    def __init__(
        self,
        hyp_client: HypothesisV1Client,
        rem_client: RemNoteV0Client,
        update_policy: UpdatePolicy = UpdatePolicy.SAFESTRICT,
    ):
        self.rem_client: RemNoteV0Client = rem_client

        self.target_annotations: List[Annotation] = hyp_client.annotations
        self.created: List[Rem] = list()
        self.updated: List[Rem] = list()

        # sorting annotations should make much of the most spaghetti sync logic
        # below unnecessary for simpler cases
        self.queue: List[Annotation] = sorted(
            self.target_annotations, key=attrgetter("uri", "depth", "created")
        )

        # define policies for updates
        self.update_policy: UpdatePolicy = update_policy

    @property
    def allow_updates(self) -> bool:
        """Whether updates are to be allowed, according to the update policy."""
        allow_updates: bool = True
        if self.update_policy == UpdatePolicy.FORBID:
            # prevent any update from taking place
            allow_updates = False
        return allow_updates

    @property
    def safe_updates_only(self) -> bool:
        """Whether overwriting manual changes in Rems is allowed."""
        safe_updates_only: bool = True
        if self.update_policy not in [
            UpdatePolicy.SAFE,
            UpdatePolicy.SAFESTRICT,
        ]:
            # allow overwriting manual modifications made in synced rems
            safe_updates_only = False
        return safe_updates_only

    @property
    def propagate_updates(self) -> bool:
        """Whether outdated parent and sibling Rems are to be updated."""
        propagate_updates: bool = True
        if self.update_policy not in [UpdatePolicy.ALL, UpdatePolicy.SAFE]:
            # prevent parent and older sibling rems from being updated when
            # they are not in the target batch
            propagate_updates = False
        return propagate_updates

    @property
    def synced(self) -> List[Rem]:
        """All synced Rems, either created or updated in this session."""
        return self.created + self.updated

    @property
    def targets_created(self) -> List[Rem]:
        """Number of Rems created from provided annotations."""
        targets_created: List[Rem] = [
            rem for rem in self.created if rem in self.target_annotations
        ]
        return targets_created

    @property
    def targets_updated(self) -> List[Rem]:
        """Number of Rems updated from provided annotations."""
        targets_updated: List[Rem] = [
            rem for rem in self.updated if rem in self.target_annotations
        ]
        return targets_updated

    @property
    def stats(self) -> Mapping[str, int]:
        """Statics on the number of annotations created and updated."""
        total_targets: int = len(self.target_annotations)
        total_created: int = len(self.created)
        total_updated: int = len(self.updated)
        total_synced: int = total_created + total_updated
        targets_created: int = len(self.targets_created)
        targets_updated: int = len(self.targets_updated)
        targets_synced: int = targets_created + targets_updated
        other_created: int = total_created - targets_created
        other_updated: int = total_updated - targets_updated
        other_synced: int = other_created + other_updated
        # return all stats
        stats: Mapping[str, int] = {
            "Total targets": total_targets,
            "Total created": total_created,
            "Total updated": total_updated,
            "Total synced": total_synced,
            "Targets created": targets_created,
            "Targets updated": targets_updated,
            "Targets synced": targets_synced,
            "Other created": other_created,
            "Other updated": other_updated,
            "Other synced": other_synced,
        }
        return stats

    @classmethod
    def rem_last_sync(cls, rem: Rem) -> Optional[datetime]:
        """Retrives the last sync date and time for a Hyp2Rem-generated Rem."""

        last_sync: Optional[datetime] = None

        # transform Hyp2Rem's template for last sync strings into a pattern
        last_sync_pattern: str = cls.source_sync_statement_template.format(
            last_sync_iso=r"(?P<last_sync_iso>.*)$"
        )

        # search pattern within rem's source field richtext
        for component in rem.source:
            if isinstance(component, str):
                match: Optional[re.Match] = re.search(
                    last_sync_pattern, component
                )
                if match:
                    last_sync_str: str = match.group("last_sync_iso")
                    last_sync = datetime.fromisoformat(last_sync_str)

        return last_sync

    @classmethod
    def check_updatable(
        cls, annotation: Annotation, correspondent_rem: Rem
    ) -> bool:
        """Check whether an annotation was updated after last sync."""

        last_sync: Optional[datetime] = cls.rem_last_sync(correspondent_rem)
        return last_sync is None or annotation.updated > last_sync

    def get_correspondent_rem(
        self, annotation: Annotation
    ) -> Union[None, Rem]:
        """Search for a Rem that was created from a given annotation."""

        return self.rem_client.get_rem_by_source(annotation.links.json_)

    def sync_one(
        self,
        annotation: Annotation,
        allow_update: bool = True,
    ) -> Rem:
        """Create or update a Rem from a Hypothes.is Annotation."""

        log.debug(f"Syncing annotation #{annotation.annotation_id}")
        # check if parent is synced
        parent_rem: Rem
        if annotation.is_reply:
            assert annotation.parent
            parent_rem = self.get_correspondent_rem(annotation.parent)
            if parent_rem is None:
                raise ParentNotSyncedError
            elif self.propagate_updates and self.check_updatable(
                annotation.parent, parent_rem
            ):
                raise ParentNotSyncedError
        else:
            parent_rem = self.rem_for_source(annotation)

        # check if older sibling is synced (if it exists)
        older_sibling_rem: Optional[Rem] = None
        if annotation.older_sibling is not None:
            older_sibling_rem = self.get_correspondent_rem(
                annotation.older_sibling
            )
            if older_sibling_rem is None:
                raise SiblingNotSyncedError
            elif self.propagate_updates and self.check_updatable(
                annotation.older_sibling, older_sibling_rem
            ):
                raise SiblingNotSyncedError

        # create or update rem based on annotation
        correspondent_rem = self.get_correspondent_rem(annotation)

        if correspondent_rem is None:
            # rem does not exist yet; create it
            correspondent_rem = self.create_rem_from_annotation(
                annotation,
                parent_rem=parent_rem,
            )

        elif allow_update and self.check_updatable(
            annotation, correspondent_rem
        ):
            # rem exists, but is out-of-date; update it
            correspondent_rem = self.update_rem_from_annotation(
                annotation,
                correspondent_rem=correspondent_rem,
                parent_rem=parent_rem,
            )

        # remove from pending annotations and return correspondent rem
        if annotation in self.queue:
            self.queue.remove(annotation)
        return correspondent_rem

    def sync_all(self) -> List[Rem]:
        """Sync all provided annotations to RemNote Rems."""

        for annotation in self.queue:
            log.info(
                f"Syncing annotation #{annotation.annotation_id}: "
                + f"'{annotation.content[0:10]}...' "
                + "("
                + str(self.stats["Targets synced"])
                + "/"
                + str(self.stats["Total targets"])
                + ")"
            )
            # traverse annotation's family hierarchy upwards
            to_sync_in_family: List[Annotation] = [annotation]
            while len(to_sync_in_family) > 0:
                # try to sync last in queue
                member_to_sync: Annotation = to_sync_in_family.pop()
                try:
                    self.sync_one(
                        member_to_sync, allow_update=self.allow_updates
                    )
                except ParentNotSyncedError:
                    log.debug("Parent Rem is not synced.")
                    to_sync_in_family.append(member_to_sync)
                    to_sync_in_family.append(member_to_sync.parent)
                    log.debug("Added to queue.")
                except SiblingNotSyncedError:
                    log.debug("Older sibling Rem is not synced.")
                    to_sync_in_family.append(member_to_sync)
                    to_sync_in_family.append(member_to_sync.older_sibling)
                    log.debug("Added to queue.")

        return self.synced

    def create_rem_from_annotation(
        self,
        annotation: Annotation,
        parent_rem: Rem,
    ) -> Rem:
        """Create a new Rem from a corresponding Hypothes.is annotation."""
        assert annotation.links.json_
        source_url: AnyUrl = annotation.links.json_
        utcnow_iso: str = datetime.now(timezone.utc).isoformat()
        source_statement = Bridge.source_statement_template.format(
            source_url=source_url, last_sync_iso=utcnow_iso
        )
        created_rem: Rem = self.rem_client.create_rem(
            text=annotation.content,
            source=source_statement,
            parent_id=parent_rem.rem_id,
        )
        self.created.append(created_rem)  # add to instance's `created` set
        return created_rem

    def update_rem_from_annotation(
        self,
        annotation: Annotation,
        correspondent_rem: Rem,
        parent_rem: Rem,
    ) -> Rem:
        """Update changes made in an annotation to the corresponding Rem."""
        last_sync: Optional[datetime] = Bridge.rem_last_sync(correspondent_rem)
        if last_sync and correspondent_rem.updated > last_sync:
            log.warn(
                f"Tried to update rem #{correspondent_rem.rem_id}, but "
                + "it has been modified in RemNote since last sync."
            )
            if self.safe_updates_only:
                log.info(
                    "Returning Rem unchanged, as Update Policy is set to "
                    + self.update_policy.value()
                )
                return correspondent_rem
            else:
                log.warn("Overwritting...")

        # split rem name and content (if existent)
        splitted_text: List[str] = re.split(":: ", annotation.text, 1)
        name: str = splitted_text[0]
        content: Optional[str] = (
            splitted_text[1] if len(splitted_text) > 0 else None
        )

        # set sync statement
        assert annotation.links.json_
        source_url: AnyUrl = annotation.links.json_
        utcnow_iso: str = datetime.now(timezone.utc).isoformat()
        source_statement = Bridge.source_statement_template.format(
            source_url=source_url, last_sync_iso=utcnow_iso
        )

        # update
        updated_rem: Rem = self.rem_client.update_rem(
            rem_id=correspondent_rem.rem_id,
            content=content,
            name=name,
            source=source_statement,
            parent_id=getattr(parent_rem, "rem_id", None),
        )
        self.updated.append(updated_rem)  # add to instance's `created` set
        return updated_rem

    def rem_for_source(self, annotation: Annotation) -> Rem:
        """Retrive or create a document-level Rem for a source in Hypothes.is."""
        source_rem: Rem
        source_url: str = annotation.target[0].source  # type: ignore
        existing_rem: Optional[Rem] = self.rem_client.get_rem_by_source(
            source_url
        )
        if existing_rem:
            source_rem = existing_rem
        else:
            source_title: Optional[str] = None
            try:
                source_title = annotation.document.title[0]
            except (AttributeError, IndexError):
                pass
            source_rem = self.rem_client.create_rem(
                source=source_url, is_document=True, text=source_title
            )
        return source_rem
