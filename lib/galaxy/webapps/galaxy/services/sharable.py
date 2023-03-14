import logging
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from sqlalchemy import false

from galaxy.managers import base
from galaxy.managers.notification import NotificationManager
from galaxy.managers.sharable import (
    SharableModelManager,
    SharableModelSerializer,
)
from galaxy.model import (
    History,
    Page,
    User,
    Visualization,
    Workflow,
)
from galaxy.schema.fields import DecodedDatabaseIdField
from galaxy.schema.notifications import (
    NewHistorySharedNotificationContent,
    NotificationCreateData,
    NotificationCreateRequest,
    NotificationRecipients,
    PersonalNotificationCategory,
)
from galaxy.schema.schema import (
    SetSlugPayload,
    ShareWithPayload,
    ShareWithStatus,
    SharingOptions,
    SharingStatus,
    UserIdentifier,
)

log = logging.getLogger(__name__)

SharableItem = Union[
    History,
    Workflow,
    Visualization,
    Page,
]


class ShareableService:
    """
    Provides the common logic used by the API to share *any* kind of
    resource with other users.

    The Manager class of the particular resource must implement the SharableModelManager
    and have a compatible SharableModelSerializer implementation.
    """

    def __init__(
        self,
        manager: SharableModelManager,
        serializer: SharableModelSerializer,
    ) -> None:
        self.manager = manager
        self.serializer = serializer
        self.notification_manager = NotificationManager(self.manager.session())  # TODO inject

    def set_slug(self, trans, id: DecodedDatabaseIdField, payload: SetSlugPayload):
        item = self._get_item_by_id(trans, id)
        self.manager.set_slug(item, payload.new_slug, trans.user)

    def sharing(self, trans, id: DecodedDatabaseIdField) -> SharingStatus:
        """Gets the current sharing status of the item with the given id."""
        item = self._get_item_by_id(trans, id)
        return self._get_sharing_status(trans, item)

    def enable_link_access(self, trans, id: DecodedDatabaseIdField) -> SharingStatus:
        """Makes this item accessible by link.
        If this item contains other elements they will be publicly accessible too.
        """
        item = self._get_item_by_id(trans, id)
        self.manager.make_members_public(trans, item)
        self.manager.make_importable(item)
        return self._get_sharing_status(trans, item)

    def disable_link_access(self, trans, id: DecodedDatabaseIdField) -> SharingStatus:
        item = self._get_item_by_id(trans, id)
        self.manager.make_non_importable(item)
        return self._get_sharing_status(trans, item)

    def publish(self, trans, id: DecodedDatabaseIdField) -> SharingStatus:
        """Makes this item publicly accessible.
        If this item contains other elements they will be publicly accessible too.
        """
        item = self._get_item_by_id(trans, id)
        self.manager.make_members_public(trans, item)
        self.manager.publish(item)
        return self._get_sharing_status(trans, item)

    def unpublish(self, trans, id: DecodedDatabaseIdField) -> SharingStatus:
        item = self._get_item_by_id(trans, id)
        self.manager.unpublish(item)
        return self._get_sharing_status(trans, item)

    def share_with_users(self, trans, id: DecodedDatabaseIdField, payload: ShareWithPayload) -> ShareWithStatus:
        item = self._get_item_by_id(trans, id)
        users, errors = self._get_users(trans, payload.user_ids)
        extra = self._share_with_options(trans, item, users, errors, payload.share_option)
        base_status = self._get_sharing_status(trans, item)
        status = ShareWithStatus.construct(**base_status.dict())
        status.extra = extra
        status.errors.extend(errors)
        self._send_notification_to_users(users, status, item)
        return status

    def _share_with_options(
        self,
        trans,
        item,
        users: Set[User],
        errors: Set[str],
        share_option: Optional[SharingOptions] = None,
    ):
        extra = self.manager.get_sharing_extra_information(trans, item, users, errors, share_option)
        if not extra or extra.can_share:
            self.manager.update_current_sharing_with_users(item, users)
            extra = None
        return extra

    def _get_item_by_id(self, trans, id: DecodedDatabaseIdField):
        class_name = self.manager.model_class.__name__
        item = base.get_object(trans, id, class_name, check_ownership=True, check_accessible=True, deleted=False)
        return item

    def _get_sharing_status(self, trans, item):
        status = self.serializer.serialize_to_view(item, user=trans.user, trans=trans, default_view="sharing")
        status["users_shared_with"] = [
            {"id": self.manager.app.security.encode_id(a.user.id), "email": a.user.email}
            for a in item.users_shared_with
        ]
        return SharingStatus.construct(**status)

    def _get_users(self, trans, emails_or_ids: List[UserIdentifier]) -> Tuple[Set[User], Set[str]]:
        send_to_users: Set[User] = set()
        send_to_err: Set[str] = set()
        for email_or_id in set(emails_or_ids):
            send_to_user = None
            if isinstance(email_or_id, int):
                send_to_user = self.manager.user_manager.by_id(email_or_id)
                if send_to_user.deleted:
                    send_to_user = None
            else:
                email_address = email_or_id.strip()
                if not email_address:
                    continue
                send_to_user = self.manager.user_manager.by_email(
                    email_address, filters=[User.table.c.deleted == false()]
                )

            if not send_to_user:
                send_to_err.add(f"{email_or_id} is not a valid Galaxy user.")
            elif send_to_user == trans.user:
                send_to_err.add("You cannot share resources with yourself.")
            else:
                send_to_users.add(send_to_user)

        return send_to_users, send_to_err

    def _send_notification_to_users(self, users: Set[User], status: ShareWithStatus, item: SharableItem):
        if self.notification_manager.notifications_enabled and users:
            request = SharedItemNotificationRequestFactory.build_notification_request(users, item, status)
            self.notification_manager.create_notification_for_users(request)


class SharedItemNotificationRequestFactory:

    category_map: Dict[SharableItem, PersonalNotificationCategory] = {
        History: PersonalNotificationCategory.new_history_shared,
        Workflow: PersonalNotificationCategory.new_workflow_shared,
        Visualization: PersonalNotificationCategory.new_visualization_shared,
        Page: PersonalNotificationCategory.new_page_shared,
    }

    @staticmethod
    def build_notification_request(
        users: Set[User], item: SharableItem, status: ShareWithStatus
    ) -> NotificationCreateRequest:
        # TODO: Skip if already shared?
        user_ids = [user.id for user in users]
        return NotificationCreateRequest(
            recipients=NotificationRecipients.construct(user_ids=user_ids),
            notification=NotificationCreateData(
                source="sharing_system",
                variant="info",
                category=SharedItemNotificationRequestFactory.category_map[type(item)],
                content=NewHistorySharedNotificationContent(
                    item_name=status.title,
                    owner_name=status.username,
                    slug=status.username_and_slug,
                ),
            ),
        )
