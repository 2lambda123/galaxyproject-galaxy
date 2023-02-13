"""
Plugins resource control over the API.
"""
import logging
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from fastapi import (
    Path,
    Query,
)
from pydantic import (
    BaseModel,
    Field,
)

from galaxy import exceptions
from galaxy.managers import (
    hdas,
    histories,
)
from galaxy.managers.context import ProvidesUserContext
from galaxy.schema.fields import DecodedDatabaseIdField
from galaxy.util import asbool
from galaxy.web import (
    expose_api,
    expose_api_anonymous_and_sessionless,
)
from . import (
    depends,
    DependsOnApp,
    DependsOnTrans,
    Router,
)

log = logging.getLogger(__name__)

router = Router(tags=["plugins"])


class VisualizationPlugin(BaseModel):
    name: str = Field(title="Name", description="Name of the plugin")
    html: str = Field(title="HTML", description="HTML of the plugin")
    description: str = Field(title="Description", description="Description of the plugin")
    logo: Optional[str] = Field(title="Logo", description="Logo of the plugin")
    title: Optional[str] = Field(title="Title", description="Title of the plugin")
    target: str = Field(title="Target", description="Target frame of the plugin")
    embeddable: bool
    entry_point: Dict[str, Any]
    settings: Optional[Dict[str, Any]]
    groups: Optional[List[str]]
    specs: Optional[Dict[str, Any]]
    href: str


# Sample response, mako:
#   {
#     "name": "audio_player",
#     "html": "Audio player",
#     "description": "Audio player",
#     "logo": null,
#     "title": null,
#     "target": "galaxy_main",
#     "embeddable": true,
#     "entry_point": {
#       "type": "mako",
#       "file": "audio_player.mako",
#       "attr": {}
#     },
#     "settings": null,
#     "groups": null,
#     "specs": null,
#     "href": "/plugins/visualizations/audio_player/show"
#   },


# Sample response, chart:
#   {
#     "name": "annotate_image",
#     "html": "Image annotator",
#     "description": "An image annotater built using PaperJS at https://github.com/paperjs/paper.js.",
#     "logo": "./static/plugins/visualizations/annotate_image/static/logo.png",
#     "title": null,
#     "target": "galaxy_main",
#     "embeddable": false,
#     "entry_point": {
#       "type": "chart",
#       "file": null,
#       "attr": {
#         "src": "script.js",
#         "css": "jquery.contextMenu.css"
#       }
#     },
#     "settings": null,
#     "groups": null,
#     "specs": null,
#     "href": "/plugins/visualizations/annotate_image/show"
#   },


@router.cbv
class FastAPIPlugins:  # type: ignore
    hda_manager: hdas.HDAManager = depends(hdas.HDAManager)
    history_manager: histories.HistoryManager = depends(histories.HistoryManager)

    @expose_api_anonymous_and_sessionless
    @router.get(
        "/api/plugins",
        summary="Get a list of all available plugins",
        response_description="List of plugins",
    )
    def index(
        self,
        trans: ProvidesUserContext = DependsOnTrans,
    ) -> List[VisualizationPlugin]:
        registry = self._get_registry()
        kwargs = {}  # transfer
        dataset_id = kwargs.get("dataset_id")
        if dataset_id is not None:
            hda = self.hda_manager.get_accessible(self.decode_id(dataset_id), trans.user)
            return registry.get_visualizations(trans, hda)
        else:
            embeddable = asbool(kwargs.get("embeddable"))
            plugins = registry.get_plugins(embeddable=embeddable)
            return plugins

    @router.get(
        "/api/plugins/{id}",
        summary="Get a plugin by id",
        response_description="Plugin",
    )
    def show(
        self,
        trans: ProvidesUserContext = DependsOnTrans,
        id: str = Path(title="Plugin ID", description="The plugin ID"),
        history_id: Optional[DecodedDatabaseIdField] = Query(
            default=None,
            description="The encoded database identifier of the History.",
        ),
    ) -> VisualizationPlugin:
        registry = self._get_registry()
        kwargs = {}  # transfer
        history_id = kwargs.get("history_id")
        if history_id is not None:
            history = self.history_manager.get_owned(
                trans.security.decode_id(history_id), trans.user, current_history=trans.history
            )
            result = {"hdas": []}
            for hda in history.contents_iter(types=["dataset"], deleted=False, visible=True):
                if registry.get_visualization(trans, id, hda):
                    result["hdas"].append({"id": trans.security.encode_id(hda.id), "name": hda.name})
        else:
            result = registry.get_plugin(id).to_dict()
        return result

    def _get_registry(self):
        if not self.app.visualizations_registry:
            raise exceptions.MessageException("The visualization registry has not been configured.")
        return self.app.visualizations_registry
