import logging
from html.parser import HTMLParser

from markupsafe import escape
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from galaxy import (
    model,
    util,
    web,
)
from galaxy.managers.sharable import SlugBuilder
from galaxy.managers.workflows import (
    MissingToolsException,
    WorkflowUpdateOptions,
)
from galaxy.model.base import transaction
from galaxy.model.item_attrs import UsesItemRatings
from galaxy.tools.parameters.workflow_building_modes import workflow_building_modes
from galaxy.util import FILENAME_VALID_CHARS
from galaxy.util.sanitize_html import sanitize_html
from galaxy.web import url_for
from galaxy.webapps.base.controller import (
    BaseUIController,
    SharableMixin,
    UsesStoredWorkflowMixin,
)
from galaxy.workflow.extract import (
    extract_workflow,
    summarize,
)
from galaxy.workflow.modules import load_module_sections

log = logging.getLogger(__name__)


# Simple HTML parser to get all content in a single tag.
class SingleTagContentsParser(HTMLParser):
    def __init__(self, target_tag):
        # Cannot use super() because HTMLParser is an old-style class in Python2
        HTMLParser.__init__(self)
        self.target_tag = target_tag
        self.cur_tag = None
        self.tag_content = ""

    def handle_starttag(self, tag, attrs):
        """Called for each start tag."""
        self.cur_tag = tag

    def handle_data(self, text):
        """Called for each block of plain text."""
        if self.cur_tag == self.target_tag:
            self.tag_content += text


class WorkflowController(BaseUIController, SharableMixin, UsesStoredWorkflowMixin, UsesItemRatings):
    slug_builder = SlugBuilder()

    @web.expose
    def display_by_username_and_slug(self, trans, username, slug, format="html", **kwargs):
        """
        Display workflow based on a username and slug. Format can be html, json, or json-download.
        """

        # Get workflow by username and slug. Security is handled by the display methods below.
        session = trans.sa_session
        user = session.query(model.User).filter_by(username=username).first()
        if not user:
            raise web.httpexceptions.HTTPNotFound()
        stored_workflow = (
            trans.sa_session.query(model.StoredWorkflow).filter_by(user=user, slug=slug, deleted=False).first()
        )
        if not stored_workflow:
            raise web.httpexceptions.HTTPNotFound()
        encoded_id = trans.security.encode_id(stored_workflow.id)

        # Display workflow in requested format.
        if format == "html":
            return self._display(trans, stored_workflow)
        elif format == "json":
            return self.for_direct_import(trans, encoded_id)
        elif format == "json-download":
            return self.export_to_file(trans, encoded_id)

    def _display(self, trans, stored_workflow):
        """Diplay workflow in client."""
        if stored_workflow is None:
            raise web.httpexceptions.HTTPNotFound()

        # Security check raises error if user cannot access workflow.
        self.security_check(trans, stored_workflow, False, True)

        # Get data for workflow's steps.
        self.get_stored_workflow_steps(trans, stored_workflow)

        # Get annotations.
        stored_workflow.annotation = self.get_item_annotation_str(
            trans.sa_session, stored_workflow.user, stored_workflow
        )
        for step in stored_workflow.latest_workflow.steps:
            step.annotation = self.get_item_annotation_str(trans.sa_session, stored_workflow.user, step)

        # Encode page identifier.
        workflow_id = trans.security.encode_id(stored_workflow.id)

        # Redirect to client.
        return trans.response.send_redirect(
            web.url_for(
                controller="published",
                action="workflow",
                id=workflow_id,
            )
        )

    @web.expose
    @web.require_login("to import a workflow", use_panels=True)
    def imp(self, trans, id, **kwargs):
        """Imports a workflow shared by other users."""
        # Set referer message.
        referer = trans.request.referer
        if referer and not referer.startswith(f"{trans.request.application_url}{url_for('/login')}"):
            referer_message = f"<a href='{escape(referer)}'>return to the previous page</a>"
        else:
            referer_message = f"<a href='{url_for('/')}'>go to Galaxy's start page</a>"

        # Do import.
        stored = self.get_stored_workflow(trans, id, check_ownership=False)
        if stored.importable is False:
            return trans.show_error_message(
                f"The owner of this workflow has disabled imports via this link.<br>You can {referer_message}",
                use_panels=True,
            )
        elif stored.deleted:
            return trans.show_error_message(
                f"You can't import this workflow because it has been deleted.<br>You can {referer_message}",
                use_panels=True,
            )
        self._import_shared_workflow(trans, stored)

        # Redirect to load galaxy frames.
        return trans.show_ok_message(
            message="""Workflow "{}" has been imported. <br>You can <a href="{}">start using this workflow</a> or {}.""".format(
                stored.name, web.url_for("/workflows/list"), referer_message
            )
        )

    @web.expose
    @web.require_login("use Galaxy workflows")
    def rename_async(self, trans, id, new_name=None, **kwargs):
        stored = self.get_stored_workflow(trans, id)
        if new_name:
            san_new_name = sanitize_html(new_name)
            stored.name = san_new_name
            stored.latest_workflow.name = san_new_name
            with transaction(trans.sa_session):
                trans.sa_session.commit()
            return stored.name

    @web.expose
    @web.require_login("use Galaxy workflows")
    def annotate_async(self, trans, id, new_annotation=None, **kwargs):
        stored = self.get_stored_workflow(trans, id)
        if new_annotation:
            # Sanitize annotation before adding it.
            new_annotation = sanitize_html(new_annotation)
            self.add_item_annotation(trans.sa_session, trans.get_user(), stored, new_annotation)
            with transaction(trans.sa_session):
                trans.sa_session.commit()
            return new_annotation

    @web.expose
    @web.require_login("use Galaxy workflows")
    def gen_image(self, trans, id, embed="false", version="", **kwargs):
        embed = util.asbool(embed)
        if version:
            version_int_or_none = int(version)
        else:
            version_int_or_none = None
        try:
            s = trans.app.workflow_manager.get_workflow_svg_from_id(
                trans, id, version=version_int_or_none, for_embed=embed
            )
            trans.response.set_content_type("image/svg+xml")
            return s
        except Exception as e:
            log.exception("Failed to generate SVG image")
            error_message = str(e)
            return trans.show_error_message(error_message)

    @web.legacy_expose_api
    def create(self, trans, payload=None, **kwd):
        if trans.request.method == "GET":
            return {
                "title": "Create Workflow",
                "inputs": [
                    {"name": "workflow_name", "label": "Name", "value": "Unnamed workflow"},
                    {
                        "name": "workflow_annotation",
                        "label": "Annotation",
                        "help": "A description of the workflow; annotation is shown alongside shared or published workflows.",
                    },
                ],
            }
        else:
            user = trans.get_user()
            workflow_name = payload.get("workflow_name")
            workflow_annotation = payload.get("workflow_annotation")
            workflow_tags = payload.get("workflow_tags", [])
            if not workflow_name:
                return self.message_exception(trans, "Please provide a workflow name.")
            # Create the new stored workflow
            stored_workflow = model.StoredWorkflow()
            stored_workflow.name = workflow_name
            stored_workflow.user = user
            self.slug_builder.create_item_slug(trans.sa_session, stored_workflow)
            # And the first (empty) workflow revision
            workflow = model.Workflow()
            workflow.name = workflow_name
            workflow.stored_workflow = stored_workflow
            stored_workflow.latest_workflow = workflow
            # Add annotation.
            workflow_annotation = sanitize_html(workflow_annotation)
            self.add_item_annotation(trans.sa_session, trans.get_user(), stored_workflow, workflow_annotation)
            # Add tags
            trans.tag_handler.set_tags_from_list(
                trans.user,
                stored_workflow,
                workflow_tags,
            )
            # Persist
            session = trans.sa_session
            session.add(stored_workflow)
            with transaction(session):
                session.commit()
            return {
                "id": trans.security.encode_id(stored_workflow.id),
                "message": f"Workflow {workflow_name} has been created.",
            }

    @web.json
    def save_workflow_as(
        self, trans, workflow_name, workflow_data, workflow_annotation="", from_tool_form=False, **kwargs
    ):
        """
        Creates a new workflow based on Save As command. It is a new workflow, but
        is created with workflow_data already present.
        """
        user = trans.get_user()
        if workflow_name is not None:
            workflow_contents_manager = self.app.workflow_contents_manager
            stored_workflow = model.StoredWorkflow()
            stored_workflow.name = workflow_name
            stored_workflow.user = user
            self.slug_builder.create_item_slug(trans.sa_session, stored_workflow)
            workflow = model.Workflow()
            workflow.name = workflow_name
            workflow.stored_workflow = stored_workflow
            stored_workflow.latest_workflow = workflow
            # Add annotation.
            workflow_annotation = sanitize_html(workflow_annotation)
            self.add_item_annotation(trans.sa_session, trans.get_user(), stored_workflow, workflow_annotation)

            # Persist
            session = trans.sa_session
            session.add(stored_workflow)
            with transaction(session):
                session.commit()
            workflow_update_options = WorkflowUpdateOptions(
                update_stored_workflow_attributes=False,  # taken care of above
                from_tool_form=from_tool_form,
            )
            try:
                workflow, errors = workflow_contents_manager.update_workflow_from_raw_description(
                    trans,
                    stored_workflow,
                    workflow_data,
                    workflow_update_options,
                )
            except MissingToolsException as e:
                return dict(
                    name=e.workflow.name,
                    message=(
                        "This workflow includes missing or invalid tools. "
                        "It cannot be saved until the following steps are removed or the missing tools are enabled."
                    ),
                    errors=e.errors,
                )
            return trans.security.encode_id(stored_workflow.id)
        else:
            # This is an error state, 'save as' must have a workflow_name
            log.exception("Error in Save As workflow: no name.")

    @web.expose
    @web.json
    @web.require_login("edit workflows")
    def editor(self, trans, id=None, workflow_id=None, version=None, **kwargs):
        """
        Render the main workflow editor interface. The canvas is embedded as
        an iframe (necessary for scrolling to work properly), which is
        rendered by `editor_canvas`.
        """

        new_workflow = False
        if not id:
            if workflow_id:
                stored_workflow = self.app.workflow_manager.get_stored_workflow(trans, workflow_id, by_stored_id=False)
                self.security_check(trans, stored_workflow, True, False)
                id = trans.security.encode_id(stored_workflow.id)
            else:
                new_workflow = True

        # The following query loads all user-owned workflows,
        # So that they can be copied or inserted in the workflow editor.
        workflows = (
            trans.sa_session.query(model.StoredWorkflow)
            .filter_by(user=trans.user, deleted=False, hidden=False)
            .order_by(desc(model.StoredWorkflow.table.c.update_time))
            .options(joinedload(model.StoredWorkflow.latest_workflow).joinedload(model.Workflow.steps))
            .all()
        )

        # create workflow module models
        module_sections = []
        for module_section in load_module_sections(trans).values():
            module_sections.append(
                {
                    "title": module_section.get("title"),
                    "name": module_section.get("name"),
                    "elems": [
                        {"name": elem.get("name"), "title": elem.get("title"), "description": elem.get("description")}
                        for elem in module_section.get("modules")
                    ],
                }
            )

        # create data manager tool models
        data_managers = []
        if trans.user_is_admin and trans.app.data_managers.data_managers:
            for data_manager_val in trans.app.data_managers.data_managers.values():
                tool = data_manager_val.tool
                if not tool.hidden:
                    data_managers.append(
                        {
                            "id": tool.id,
                            "name": tool.name,
                            "hidden": tool.hidden,
                            "description": tool.description,
                            "is_workflow_compatible": tool.is_workflow_compatible,
                        }
                    )

        stored = None
        if new_workflow is False:
            stored = self.get_stored_workflow(trans, id)

            if version is None:
                version = len(stored.workflows) - 1
            else:
                version = int(version)

            # identify item tags
            item_tags = stored.make_tag_string_list()

        # create workflow models
        workflows = [
            {
                "id": trans.security.encode_id(workflow.id),
                "latest_id": trans.security.encode_id(workflow.latest_workflow.id),
                "step_count": len(workflow.latest_workflow.steps),
                "name": workflow.name,
            }
            for workflow in workflows
            if new_workflow or workflow.id != stored.id
        ]

        # build workflow editor model
        editor_config = {
            "moduleSections": module_sections,
            "dataManagers": data_managers,
            "workflows": workflows,
        }

        # for existing workflow add its data to the model
        if new_workflow is False:
            editor_config.update(
                {
                    "id": trans.security.encode_id(stored.id),
                    "name": stored.name,
                    "tags": item_tags,
                    "initialVersion": version,
                    "annotation": self.get_item_annotation_str(trans.sa_session, trans.user, stored),
                }
            )

        # parse to mako
        return editor_config

    @web.json
    def load_workflow(self, trans, id, version=None, **kwargs):
        """
        Get the latest Workflow for the StoredWorkflow identified by `id` and
        encode it as a json string that can be read by the workflow editor
        web interface.
        """
        trans.workflow_building_mode = workflow_building_modes.ENABLED
        stored = self.get_stored_workflow(trans, id, check_ownership=False, check_accessible=True)
        workflow_contents_manager = self.app.workflow_contents_manager
        return workflow_contents_manager.workflow_to_dict(trans, stored, style="editor", version=version)

    @web.json_pretty
    def for_direct_import(self, trans, id, **kwargs):
        """
        Get the latest Workflow for the StoredWorkflow identified by `id` and
        encode it as a json string that can be imported back into Galaxy

        This has slightly different information than the above. In particular,
        it does not attempt to decode forms and build UIs, it just stores
        the raw state.
        """
        stored = self.get_stored_workflow(trans, id, check_ownership=False, check_accessible=True)
        return self._workflow_to_dict(trans, stored)

    @web.json_pretty
    def export_to_file(self, trans, id):
        """
        Get the latest Workflow for the StoredWorkflow identified by `id` and
        export it to a JSON file that can be imported back into Galaxy.

        This has slightly different information than the above. In particular,
        it does not attempt to decode forms and build UIs, it just stores
        the raw state.
        """

        # Get workflow.
        stored = self.get_stored_workflow(trans, id, check_ownership=False, check_accessible=True)

        # Stream workflow to file.
        stored_dict = self._workflow_to_dict(trans, stored)
        if not stored_dict:
            # This workflow has a tool that's missing from the distribution
            trans.response.status = 400
            return "Workflow cannot be exported due to missing tools."
        sname = stored.name
        sname = "".join(c in FILENAME_VALID_CHARS and c or "_" for c in sname)[0:150]
        trans.response.headers["Content-Disposition"] = f'attachment; filename="Galaxy-Workflow-{sname}.ga"'
        trans.response.set_content_type("application/galaxy-archive")
        return stored_dict

    @web.expose
    def build_from_current_history(
        self,
        trans,
        job_ids=None,
        dataset_ids=None,
        dataset_collection_ids=None,
        workflow_name=None,
        dataset_names=None,
        dataset_collection_names=None,
        **kwargs,
    ):
        user = trans.get_user()
        history = trans.get_history()
        if not user:
            return trans.show_error_message("Must be logged in to create workflows")
        if (job_ids is None and dataset_ids is None) or workflow_name is None:
            jobs, warnings = summarize(trans)
            # Render
            return trans.fill_template(
                "workflow/build_from_current_history.mako", jobs=jobs, warnings=warnings, history=history
            )
        else:
            # If there is just one dataset name selected or one dataset collection, these
            # come through as string types instead of lists. xref #3247.
            dataset_names = util.listify(dataset_names)
            dataset_collection_names = util.listify(dataset_collection_names)
            stored_workflow = extract_workflow(
                trans,
                user=user,
                job_ids=job_ids,
                dataset_ids=dataset_ids,
                dataset_collection_ids=dataset_collection_ids,
                workflow_name=workflow_name,
                dataset_names=dataset_names,
                dataset_collection_names=dataset_collection_names,
            )
            # Index page with message
            workflow_id = trans.security.encode_id(stored_workflow.id)
            edit_url = url_for(f"/workflows/edit?id={workflow_id}")
            run_url = url_for(f"/workflows/run?id={workflow_id}")
            return trans.show_message(
                f'Workflow "{escape(workflow_name)}" created from current history. '
                f'You can <a href="{edit_url}" target="_parent">edit</a> or <a href="{run_url}" target="_parent">run</a> the workflow.'
            )
