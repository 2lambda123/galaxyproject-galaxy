"""
Details of how the data model objects are mapped onto the relational database
are encapsulated here.
"""

import logging
from threading import local
from typing import Optional, Type

from sqlalchemy import (
    and_,
    asc,
    Boolean,
    Column,
    DateTime,
    desc,
    false,
    ForeignKey,
    func,
    Index,
    Integer,
    not_,
    Numeric,
    select,
    String, Table,
    TEXT,
    Text,
    true,
    Unicode,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import backref, class_mapper, column_property, deferred, object_session, relation
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql import exists

from galaxy import model
from galaxy.model import mapper_registry
from galaxy.model.base import SharedModelMapping
from galaxy.model.custom_types import (
    JSONType,
    MutableJSONType,
    TrimmedString,
    UUIDType,
)
from galaxy.model.migrate.triggers.update_audit_table import install as install_timestamp_triggers
from galaxy.model.orm.engine_factory import build_engine
from galaxy.model.orm.now import now
from galaxy.model.security import GalaxyRBACAgent
from galaxy.model.view import HistoryDatasetCollectionJobStateSummary
from galaxy.model.view.utils import install_views

log = logging.getLogger(__name__)

metadata = mapper_registry.metadata


model.User.table = Table(
    "galaxy_user", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("email", TrimmedString(255), index=True, nullable=False),
    Column("username", TrimmedString(255), index=True, unique=True),
    Column("password", TrimmedString(255), nullable=False),
    Column("last_password_change", DateTime, default=now),
    Column("external", Boolean, default=False),
    Column("form_values_id", Integer, ForeignKey("form_values.id"), index=True),
    Column("deleted", Boolean, index=True, default=False),
    Column("purged", Boolean, index=True, default=False),
    Column("disk_usage", Numeric(15, 0), index=True),
    # Column("person_metadata", JSONType),  # TODO: add persistent, configurable metadata rep for workflow creator
    Column("active", Boolean, index=True, default=True, nullable=False),
    Column("activation_token", TrimmedString(64), nullable=True, index=True))

model.HistoryDatasetAssociation.table = Table(
    "history_dataset_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("history_id", Integer, ForeignKey("history.id"), index=True),
    Column("dataset_id", Integer, ForeignKey("dataset.id"), index=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now, index=True),
    Column("state", TrimmedString(64), index=True, key="_state"),
    Column("copied_from_history_dataset_association_id", Integer,
           ForeignKey("history_dataset_association.id"), nullable=True),
    Column("copied_from_library_dataset_dataset_association_id", Integer,
           ForeignKey("library_dataset_dataset_association.id"), nullable=True),
    Column("name", TrimmedString(255)),
    Column("info", TrimmedString(255)),
    Column("blurb", TrimmedString(255)),
    Column("peek", TEXT, key="_peek"),
    Column("tool_version", TEXT),
    Column("extension", TrimmedString(64)),
    Column("metadata", JSONType, key="_metadata"),
    Column("parent_id", Integer, ForeignKey("history_dataset_association.id"), nullable=True),
    Column("designation", TrimmedString(255)),
    Column("deleted", Boolean, index=True, default=False),
    Column("visible", Boolean),
    Column("extended_metadata_id", Integer, ForeignKey("extended_metadata.id"), index=True),
    Column("version", Integer, default=1, nullable=True, index=True),
    Column("hid", Integer),
    Column("purged", Boolean, index=True, default=False),
    Column("validated_state", TrimmedString(64), default='unvalidated', nullable=False),
    Column("validated_state_message", TEXT),
    Column("hidden_beneath_collection_instance_id",
           ForeignKey("history_dataset_collection_association.id"), nullable=True))


model.HistoryDatasetAssociationHistory.table = Table(
    "history_dataset_association_history", metadata,
    Column("id", Integer, primary_key=True),
    Column("history_dataset_association_id", Integer, ForeignKey("history_dataset_association.id"), index=True),
    Column("update_time", DateTime, default=now),
    Column("version", Integer),
    Column("name", TrimmedString(255)),
    Column("extension", TrimmedString(64)),
    Column("metadata", JSONType, key="_metadata"),
    Column("extended_metadata_id", Integer, ForeignKey("extended_metadata.id"), index=True),
)


model.Dataset.table = Table(
    "dataset", metadata,
    Column("id", Integer, primary_key=True),
    Column('job_id', Integer, ForeignKey('job.id'), index=True, nullable=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, index=True, default=now, onupdate=now),
    Column("state", TrimmedString(64), index=True),
    Column("deleted", Boolean, index=True, default=False),
    Column("purged", Boolean, index=True, default=False),
    Column("purgable", Boolean, default=True),
    Column("object_store_id", TrimmedString(255), index=True),
    Column("external_filename", TEXT),
    Column("_extra_files_path", TEXT),
    Column("created_from_basename", TEXT),
    Column('file_size', Numeric(15, 0)),
    Column('total_size', Numeric(15, 0)),
    Column('uuid', UUIDType()))

# hda read access permission given by a user to a specific site (gen. for external display applications)
model.HistoryDatasetAssociationDisplayAtAuthorization.table = Table(
    "history_dataset_association_display_at_authorization", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, index=True, default=now, onupdate=now),
    Column("history_dataset_association_id", Integer, ForeignKey("history_dataset_association.id"), index=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True),
    Column("site", TrimmedString(255)))

model.HistoryDatasetAssociationSubset.table = Table(
    "history_dataset_association_subset", metadata,
    Column("id", Integer, primary_key=True),
    Column("history_dataset_association_id", Integer, ForeignKey("history_dataset_association.id"), index=True),
    Column("history_dataset_association_subset_id", Integer, ForeignKey("history_dataset_association.id"), index=True),
    Column("location", Unicode(255), index=True))

model.ImplicitlyConvertedDatasetAssociation.table = Table(
    "implicitly_converted_dataset_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("hda_id", Integer, ForeignKey("history_dataset_association.id"), index=True, nullable=True),
    Column("ldda_id", Integer, ForeignKey("library_dataset_dataset_association.id"), index=True, nullable=True),
    Column("hda_parent_id", Integer, ForeignKey("history_dataset_association.id"), index=True),
    Column("ldda_parent_id", Integer, ForeignKey("library_dataset_dataset_association.id"), index=True),
    Column("deleted", Boolean, index=True, default=False),
    Column("metadata_safe", Boolean, index=True, default=True),
    Column("type", TrimmedString(255)))

model.UserRoleAssociation.table = Table(
    "user_role_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True),
    Column("role_id", Integer, ForeignKey("role.id"), index=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now))

model.LibraryDatasetDatasetAssociation.table = Table(
    "library_dataset_dataset_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("library_dataset_id", Integer, ForeignKey("library_dataset.id"), index=True),
    Column("dataset_id", Integer, ForeignKey("dataset.id"), index=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now, index=True),
    Column("state", TrimmedString(64), index=True, key="_state"),
    Column("copied_from_history_dataset_association_id", Integer,
        ForeignKey("history_dataset_association.id", use_alter=True, name='history_dataset_association_dataset_id_fkey'),
        nullable=True),

    Column("copied_from_library_dataset_dataset_association_id", Integer,
        ForeignKey("library_dataset_dataset_association.id", use_alter=True, name='library_dataset_dataset_association_id_fkey'),
        nullable=True),

    Column("name", TrimmedString(255), index=True),
    Column("info", TrimmedString(255)),
    Column("blurb", TrimmedString(255)),
    Column("peek", TEXT, key="_peek"),
    Column("tool_version", TEXT),
    Column("extension", TrimmedString(64)),
    Column("metadata", JSONType, key="_metadata"),
    Column("parent_id", Integer, ForeignKey("library_dataset_dataset_association.id"), nullable=True),
    Column("designation", TrimmedString(255)),
    Column("deleted", Boolean, index=True, default=False),
    Column("validated_state", TrimmedString(64), default='unvalidated', nullable=False),
    Column("validated_state_message", TEXT),
    Column("visible", Boolean),
    Column("extended_metadata_id", Integer, ForeignKey("extended_metadata.id"), index=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True),
    Column("message", TrimmedString(255)))

model.ExtendedMetadata.table = Table(
    "extended_metadata", metadata,
    Column("id", Integer, primary_key=True),
    Column("data", MutableJSONType))

model.ExtendedMetadataIndex.table = Table(
    "extended_metadata_index", metadata,
    Column("id", Integer, primary_key=True),
    Column("extended_metadata_id", Integer,
        ForeignKey("extended_metadata.id", onupdate="CASCADE", ondelete="CASCADE"), index=True),
    Column("path", String(255)),
    Column("value", TEXT))

model.LibraryInfoAssociation.table = Table(
    "library_info_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("library_id", Integer, ForeignKey("library.id"), index=True),
    Column("form_definition_id", Integer, ForeignKey("form_definition.id"), index=True),
    Column("form_values_id", Integer, ForeignKey("form_values.id"), index=True),
    Column("inheritable", Boolean, index=True, default=False),
    Column("deleted", Boolean, index=True, default=False))

model.LibraryFolderInfoAssociation.table = Table(
    "library_folder_info_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("library_folder_id", Integer, ForeignKey("library_folder.id"), nullable=True, index=True),
    Column("form_definition_id", Integer, ForeignKey("form_definition.id"), index=True),
    Column("form_values_id", Integer, ForeignKey("form_values.id"), index=True),
    Column("inheritable", Boolean, index=True, default=False),
    Column("deleted", Boolean, index=True, default=False))

model.LibraryDatasetDatasetInfoAssociation.table = Table(
    "library_dataset_dataset_info_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("library_dataset_dataset_association_id", Integer,
        ForeignKey("library_dataset_dataset_association.id"), nullable=True, index=True),
    Column("form_definition_id", Integer, ForeignKey("form_definition.id"), index=True),
    Column("form_values_id", Integer, ForeignKey("form_values.id"), index=True),
    Column("deleted", Boolean, index=True, default=False))

model.Job.table = Table(
    "job", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now, index=True),
    Column("history_id", Integer, ForeignKey("history.id"), index=True),
    Column("library_folder_id", Integer, ForeignKey("library_folder.id"), index=True),
    Column("tool_id", String(255)),
    Column("tool_version", TEXT, default="1.0.0"),
    Column("galaxy_version", String(64), default=None),
    Column("dynamic_tool_id", Integer, ForeignKey("dynamic_tool.id"), index=True, nullable=True),
    Column("state", String(64), index=True),
    Column("info", TrimmedString(255)),
    Column("copied_from_job_id", Integer, nullable=True),
    Column("command_line", TEXT),
    Column("dependencies", MutableJSONType, nullable=True),
    Column("job_messages", MutableJSONType, nullable=True),
    Column("param_filename", String(1024)),
    Column("runner_name", String(255)),
    Column("job_stdout", TEXT),
    Column("job_stderr", TEXT),
    Column("tool_stdout", TEXT),
    Column("tool_stderr", TEXT),
    Column("exit_code", Integer, nullable=True),
    Column("traceback", TEXT),
    Column("session_id", Integer, ForeignKey("galaxy_session.id"), index=True, nullable=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True, nullable=True),
    Column("job_runner_name", String(255)),
    Column("job_runner_external_id", String(255), index=True),
    Column("destination_id", String(255), nullable=True),
    Column("destination_params", MutableJSONType, nullable=True),
    Column("object_store_id", TrimmedString(255), index=True),
    Column("imported", Boolean, default=False, index=True),
    Column("params", TrimmedString(255), index=True),
    Column("handler", TrimmedString(255), index=True))

model.ImplicitlyCreatedDatasetCollectionInput.table = Table(
    "implicitly_created_dataset_collection_inputs", metadata,
    Column("id", Integer, primary_key=True),
    Column("dataset_collection_id", Integer,
        ForeignKey("history_dataset_collection_association.id"), index=True),
    Column("input_dataset_collection_id", Integer,
        ForeignKey("history_dataset_collection_association.id"), index=True),
    Column("name", Unicode(255)))

model.ImplicitCollectionJobs.table = Table(
    "implicit_collection_jobs", metadata,
    Column("id", Integer, primary_key=True),
    Column("populated_state", TrimmedString(64), default='new', nullable=False),
)

model.ImplicitCollectionJobsJobAssociation.table = Table(
    "implicit_collection_jobs_job_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("implicit_collection_jobs_id", Integer, ForeignKey("implicit_collection_jobs.id"), index=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),  # Consider making this nullable...
    Column("order_index", Integer, nullable=False),
)

model.JobExternalOutputMetadata.table = Table(
    "job_external_output_metadata", metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),
    Column("history_dataset_association_id", Integer,
        ForeignKey("history_dataset_association.id"), index=True, nullable=True),
    Column("library_dataset_dataset_association_id", Integer,
        ForeignKey("library_dataset_dataset_association.id"), index=True, nullable=True),
    Column("is_valid", Boolean, default=True),
    Column("filename_in", String(255)),
    Column("filename_out", String(255)),
    Column("filename_results_code", String(255)),
    Column("filename_kwds", String(255)),
    Column("filename_override_metadata", String(255)),
    Column("job_runner_external_pid", String(255)))

model.JobExportHistoryArchive.table = Table(
    "job_export_history_archive", metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),
    Column("history_id", Integer, ForeignKey("history.id"), index=True),
    Column("dataset_id", Integer, ForeignKey("dataset.id"), index=True),
    Column("compressed", Boolean, index=True, default=False),
    Column("history_attrs_filename", TEXT))

model.JobImportHistoryArchive.table = Table(
    "job_import_history_archive", metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),
    Column("history_id", Integer, ForeignKey("history.id"), index=True),
    Column("archive_dir", TEXT))

model.GenomeIndexToolData.table = Table(
    "genome_index_tool_data", metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),
    Column("deferred_job_id", Integer, ForeignKey("deferred_job.id"), index=True),
    Column("transfer_job_id", Integer, ForeignKey("transfer_job.id"), index=True),
    Column("dataset_id", Integer, ForeignKey("dataset.id"), index=True),
    Column("fasta_path", String(255)),
    Column("created_time", DateTime, default=now),
    Column("modified_time", DateTime, default=now, onupdate=now),
    Column("indexer", String(64)),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True))

model.InteractiveToolEntryPoint.table = Table(
    "interactivetool_entry_point", metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),
    Column("name", TEXT),
    Column("token", TEXT),
    Column("tool_port", Integer),
    Column("host", TEXT),
    Column("port", Integer),
    Column("protocol", TEXT),
    Column("entry_url", TEXT),
    Column("requires_domain", Boolean, default=True),
    Column("info", MutableJSONType, nullable=True),
    Column("configured", Boolean, default=False),
    Column("deleted", Boolean, default=False),
    Column("created_time", DateTime, default=now),
    Column("modified_time", DateTime, default=now, onupdate=now))

model.JobContainerAssociation.table = Table(
    "job_container_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),
    Column("container_type", TEXT),
    Column("container_name", TEXT),
    Column("container_info", MutableJSONType, nullable=True),
    Column("created_time", DateTime, default=now),
    Column("modified_time", DateTime, default=now, onupdate=now))

model.PostJobAction.table = Table(
    "post_job_action", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id"), index=True, nullable=True),
    Column("action_type", String(255), nullable=False),
    Column("output_name", String(255), nullable=True),
    Column("action_arguments", MutableJSONType, nullable=True))

model.PostJobActionAssociation.table = Table(
    "post_job_action_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True, nullable=False),
    Column("post_job_action_id", Integer, ForeignKey("post_job_action.id"), index=True, nullable=False))

model.DeferredJob.table = Table(
    "deferred_job", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("state", String(64), index=True),
    Column("plugin", String(128), index=True),
    Column("params", MutableJSONType))

model.TransferJob.table = Table(
    "transfer_job", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("state", String(64), index=True),
    Column("path", String(1024)),
    Column("info", TEXT),
    Column("pid", Integer),
    Column("socket", Integer),
    Column("params", MutableJSONType))

model.DatasetCollection.table = Table(
    "dataset_collection", metadata,
    Column("id", Integer, primary_key=True),
    Column("collection_type", Unicode(255), nullable=False),
    Column("populated_state", TrimmedString(64), default='ok', nullable=False),
    Column("populated_state_message", TEXT),
    Column("element_count", Integer, nullable=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now))

model.HistoryDatasetCollectionAssociation.table = Table(
    "history_dataset_collection_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("collection_id", Integer, ForeignKey("dataset_collection.id"), index=True),
    Column("history_id", Integer, ForeignKey("history.id"), index=True),
    Column("name", TrimmedString(255)),
    Column("hid", Integer),
    Column("visible", Boolean),
    Column("deleted", Boolean, default=False),
    Column("copied_from_history_dataset_collection_association_id", Integer,
        ForeignKey("history_dataset_collection_association.id"), nullable=True),
    Column("implicit_output_name", Unicode(255), nullable=True),
    Column("job_id", ForeignKey("job.id"), index=True, nullable=True),
    Column("implicit_collection_jobs_id", ForeignKey("implicit_collection_jobs.id"), index=True, nullable=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now, index=True))

model.LibraryDatasetCollectionAssociation.table = Table(
    "library_dataset_collection_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("collection_id", Integer, ForeignKey("dataset_collection.id"), index=True),
    Column("folder_id", Integer, ForeignKey("library_folder.id"), index=True),
    Column("name", TrimmedString(255)),
    Column("deleted", Boolean, default=False))

model.DatasetCollectionElement.table = Table(
    "dataset_collection_element", metadata,
    Column("id", Integer, primary_key=True),
    # Parent collection id describing what collection this element belongs to.
    Column("dataset_collection_id", Integer, ForeignKey("dataset_collection.id"), index=True, nullable=False),
    # Child defined by this association - HDA, LDDA, or another dataset association...
    Column("hda_id", Integer, ForeignKey("history_dataset_association.id"), index=True, nullable=True),
    Column("ldda_id", Integer, ForeignKey("library_dataset_dataset_association.id"), index=True, nullable=True),
    Column("child_collection_id", Integer, ForeignKey("dataset_collection.id"), index=True, nullable=True),
    # Element index and identifier to define this parent-child relationship.
    Column("element_index", Integer),
    Column("element_identifier", Unicode(255), ))

model.Event.table = Table(
    "event", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("history_id", Integer, ForeignKey("history.id"), index=True, nullable=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True, nullable=True),
    Column("message", TrimmedString(1024)),
    Column("session_id", Integer, ForeignKey("galaxy_session.id"), index=True, nullable=True),
    Column("tool_id", String(255)))

model.GalaxySession.table = Table(
    "galaxy_session", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True, nullable=True),
    Column("remote_host", String(255)),
    Column("remote_addr", String(255)),
    Column("referer", TEXT),
    Column("current_history_id", Integer, ForeignKey("history.id"), nullable=True),
    # unique 128 bit random number coerced to a string
    Column("session_key", TrimmedString(255), index=True, unique=True),
    Column("is_valid", Boolean, default=False),
    # saves a reference to the previous session so we have a way to chain them together
    Column("prev_session_id", Integer),
    Column("disk_usage", Numeric(15, 0), index=True),
    Column("last_action", DateTime))

model.GalaxySessionToHistoryAssociation.table = Table(
    "galaxy_session_to_history", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("session_id", Integer, ForeignKey("galaxy_session.id"), index=True),
    Column("history_id", Integer, ForeignKey("history.id"), index=True))

model.StoredWorkflow.table = Table(
    "stored_workflow", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now, index=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True, nullable=False),
    Column("latest_workflow_id", Integer,
        ForeignKey("workflow.id", use_alter=True, name='stored_workflow_latest_workflow_id_fk'), index=True),
    Column("name", TEXT),
    Column("deleted", Boolean, default=False),
    Column("hidden", Boolean, default=False),
    Column("importable", Boolean, default=False),
    Column("slug", TEXT),
    Column("from_path", TEXT),
    Column("published", Boolean, index=True, default=False),
    Index('ix_stored_workflow_slug', 'slug', mysql_length=200),
)

model.Workflow.table = Table(
    "workflow", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    # workflows will belong to either a stored workflow or a parent/nesting workflow.
    Column("stored_workflow_id", Integer, ForeignKey("stored_workflow.id"), index=True, nullable=True),
    Column("parent_workflow_id", Integer, ForeignKey("workflow.id"), index=True, nullable=True),
    Column("name", TEXT),
    Column("has_cycles", Boolean),
    Column("has_errors", Boolean),
    Column("reports_config", MutableJSONType),
    Column("creator_metadata", MutableJSONType),
    Column("license", TEXT),
    Column("uuid", UUIDType, nullable=True))

model.WorkflowStep.table = Table(
    "workflow_step", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("workflow_id", Integer, ForeignKey("workflow.id"), index=True, nullable=False),
    Column("subworkflow_id", Integer, ForeignKey("workflow.id"), index=True, nullable=True),
    Column("dynamic_tool_id", Integer, ForeignKey("dynamic_tool.id"), index=True, nullable=True),
    Column("type", String(64)),
    Column("tool_id", TEXT),
    Column("tool_version", TEXT),
    Column("tool_inputs", JSONType),
    Column("tool_errors", JSONType),
    Column("position", MutableJSONType),
    Column("config", JSONType),
    Column("order_index", Integer),
    Column("uuid", UUIDType),
    # Column( "input_connections", JSONType ),
    Column("label", Unicode(255)))


model.WorkflowStepInput.table = Table(
    "workflow_step_input", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id"), index=True),
    Column("name", TEXT),
    Column("merge_type", TEXT),
    Column("scatter_type", TEXT),
    Column("value_from", MutableJSONType),
    Column("value_from_type", TEXT),
    Column("default_value", MutableJSONType),
    Column("default_value_set", Boolean, default=False),
    Column("runtime_value", Boolean, default=False),
    Index('ix_workflow_step_input_workflow_step_id_name_unique', "workflow_step_id", "name", unique=True, mysql_length={'name': 200}),
)


model.WorkflowRequestStepState.table = Table(
    "workflow_request_step_states", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_id", Integer,
        ForeignKey("workflow_invocation.id", onupdate="CASCADE", ondelete="CASCADE")),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id")),
    Column("value", MutableJSONType))

model.WorkflowRequestInputStepParameter.table = Table(
    "workflow_request_input_step_parameter", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id"), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id")),
    Column("parameter_value", MutableJSONType),
)

model.WorkflowRequestToInputDatasetAssociation.table = Table(
    "workflow_request_to_input_dataset", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id"), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id")),
    Column("dataset_id", Integer, ForeignKey("history_dataset_association.id"), index=True))

model.WorkflowRequestToInputDatasetCollectionAssociation.table = Table(
    "workflow_request_to_input_collection_dataset", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id"), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id")),
    Column("dataset_collection_id", Integer, ForeignKey("history_dataset_collection_association.id"), index=True))

model.WorkflowStepConnection.table = Table(
    "workflow_step_connection", metadata,
    Column("id", Integer, primary_key=True),
    Column("output_step_id", Integer, ForeignKey("workflow_step.id"), index=True),
    Column("input_step_input_id", Integer, ForeignKey("workflow_step_input.id"), index=True),
    Column("output_name", TEXT),
    Column("input_subworkflow_step_id", Integer, ForeignKey("workflow_step.id"), index=True),
)

model.WorkflowOutput.table = Table(
    "workflow_output", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id"), index=True, nullable=False),
    Column("output_name", String(255), nullable=True),
    Column("label", Unicode(255)),
    Column("uuid", UUIDType),
)

model.WorkflowInvocation.table = Table(
    "workflow_invocation", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now, index=True),
    Column("workflow_id", Integer, ForeignKey("workflow.id"), index=True, nullable=False),
    Column("state", TrimmedString(64), index=True),
    Column("scheduler", TrimmedString(255), index=True),
    Column("handler", TrimmedString(255), index=True),
    Column('uuid', UUIDType()),
    Column("history_id", Integer, ForeignKey("history.id"), index=True))

model.WorkflowInvocationStep.table = Table(
    "workflow_invocation_step", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id"), index=True, nullable=False),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id"), index=True, nullable=False),
    Column("state", TrimmedString(64), index=True),
    Column("job_id", Integer, ForeignKey("job.id"), index=True, nullable=True),
    Column("implicit_collection_jobs_id", Integer, ForeignKey("implicit_collection_jobs.id"), index=True, nullable=True),
    Column("action", MutableJSONType, nullable=True))

model.WorkflowInvocationOutputDatasetAssociation.table = Table(
    "workflow_invocation_output_dataset_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id"), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id"), index=True),
    Column("dataset_id", Integer, ForeignKey("history_dataset_association.id"), index=True),
    Column("workflow_output_id", Integer, ForeignKey("workflow_output.id"), index=True),
)

model.WorkflowInvocationOutputDatasetCollectionAssociation.table = Table(
    "workflow_invocation_output_dataset_collection_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id", name='fk_wiodca_wii'), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id", name='fk_wiodca_wsi'), index=True),
    Column("dataset_collection_id", Integer, ForeignKey("history_dataset_collection_association.id", name='fk_wiodca_dci'), index=True),
    Column("workflow_output_id", Integer, ForeignKey("workflow_output.id", name='fk_wiodca_woi'), index=True),
)

model.WorkflowInvocationOutputValue.table = Table(
    "workflow_invocation_output_value", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id"), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id")),
    Column("workflow_output_id", Integer, ForeignKey("workflow_output.id"), index=True),
    Column("value", MutableJSONType),
)

model.WorkflowInvocationStepOutputDatasetAssociation.table = Table(
    "workflow_invocation_step_output_dataset_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_step_id", Integer, ForeignKey("workflow_invocation_step.id"), index=True),
    Column("dataset_id", Integer, ForeignKey("history_dataset_association.id"), index=True),
    Column("output_name", String(255), nullable=True),
)

model.WorkflowInvocationStepOutputDatasetCollectionAssociation.table = Table(
    "workflow_invocation_step_output_dataset_collection_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_step_id", Integer, ForeignKey("workflow_invocation_step.id", name='fk_wisodca_wisi'), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id", name='fk_wisodca_wsi'), index=True),
    Column("dataset_collection_id", Integer, ForeignKey("history_dataset_collection_association.id", name='fk_wisodca_dci'), index=True),
    Column("output_name", String(255), nullable=True),
)

model.WorkflowInvocationToSubworkflowInvocationAssociation.table = Table(
    "workflow_invocation_to_subworkflow_invocation_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("workflow_invocation_id", Integer, ForeignKey("workflow_invocation.id", name='fk_wfi_swi_wfi'), index=True),
    Column("subworkflow_invocation_id", Integer, ForeignKey("workflow_invocation.id", name='fk_wfi_swi_swi'), index=True),
    Column("workflow_step_id", Integer, ForeignKey("workflow_step.id", name='fk_wfi_swi_ws')),
)

model.StoredWorkflowUserShareAssociation.table = Table(
    "stored_workflow_user_share_connection", metadata,
    Column("id", Integer, primary_key=True),
    Column("stored_workflow_id", Integer, ForeignKey("stored_workflow.id"), index=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True))

model.StoredWorkflowMenuEntry.table = Table(
    "stored_workflow_menu_entry", metadata,
    Column("id", Integer, primary_key=True),
    Column("stored_workflow_id", Integer, ForeignKey("stored_workflow.id"), index=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True),
    Column("order_index", Integer))

model.MetadataFile.table = Table(
    "metadata_file", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", TEXT),
    Column("hda_id", Integer, ForeignKey("history_dataset_association.id"), index=True, nullable=True),
    Column("lda_id", Integer, ForeignKey("library_dataset_dataset_association.id"), index=True, nullable=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, index=True, default=now, onupdate=now),
    Column("object_store_id", TrimmedString(255), index=True),
    Column("uuid", UUIDType(), index=True),
    Column("deleted", Boolean, index=True, default=False),
    Column("purged", Boolean, index=True, default=False))

model.Visualization.table = Table(
    "visualization", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, default=now, onupdate=now),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True, nullable=False),
    Column("latest_revision_id", Integer,
        ForeignKey("visualization_revision.id", use_alter=True, name='visualization_latest_revision_id_fk'), index=True),
    Column("title", TEXT),
    Column("type", TEXT),
    Column("dbkey", TEXT),
    Column("deleted", Boolean, default=False, index=True),
    Column("importable", Boolean, default=False, index=True),
    Column("slug", TEXT),
    Column("published", Boolean, default=False, index=True),
    Index('ix_visualization_dbkey', 'dbkey', mysql_length=200),
    Index('ix_visualization_slug', 'slug', mysql_length=200),
)

model.VisualizationUserShareAssociation.table = Table(
    "visualization_user_share_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("visualization_id", Integer, ForeignKey("visualization.id"), index=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True))

# Data Manager tables
model.DataManagerHistoryAssociation.table = Table(
    "data_manager_history_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, index=True, default=now, onupdate=now),
    Column("history_id", Integer, ForeignKey("history.id"), index=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True))

model.DataManagerJobAssociation.table = Table(
    "data_manager_job_association", metadata,
    Column("id", Integer, primary_key=True),
    Column("create_time", DateTime, default=now),
    Column("update_time", DateTime, index=True, default=now, onupdate=now),
    Column("job_id", Integer, ForeignKey("job.id"), index=True),
    Column("data_manager_id", TEXT),
    Index('ix_data_manager_job_association_data_manager_id', 'data_manager_id', mysql_length=200),
)

model.UserPreference.table = Table(
    "user_preference", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("galaxy_user.id"), index=True),
    Column("name", Unicode(255), index=True),
    Column("value", Text))

CleanupEvent_table = Table("cleanup_event", metadata,
                           Column("id", Integer, primary_key=True),
                           Column("create_time", DateTime, default=now),
                           Column("message", TrimmedString(1024)))

CleanupEventDatasetAssociation_table = Table("cleanup_event_dataset_association", metadata,
                                             Column("id", Integer, primary_key=True),
                                             Column("create_time", DateTime, default=now),
                                             Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                             Column("dataset_id", Integer, ForeignKey("dataset.id"), index=True))

CleanupEventMetadataFileAssociation_table = Table("cleanup_event_metadata_file_association", metadata,
                                                  Column("id", Integer, primary_key=True),
                                                  Column("create_time", DateTime, default=now),
                                                  Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                                  Column("metadata_file_id", Integer, ForeignKey("metadata_file.id"), index=True))

CleanupEventHistoryAssociation_table = Table("cleanup_event_history_association", metadata,
                                             Column("id", Integer, primary_key=True),
                                             Column("create_time", DateTime, default=now),
                                             Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                             Column("history_id", Integer, ForeignKey("history.id"), index=True))

CleanupEventHistoryDatasetAssociationAssociation_table = Table("cleanup_event_hda_association", metadata,
                                                               Column("id", Integer, primary_key=True),
                                                               Column("create_time", DateTime, default=now),
                                                               Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                                               Column("hda_id", Integer, ForeignKey("history_dataset_association.id"), index=True))

CleanupEventLibraryAssociation_table = Table("cleanup_event_library_association", metadata,
                                             Column("id", Integer, primary_key=True),
                                             Column("create_time", DateTime, default=now),
                                             Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                             Column("library_id", Integer, ForeignKey("library.id"), index=True))

CleanupEventLibraryFolderAssociation_table = Table("cleanup_event_library_folder_association", metadata,
                                                   Column("id", Integer, primary_key=True),
                                                   Column("create_time", DateTime, default=now),
                                                   Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                                   Column("library_folder_id", Integer, ForeignKey("library_folder.id"), index=True))

CleanupEventLibraryDatasetAssociation_table = Table("cleanup_event_library_dataset_association", metadata,
                                                    Column("id", Integer, primary_key=True),
                                                    Column("create_time", DateTime, default=now),
                                                    Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                                    Column("library_dataset_id", Integer, ForeignKey("library_dataset.id"), index=True))

CleanupEventLibraryDatasetDatasetAssociationAssociation_table = Table("cleanup_event_ldda_association", metadata,
                                                                      Column("id", Integer, primary_key=True),
                                                                      Column("create_time", DateTime, default=now),
                                                                      Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                                                      Column("ldda_id", Integer, ForeignKey("library_dataset_dataset_association.id"), index=True))

CleanupEventImplicitlyConvertedDatasetAssociationAssociation_table = Table("cleanup_event_icda_association", metadata,
                                                                           Column("id", Integer, primary_key=True),
                                                                           Column("create_time", DateTime, default=now),
                                                                           Column("cleanup_event_id", Integer, ForeignKey("cleanup_event.id"), index=True, nullable=True),
                                                                           Column("icda_id", Integer, ForeignKey("implicitly_converted_dataset_association.id"), index=True))


# With the tables defined we can define the mappers and setup the
# relationships between the model objects.
def simple_mapping(model, **kwds):
    mapper_registry.map_imperatively(model, model.table, properties=kwds)


mapper_registry.map_imperatively(model.UserPreference, model.UserPreference.table, properties={})

simple_mapping(model.HistoryDatasetAssociation,
    dataset=relation(model.Dataset,
        primaryjoin=(model.Dataset.table.c.id == model.HistoryDatasetAssociation.table.c.dataset_id),
        lazy=False,
        backref='history_associations'),
    # .history defined in History mapper
    copied_from_history_dataset_association=relation(model.HistoryDatasetAssociation,
        primaryjoin=(model.HistoryDatasetAssociation.table.c.copied_from_history_dataset_association_id
                     == model.HistoryDatasetAssociation.table.c.id),
        remote_side=[model.HistoryDatasetAssociation.table.c.id],
        uselist=False,
        backref='copied_to_history_dataset_associations'),
    copied_to_library_dataset_dataset_associations=relation(model.LibraryDatasetDatasetAssociation,
        primaryjoin=(model.HistoryDatasetAssociation.table.c.id
                     == model.LibraryDatasetDatasetAssociation.table.c.copied_from_history_dataset_association_id),
        backref='copied_from_history_dataset_association'),
    tags=relation(model.HistoryDatasetAssociationTagAssociation,
        order_by=model.HistoryDatasetAssociationTagAssociation.id,
        back_populates='history_dataset_association'),
    annotations=relation(model.HistoryDatasetAssociationAnnotationAssociation,
        order_by=model.HistoryDatasetAssociationAnnotationAssociation.id,
        back_populates="hda"),
    ratings=relation(model.HistoryDatasetAssociationRatingAssociation,
        order_by=model.HistoryDatasetAssociationRatingAssociation.id,
        back_populates="history_dataset_association"),
    extended_metadata=relation(model.ExtendedMetadata,
        primaryjoin=(model.HistoryDatasetAssociation.table.c.extended_metadata_id
                     == model.ExtendedMetadata.table.c.id)),
    hidden_beneath_collection_instance=relation(model.HistoryDatasetCollectionAssociation,
        primaryjoin=(model.HistoryDatasetAssociation.table.c.hidden_beneath_collection_instance_id
                     == model.HistoryDatasetCollectionAssociation.table.c.id),
        uselist=False,
        backref="hidden_dataset_instances"),
    _metadata=deferred(model.HistoryDatasetAssociation.table.c._metadata),
    dependent_jobs=relation(model.JobToInputDatasetAssociation, back_populates='dataset'),
    creating_job_associations=relation(
        model.JobToOutputDatasetAssociation, back_populates='dataset'),
    history=relation(model.History, back_populates='datasets'),
)

simple_mapping(model.Dataset,
    actions=relation(model.DatasetPermissions, back_populates='dataset'),
    job=relation(model.Job, primaryjoin=(model.Dataset.table.c.job_id == model.Job.table.c.id)),
    active_history_associations=relation(model.HistoryDatasetAssociation,
        primaryjoin=(
            (model.Dataset.table.c.id == model.HistoryDatasetAssociation.table.c.dataset_id)
            & (model.HistoryDatasetAssociation.table.c.deleted == false())
            & (model.HistoryDatasetAssociation.table.c.purged == false())),
        viewonly=True),
    purged_history_associations=relation(model.HistoryDatasetAssociation,
        primaryjoin=(
            (model.Dataset.table.c.id == model.HistoryDatasetAssociation.table.c.dataset_id)
            & (model.HistoryDatasetAssociation.table.c.purged == true())),
        viewonly=True),
    active_library_associations=relation(model.LibraryDatasetDatasetAssociation,
        primaryjoin=(
            (model.Dataset.table.c.id == model.LibraryDatasetDatasetAssociation.table.c.dataset_id)
            & (model.LibraryDatasetDatasetAssociation.table.c.deleted == false())),
        viewonly=True),
    hashes=relation(model.DatasetHash, back_populates='dataset'),
    sources=relation(model.DatasetSource, back_populates='dataset'),
)

mapper_registry.map_imperatively(model.HistoryDatasetAssociationHistory, model.HistoryDatasetAssociationHistory.table)

mapper_registry.map_imperatively(model.HistoryDatasetAssociationDisplayAtAuthorization, model.HistoryDatasetAssociationDisplayAtAuthorization.table, properties=dict(
    history_dataset_association=relation(model.HistoryDatasetAssociation),
    user=relation(model.User)
))

mapper_registry.map_imperatively(model.HistoryDatasetAssociationSubset, model.HistoryDatasetAssociationSubset.table, properties=dict(
    hda=relation(model.HistoryDatasetAssociation,
        primaryjoin=(model.HistoryDatasetAssociationSubset.table.c.history_dataset_association_id
                     == model.HistoryDatasetAssociation.table.c.id)),
    subset=relation(model.HistoryDatasetAssociation,
        primaryjoin=(model.HistoryDatasetAssociationSubset.table.c.history_dataset_association_subset_id
                     == model.HistoryDatasetAssociation.table.c.id))
))

mapper_registry.map_imperatively(model.ImplicitlyConvertedDatasetAssociation, model.ImplicitlyConvertedDatasetAssociation.table, properties=dict(
    parent_hda=relation(model.HistoryDatasetAssociation,
        primaryjoin=(model.ImplicitlyConvertedDatasetAssociation.table.c.hda_parent_id
                     == model.HistoryDatasetAssociation.table.c.id),
        backref='implicitly_converted_datasets'),
    dataset_ldda=relation(model.LibraryDatasetDatasetAssociation,
        primaryjoin=(model.ImplicitlyConvertedDatasetAssociation.table.c.ldda_id
                     == model.LibraryDatasetDatasetAssociation.table.c.id),
        backref="implicitly_converted_parent_datasets"),
    dataset=relation(model.HistoryDatasetAssociation,
        primaryjoin=(model.ImplicitlyConvertedDatasetAssociation.table.c.hda_id
                     == model.HistoryDatasetAssociation.table.c.id),
        backref="implicitly_converted_parent_datasets")
))

# Set up proxy so that
#   History.users_shared_with
# returns a list of users that history is shared with.
model.History.users_shared_with_dot_users = association_proxy('users_shared_with', 'user')  # type: ignore

mapper_registry.map_imperatively(model.User, model.User.table, properties=dict(
    addresses=relation(model.UserAddress,
        back_populates='user',
        order_by=desc(model.UserAddress.update_time)),
    cloudauthz=relation(model.CloudAuthz, back_populates='user'),
    custos_auth=relation(model.CustosAuthnzToken, back_populates='user'),
    default_permissions=relation(model.DefaultUserPermissions, back_populates='user'),
    groups=relation(model.UserGroupAssociation, back_populates='user'),
    histories=relation(model.History,
        backref="user",
        order_by=desc(model.History.update_time)),
    active_histories=relation(model.History,
        primaryjoin=(
            (model.History.user_id == model.User.table.c.id)
            & (not_(model.History.deleted))
        ),
        viewonly=True,
        order_by=desc(model.History.update_time)),
    galaxy_sessions=relation(model.GalaxySession,
        backref="user",
        order_by=desc(model.GalaxySession.table.c.update_time)),
    pages_shared_by_others=relation(model.PageUserShareAssociation, back_populates='user'),
    quotas=relation(model.UserQuotaAssociation, back_populates='user'),
    social_auth=relation(model.UserAuthnzToken, back_populates='user'),
    stored_workflow_menu_entries=relation(model.StoredWorkflowMenuEntry,
        primaryjoin=(
            (model.StoredWorkflowMenuEntry.table.c.user_id == model.User.table.c.id)
            & (model.StoredWorkflowMenuEntry.table.c.stored_workflow_id == model.StoredWorkflow.table.c.id)
            & not_(model.StoredWorkflow.table.c.deleted)
        ),
        backref="user",
        cascade="all, delete-orphan",
        collection_class=ordering_list('order_index')),
    _preferences=relation(model.UserPreference,
        backref="user",
        collection_class=attribute_mapped_collection('name')),
    values=relation(model.FormValues,
        primaryjoin=(model.User.table.c.form_values_id == model.FormValues.id)),
    api_keys=relation(model.APIKeys,
        back_populates="user",
        order_by=desc(model.APIKeys.create_time)),
    pages=relation(model.Page, back_populates='user'),
    reset_tokens=relation(model.PasswordResetToken, back_populates='user'),
    histories_shared_by_others=relation(
        model.HistoryUserShareAssociation, back_populates='user'),
))

# Set up proxy so that this syntax is possible:
# <user_obj>.preferences[pref_name] = pref_value
model.User.preferences = association_proxy('_preferences', 'value', creator=model.UserPreference)  # type: ignore

mapper_registry.map_imperatively(model.UserRoleAssociation, model.UserRoleAssociation.table, properties=dict(
    user=relation(model.User, backref="roles"),
    role=relation(model.Role, backref="users"),
    non_private_roles=relation(
        model.User,
        backref="non_private_roles",
        viewonly=True,
        primaryjoin=(
            (model.User.table.c.id == model.UserRoleAssociation.table.c.user_id)
            & (model.UserRoleAssociation.table.c.role_id == model.Role.id)
            & not_(model.Role.name == model.User.table.c.email))
    )
))

mapper_registry.map_imperatively(model.ExtendedMetadata, model.ExtendedMetadata.table, properties=dict(
    children=relation(model.ExtendedMetadataIndex, backref='extended_metadata')
))

mapper_registry.map_imperatively(model.ExtendedMetadataIndex, model.ExtendedMetadataIndex.table)

mapper_registry.map_imperatively(model.LibraryInfoAssociation, model.LibraryInfoAssociation.table, properties=dict(
    library=relation(model.Library,
        primaryjoin=(
            (model.LibraryInfoAssociation.table.c.library_id == model.Library.id)
            & (not_(model.LibraryInfoAssociation.table.c.deleted))
        ),
        backref="info_association"),
    template=relation(model.FormDefinition,
        primaryjoin=(model.LibraryInfoAssociation.table.c.form_definition_id == model.FormDefinition.id)),
    info=relation(model.FormValues,
        primaryjoin=(model.LibraryInfoAssociation.table.c.form_values_id == model.FormValues.id))
))

mapper_registry.map_imperatively(model.LibraryFolderInfoAssociation, model.LibraryFolderInfoAssociation.table, properties=dict(
    folder=relation(model.LibraryFolder,
        primaryjoin=(
            (model.LibraryFolderInfoAssociation.table.c.library_folder_id == model.LibraryFolder.id)
            & (not_(model.LibraryFolderInfoAssociation.table.c.deleted))
        ),
        backref="info_association"),
    template=relation(model.FormDefinition,
        primaryjoin=(model.LibraryFolderInfoAssociation.table.c.form_definition_id == model.FormDefinition.id)),
    info=relation(model.FormValues,
        primaryjoin=(model.LibraryFolderInfoAssociation.table.c.form_values_id == model.FormValues.id))
))

mapper_registry.map_imperatively(model.LibraryDatasetDatasetAssociation, model.LibraryDatasetDatasetAssociation.table, properties=dict(
    dataset=relation(model.Dataset,
        primaryjoin=(model.LibraryDatasetDatasetAssociation.table.c.dataset_id == model.Dataset.table.c.id),
        backref='library_associations'),
    library_dataset=relation(model.LibraryDataset,
        foreign_keys=model.LibraryDatasetDatasetAssociation.table.c.library_dataset_id),
    # user=relation( model.User.mapper ),
    user=relation(model.User),
    copied_from_library_dataset_dataset_association=relation(model.LibraryDatasetDatasetAssociation,
        primaryjoin=(model.LibraryDatasetDatasetAssociation.table.c.copied_from_library_dataset_dataset_association_id
                     == model.LibraryDatasetDatasetAssociation.table.c.id),
        remote_side=[model.LibraryDatasetDatasetAssociation.table.c.id],
        uselist=False,
        backref='copied_to_library_dataset_dataset_associations'),
    copied_to_history_dataset_associations=relation(model.HistoryDatasetAssociation,
        primaryjoin=(model.LibraryDatasetDatasetAssociation.table.c.id
                     == model.HistoryDatasetAssociation.table.c.copied_from_library_dataset_dataset_association_id),
        backref='copied_from_library_dataset_dataset_association'),
    implicitly_converted_datasets=relation(model.ImplicitlyConvertedDatasetAssociation,
        primaryjoin=(model.ImplicitlyConvertedDatasetAssociation.table.c.ldda_parent_id
                     == model.LibraryDatasetDatasetAssociation.table.c.id),
        backref='parent_ldda'),
    tags=relation(model.LibraryDatasetDatasetAssociationTagAssociation,
                  order_by=model.LibraryDatasetDatasetAssociationTagAssociation.id,
                  back_populates='library_dataset_dataset_association'),
    extended_metadata=relation(model.ExtendedMetadata,
        primaryjoin=(model.LibraryDatasetDatasetAssociation.table.c.extended_metadata_id == model.ExtendedMetadata.table.c.id)
    ),
    _metadata=deferred(model.LibraryDatasetDatasetAssociation.table.c._metadata),
    actions=relation(
        model.LibraryDatasetDatasetAssociationPermissions,
        back_populates='library_dataset_dataset_association'),
    dependent_jobs=relation(
        model.JobToInputLibraryDatasetAssociation, back_populates='dataset'),
    creating_job_associations=relation(
        model.JobToOutputLibraryDatasetAssociation, back_populates='dataset'),
))

mapper_registry.map_imperatively(model.LibraryDatasetDatasetInfoAssociation, model.LibraryDatasetDatasetInfoAssociation.table, properties=dict(
    library_dataset_dataset_association=relation(model.LibraryDatasetDatasetAssociation,
        primaryjoin=(
            (model.LibraryDatasetDatasetInfoAssociation.table.c.library_dataset_dataset_association_id
             == model.LibraryDatasetDatasetAssociation.table.c.id)
            & (not_(model.LibraryDatasetDatasetInfoAssociation.table.c.deleted))
        ),
        backref="info_association"),
    template=relation(model.FormDefinition,
        primaryjoin=(model.LibraryDatasetDatasetInfoAssociation.table.c.form_definition_id == model.FormDefinition.id)),
    info=relation(model.FormValues,
        primaryjoin=(model.LibraryDatasetDatasetInfoAssociation.table.c.form_values_id == model.FormValues.id))
))

simple_mapping(model.ImplicitlyCreatedDatasetCollectionInput,
    input_dataset_collection=relation(model.HistoryDatasetCollectionAssociation,
        primaryjoin=(model.HistoryDatasetCollectionAssociation.table.c.id
                     == model.ImplicitlyCreatedDatasetCollectionInput.table.c.input_dataset_collection_id),
        # backref="implicitly_created_dataset_collections",
    ),
)

simple_mapping(model.ImplicitCollectionJobs)

# simple_mapping(
#     model.ImplicitCollectionJobsHistoryDatasetCollectionAssociation,
#     history_dataset_collection_associations=relation(
#         model.HistoryDatasetCollectionAssociation,
#         backref=backref("implicit_collection_jobs_association", uselist=False),
#         uselist=True,
#     ),
# )

simple_mapping(
    model.ImplicitCollectionJobsJobAssociation,
    implicit_collection_jobs=relation(
        model.ImplicitCollectionJobs,
        backref=backref("jobs", uselist=True),
        uselist=False,
    ),
    job=relation(
        model.Job,
        backref=backref("implicit_collection_jobs_association", uselist=False),
        uselist=False,
    ),
)

mapper_registry.map_imperatively(model.JobExternalOutputMetadata, model.JobExternalOutputMetadata.table, properties=dict(
    history_dataset_association=relation(model.HistoryDatasetAssociation, lazy=False),
    library_dataset_dataset_association=relation(model.LibraryDatasetDatasetAssociation, lazy=False)
))

mapper_registry.map_imperatively(model.JobExportHistoryArchive, model.JobExportHistoryArchive.table, properties=dict(
    job=relation(model.Job),
    dataset=relation(model.Dataset, backref='job_export_history_archive'),
    history=relation(model.History, back_populates='exports'),
))

mapper_registry.map_imperatively(model.JobImportHistoryArchive, model.JobImportHistoryArchive.table, properties=dict(
    job=relation(model.Job),
    history=relation(model.History)
))

mapper_registry.map_imperatively(model.GenomeIndexToolData, model.GenomeIndexToolData.table, properties=dict(
    job=relation(model.Job, backref='job'),
    dataset=relation(model.Dataset, backref='genome_index_tool_data'),
    user=relation(model.User),
    deferred=relation(model.DeferredJob, backref='deferred_job'),
    transfer=relation(model.TransferJob, backref='transfer_job')
))

mapper_registry.map_imperatively(model.InteractiveToolEntryPoint, model.InteractiveToolEntryPoint.table, properties=dict(
    job=relation(model.Job, backref=backref('interactivetool_entry_points', uselist=True), uselist=False)
))

mapper_registry.map_imperatively(model.JobContainerAssociation, model.JobContainerAssociation.table, properties=dict(
    job=relation(model.Job, backref=backref('container', uselist=False), uselist=False)
))

mapper_registry.map_imperatively(model.PostJobAction, model.PostJobAction.table, properties=dict(
    workflow_step=relation(model.WorkflowStep,
        backref='post_job_actions',
        primaryjoin=(model.WorkflowStep.table.c.id == model.PostJobAction.table.c.workflow_step_id))
))

mapper_registry.map_imperatively(model.PostJobActionAssociation, model.PostJobActionAssociation.table, properties=dict(
    post_job_action=relation(model.PostJobAction)
))

mapper_registry.map_imperatively(model.DeferredJob, model.DeferredJob.table, properties={})

mapper_registry.map_imperatively(model.TransferJob, model.TransferJob.table, properties={})


simple_mapping(model.DatasetCollection,
    elements=relation(model.DatasetCollectionElement,
        primaryjoin=(model.DatasetCollection.table.c.id == model.DatasetCollectionElement.table.c.dataset_collection_id),
        remote_side=[model.DatasetCollectionElement.table.c.dataset_collection_id],
        backref="collection",
        order_by=model.DatasetCollectionElement.table.c.element_index),
    output_dataset_collections=relation(
        model.JobToImplicitOutputDatasetCollectionAssociation, back_populates='dataset_collection'),
)

simple_mapping(model.HistoryDatasetCollectionAssociation,
    collection=relation(model.DatasetCollection),
    history=relation(model.History,
        backref='dataset_collections'),
    copied_from_history_dataset_collection_association=relation(model.HistoryDatasetCollectionAssociation,
        primaryjoin=(model.HistoryDatasetCollectionAssociation.table.c.copied_from_history_dataset_collection_association_id
                     == model.HistoryDatasetCollectionAssociation.table.c.id),
        remote_side=[model.HistoryDatasetCollectionAssociation.table.c.id],
        backref='copied_to_history_dataset_collection_associations',
        uselist=False),
    implicit_input_collections=relation(model.ImplicitlyCreatedDatasetCollectionInput,
        primaryjoin=(model.HistoryDatasetCollectionAssociation.table.c.id
                     == model.ImplicitlyCreatedDatasetCollectionInput.table.c.dataset_collection_id),
        backref="dataset_collection",
    ),
    implicit_collection_jobs=relation(
        model.ImplicitCollectionJobs,
        backref=backref("history_dataset_collection_associations", uselist=True),
        uselist=False,
    ),
    job=relation(
        model.Job,
        backref=backref("history_dataset_collection_associations", uselist=True),
        uselist=False,
    ),
    job_state_summary=relation(HistoryDatasetCollectionJobStateSummary,
        primaryjoin=(model.HistoryDatasetCollectionAssociation.table.c.id == HistoryDatasetCollectionJobStateSummary.__table__.c.hdca_id),
        foreign_keys=HistoryDatasetCollectionJobStateSummary.__table__.c.hdca_id,
        uselist=False
    ),
    tags=relation(model.HistoryDatasetCollectionTagAssociation,
        order_by=model.HistoryDatasetCollectionTagAssociation.id,
        back_populates='dataset_collection'),
    annotations=relation(model.HistoryDatasetCollectionAssociationAnnotationAssociation,
        order_by=model.HistoryDatasetCollectionAssociationAnnotationAssociation.id,
        back_populates="history_dataset_collection"),
    ratings=relation(model.HistoryDatasetCollectionRatingAssociation,
        order_by=model.HistoryDatasetCollectionRatingAssociation.id,
        back_populates="dataset_collection"),
    output_dataset_collection_instances=relation(
        model.JobToOutputDatasetCollectionAssociation,
        back_populates='dataset_collection_instance'),
)

simple_mapping(model.LibraryDatasetCollectionAssociation,
    collection=relation(model.DatasetCollection),
    folder=relation(model.LibraryFolder,
        backref='dataset_collections'),
    tags=relation(model.LibraryDatasetCollectionTagAssociation,
        order_by=model.LibraryDatasetCollectionTagAssociation.id,
        back_populates='dataset_collection'),
    annotations=relation(model.LibraryDatasetCollectionAnnotationAssociation,
        order_by=model.LibraryDatasetCollectionAnnotationAssociation.id,
        back_populates="dataset_collection"),
    ratings=relation(model.LibraryDatasetCollectionRatingAssociation,
        order_by=model.LibraryDatasetCollectionRatingAssociation.id,
        back_populates="dataset_collection"))

simple_mapping(model.DatasetCollectionElement,
    hda=relation(model.HistoryDatasetAssociation,
        primaryjoin=(model.DatasetCollectionElement.table.c.hda_id == model.HistoryDatasetAssociation.table.c.id)),
    ldda=relation(model.LibraryDatasetDatasetAssociation,
        primaryjoin=(model.DatasetCollectionElement.table.c.ldda_id == model.LibraryDatasetDatasetAssociation.table.c.id)),
    child_collection=relation(model.DatasetCollection,
        primaryjoin=(model.DatasetCollectionElement.table.c.child_collection_id == model.DatasetCollection.table.c.id)))

mapper_registry.map_imperatively(model.Event, model.Event.table, properties=dict(
    history=relation(model.History),
    galaxy_session=relation(model.GalaxySession),
    # user=relation( model.User.mapper ) ) )
    user=relation(model.User)
))

mapper_registry.map_imperatively(model.GalaxySession, model.GalaxySession.table, properties=dict(
    current_history=relation(model.History),
))

mapper_registry.map_imperatively(model.GalaxySessionToHistoryAssociation, model.GalaxySessionToHistoryAssociation.table, properties=dict(
    galaxy_session=relation(model.GalaxySession, backref='histories'),
    history=relation(model.History, backref='galaxy_sessions')
))

mapper_registry.map_imperatively(model.Workflow, model.Workflow.table, properties=dict(
    steps=relation(model.WorkflowStep,
        backref='workflow',
        primaryjoin=(model.Workflow.table.c.id == model.WorkflowStep.table.c.workflow_id),
        order_by=asc(model.WorkflowStep.table.c.order_index),
        cascade="all, delete-orphan",
        lazy=False),
    step_count=column_property(
        select(func.count(model.WorkflowStep.table.c.id)).where(model.Workflow.table.c.id == model.WorkflowStep.table.c.workflow_id).scalar_subquery(),
        deferred=True
    )

))

mapper_registry.map_imperatively(model.WorkflowStep, model.WorkflowStep.table, properties=dict(
    subworkflow=relation(model.Workflow,
        primaryjoin=(model.Workflow.table.c.id == model.WorkflowStep.table.c.subworkflow_id),
        backref="parent_workflow_steps"),
    dynamic_tool=relation(model.DynamicTool,
        primaryjoin=(model.DynamicTool.id == model.WorkflowStep.table.c.dynamic_tool_id),
        back_populates="workflow_steps"),
    tags=relation(model.WorkflowStepTagAssociation,
        order_by=model.WorkflowStepTagAssociation.id,
        back_populates="workflow_step"),
    annotations=relation(model.WorkflowStepAnnotationAssociation,
        order_by=model.WorkflowStepAnnotationAssociation.id,
        back_populates="workflow_step")
))

mapper_registry.map_imperatively(model.WorkflowStepInput, model.WorkflowStepInput.table, properties=dict(
    workflow_step=relation(model.WorkflowStep,
        backref=backref("inputs", uselist=True),
        cascade="all",
        primaryjoin=(model.WorkflowStepInput.table.c.workflow_step_id == model.WorkflowStep.table.c.id))
))

mapper_registry.map_imperatively(model.WorkflowOutput, model.WorkflowOutput.table, properties=dict(
    workflow_step=relation(model.WorkflowStep,
        backref='workflow_outputs',
        primaryjoin=(model.WorkflowStep.table.c.id == model.WorkflowOutput.table.c.workflow_step_id))
))

mapper_registry.map_imperatively(model.WorkflowStepConnection, model.WorkflowStepConnection.table, properties=dict(
    input_step_input=relation(model.WorkflowStepInput,
        backref="connections",
        cascade="all",
        primaryjoin=(model.WorkflowStepConnection.table.c.input_step_input_id == model.WorkflowStepInput.table.c.id)),
    input_subworkflow_step=relation(model.WorkflowStep,
        backref=backref("parent_workflow_input_connections", uselist=True),
        primaryjoin=(model.WorkflowStepConnection.table.c.input_subworkflow_step_id == model.WorkflowStep.table.c.id),
    ),
    output_step=relation(model.WorkflowStep,
        backref="output_connections",
        cascade="all",
        primaryjoin=(model.WorkflowStepConnection.table.c.output_step_id == model.WorkflowStep.table.c.id)),
))


mapper_registry.map_imperatively(model.StoredWorkflow, model.StoredWorkflow.table, properties=dict(
    user=relation(model.User,
        primaryjoin=(model.User.table.c.id == model.StoredWorkflow.table.c.user_id),
        backref='stored_workflows'),
    workflows=relation(model.Workflow,
        backref='stored_workflow',
        cascade="all, delete-orphan",
        primaryjoin=(model.StoredWorkflow.table.c.id == model.Workflow.table.c.stored_workflow_id),
        order_by=-model.Workflow.id),
    latest_workflow=relation(model.Workflow,
        post_update=True,
        primaryjoin=(model.StoredWorkflow.table.c.latest_workflow_id == model.Workflow.table.c.id),
        lazy=False),
    tags=relation(model.StoredWorkflowTagAssociation,
        order_by=model.StoredWorkflowTagAssociation.id,
        back_populates="stored_workflow"),
    owner_tags=relation(model.StoredWorkflowTagAssociation,
        primaryjoin=(
            and_(model.StoredWorkflow.table.c.id == model.StoredWorkflowTagAssociation.stored_workflow_id,
                 model.StoredWorkflow.table.c.user_id == model.StoredWorkflowTagAssociation.user_id)
        ),
        viewonly=True,
        order_by=model.StoredWorkflowTagAssociation.id),
    annotations=relation(model.StoredWorkflowAnnotationAssociation,
        order_by=model.StoredWorkflowAnnotationAssociation.id,
        back_populates="stored_workflow"),
    ratings=relation(model.StoredWorkflowRatingAssociation,
        order_by=model.StoredWorkflowRatingAssociation.id,
        back_populates="stored_workflow"),
    average_rating=column_property(
        select(func.avg(model.StoredWorkflowRatingAssociation.rating)).where(model.StoredWorkflowRatingAssociation.stored_workflow_id == model.StoredWorkflow.table.c.id).scalar_subquery(),
        deferred=True
    )
))

# Set up proxy so that
#   StoredWorkflow.users_shared_with
# returns a list of users that workflow is shared with.
model.StoredWorkflow.users_shared_with_dot_users = association_proxy('users_shared_with', 'user')  # type: ignore

mapper_registry.map_imperatively(model.StoredWorkflowUserShareAssociation, model.StoredWorkflowUserShareAssociation.table, properties=dict(
    user=relation(model.User,
        backref='workflows_shared_by_others'),
    stored_workflow=relation(model.StoredWorkflow,
        backref='users_shared_with')
))

mapper_registry.map_imperatively(model.StoredWorkflowMenuEntry, model.StoredWorkflowMenuEntry.table, properties=dict(
    stored_workflow=relation(model.StoredWorkflow)
))

mapper_registry.map_imperatively(model.WorkflowInvocation, model.WorkflowInvocation.table, properties=dict(
    history=relation(model.History, backref=backref('workflow_invocations', uselist=True)),
    input_parameters=relation(model.WorkflowRequestInputParameter, back_populates='workflow_invocation'),
    step_states=relation(model.WorkflowRequestStepState, backref='workflow_invocation'),
    input_step_parameters=relation(model.WorkflowRequestInputStepParameter,
        backref='workflow_invocation'),
    input_datasets=relation(model.WorkflowRequestToInputDatasetAssociation,
        backref='workflow_invocation'),
    input_dataset_collections=relation(model.WorkflowRequestToInputDatasetCollectionAssociation,
        backref='workflow_invocation'),
    subworkflow_invocations=relation(model.WorkflowInvocationToSubworkflowInvocationAssociation,
        primaryjoin=(model.WorkflowInvocationToSubworkflowInvocationAssociation.table.c.workflow_invocation_id == model.WorkflowInvocation.table.c.id),
        backref=backref("parent_workflow_invocation", uselist=False),
        uselist=True,
    ),
    steps=relation(model.WorkflowInvocationStep,
        backref="workflow_invocation"),
    workflow=relation(model.Workflow)
))

mapper_registry.map_imperatively(model.WorkflowInvocationToSubworkflowInvocationAssociation, model.WorkflowInvocationToSubworkflowInvocationAssociation.table, properties=dict(
    subworkflow_invocation=relation(model.WorkflowInvocation,
        primaryjoin=(model.WorkflowInvocationToSubworkflowInvocationAssociation.table.c.subworkflow_invocation_id == model.WorkflowInvocation.table.c.id),
        backref="parent_workflow_invocation_association",
        uselist=False,
    ),
    workflow_step=relation(model.WorkflowStep),
))

simple_mapping(model.WorkflowInvocationStep,
    workflow_step=relation(model.WorkflowStep),
    job=relation(model.Job, backref=backref('workflow_invocation_step', uselist=False), uselist=False),
    implicit_collection_jobs=relation(model.ImplicitCollectionJobs, backref=backref('workflow_invocation_step', uselist=False), uselist=False),
    subworkflow_invocation_id=column_property(
        select(model.WorkflowInvocationToSubworkflowInvocationAssociation.table.c.subworkflow_invocation_id).where(and_(
            model.WorkflowInvocationToSubworkflowInvocationAssociation.table.c.workflow_invocation_id == model.WorkflowInvocationStep.table.c.workflow_invocation_id,
            model.WorkflowInvocationToSubworkflowInvocationAssociation.table.c.workflow_step_id == model.WorkflowInvocationStep.table.c.workflow_step_id,
        )).scalar_subquery(),
    ),
)

simple_mapping(model.WorkflowRequestStepState,
    workflow_step=relation(model.WorkflowStep))

simple_mapping(model.WorkflowRequestInputStepParameter,
    workflow_step=relation(model.WorkflowStep))

simple_mapping(model.WorkflowRequestToInputDatasetAssociation,
    workflow_step=relation(model.WorkflowStep),
    dataset=relation(model.HistoryDatasetAssociation))


simple_mapping(model.WorkflowRequestToInputDatasetCollectionAssociation,
    workflow_step=relation(model.WorkflowStep),
    dataset_collection=relation(model.HistoryDatasetCollectionAssociation))


mapper_registry.map_imperatively(model.MetadataFile, model.MetadataFile.table, properties=dict(
    history_dataset=relation(model.HistoryDatasetAssociation),
    library_dataset=relation(model.LibraryDatasetDatasetAssociation)
))


simple_mapping(
    model.WorkflowInvocationOutputDatasetAssociation,
    workflow_invocation=relation(model.WorkflowInvocation, backref="output_datasets"),
    workflow_step=relation(model.WorkflowStep),
    dataset=relation(model.HistoryDatasetAssociation),
    workflow_output=relation(model.WorkflowOutput),
)


simple_mapping(
    model.WorkflowInvocationOutputDatasetCollectionAssociation,
    workflow_invocation=relation(model.WorkflowInvocation, backref="output_dataset_collections"),
    workflow_step=relation(model.WorkflowStep),
    dataset_collection=relation(model.HistoryDatasetCollectionAssociation),
    workflow_output=relation(model.WorkflowOutput),
)


simple_mapping(
    model.WorkflowInvocationOutputValue,
    workflow_invocation=relation(model.WorkflowInvocation, backref="output_values"),
    workflow_invocation_step=relation(model.WorkflowInvocationStep,
        foreign_keys=[model.WorkflowInvocationStep.table.c.workflow_invocation_id, model.WorkflowInvocationStep.table.c.workflow_step_id],
        primaryjoin=and_(
            model.WorkflowInvocationStep.table.c.workflow_invocation_id == model.WorkflowInvocationOutputValue.table.c.workflow_invocation_id,
            model.WorkflowInvocationStep.table.c.workflow_step_id == model.WorkflowInvocationOutputValue.table.c.workflow_step_id,
        ),
        backref='output_value',
        viewonly=True
    ),
    workflow_step=relation(model.WorkflowStep),
    workflow_output=relation(model.WorkflowOutput),
)


simple_mapping(
    model.WorkflowInvocationStepOutputDatasetAssociation,
    workflow_invocation_step=relation(model.WorkflowInvocationStep, backref="output_datasets"),
    dataset=relation(model.HistoryDatasetAssociation),
)


simple_mapping(
    model.WorkflowInvocationStepOutputDatasetCollectionAssociation,
    workflow_invocation_step=relation(model.WorkflowInvocationStep, backref="output_dataset_collections"),
    dataset_collection=relation(model.HistoryDatasetCollectionAssociation),
)

# Set up proxy so that
#   Page.users_shared_with
# returns a list of users that page is shared with.
model.Page.users_shared_with_dot_users = association_proxy('users_shared_with', 'user')  # type: ignore

mapper_registry.map_imperatively(model.Visualization, model.Visualization.table, properties=dict(
    user=relation(model.User),
    revisions=relation(model.VisualizationRevision,
        backref='visualization',
        cascade="all, delete-orphan",
        primaryjoin=(model.Visualization.table.c.id == model.VisualizationRevision.visualization_id)),
    latest_revision=relation(model.VisualizationRevision,
        post_update=True,
        primaryjoin=(model.Visualization.table.c.latest_revision_id == model.VisualizationRevision.id),
        lazy=False),
    tags=relation(model.VisualizationTagAssociation,
        order_by=model.VisualizationTagAssociation.id,
        back_populates="visualization"),
    annotations=relation(model.VisualizationAnnotationAssociation,
        order_by=model.VisualizationAnnotationAssociation.id,
        back_populates="visualization"),
    ratings=relation(model.VisualizationRatingAssociation,
        order_by=model.VisualizationRatingAssociation.id,
        back_populates="visualization"),
    average_rating=column_property(
        select(func.avg(model.VisualizationRatingAssociation.rating)).where(model.VisualizationRatingAssociation.visualization_id == model.Visualization.table.c.id).scalar_subquery(),
        deferred=True
    )
))

# Set up proxy so that
#   Visualization.users_shared_with
# returns a list of users that visualization is shared with.
model.Visualization.users_shared_with_dot_users = association_proxy('users_shared_with', 'user')  # type: ignore

mapper_registry.map_imperatively(model.VisualizationUserShareAssociation, model.VisualizationUserShareAssociation.table, properties=dict(
    user=relation(model.User,
        backref='visualizations_shared_by_others'),
    visualization=relation(model.Visualization,
        backref='users_shared_with')
))

mapper_registry.map_imperatively(model.Job, model.Job.table, properties=dict(
    # user=relation( model.User.mapper ),
    user=relation(model.User),
    galaxy_session=relation(model.GalaxySession),
    history=relation(model.History, backref="jobs"),
    library_folder=relation(model.LibraryFolder, lazy=True),
    parameters=relation(model.JobParameter, lazy=True),
    input_datasets=relation(model.JobToInputDatasetAssociation, back_populates="job"),
    input_dataset_collections=relation(model.JobToInputDatasetCollectionAssociation, back_populates="job", lazy=True),
    input_dataset_collection_elements=relation(model.JobToInputDatasetCollectionElementAssociation,
        back_populates="job", lazy=True),
    output_dataset_collection_instances=relation(model.JobToOutputDatasetCollectionAssociation,
        back_populates="job", lazy=True),
    output_dataset_collections=relation(model.JobToImplicitOutputDatasetCollectionAssociation,
        back_populates="job", lazy=True),
    post_job_actions=relation(model.PostJobActionAssociation, backref="job", lazy=False),
    input_library_datasets=relation(model.JobToInputLibraryDatasetAssociation, back_populates="job"),
    output_library_datasets=relation(model.JobToOutputLibraryDatasetAssociation,
        back_populates="job", lazy=True),
    external_output_metadata=relation(model.JobExternalOutputMetadata, lazy=True, backref='job'),
    tasks=relation(model.Task, back_populates='job'),
    output_datasets=relation(model.JobToOutputDatasetAssociation, back_populates='job'),
    state_history=relation(model.JobStateHistory, back_populates='job'),
    text_metrics=relation(model.JobMetricText, back_populates='job'),
    numeric_metrics=relation(model.JobMetricNumeric, back_populates='job'),
))
model.Job.any_output_dataset_deleted = column_property(  # type: ignore
    exists([model.HistoryDatasetAssociation],
           and_(model.Job.table.c.id == model.JobToOutputDatasetAssociation.job_id,
                model.HistoryDatasetAssociation.table.c.id == model.JobToOutputDatasetAssociation.dataset_id,
                model.HistoryDatasetAssociation.table.c.deleted == true())
           )
)
model.Job.any_output_dataset_collection_instances_deleted = column_property(  # type: ignore
    exists([model.HistoryDatasetCollectionAssociation.table.c.id],
           and_(model.Job.table.c.id == model.JobToOutputDatasetCollectionAssociation.job_id,
                model.HistoryDatasetCollectionAssociation.table.c.id == model.JobToOutputDatasetCollectionAssociation.dataset_collection_id,
                model.HistoryDatasetCollectionAssociation.table.c.deleted == true())
           )
)

# Data Manager tables
mapper_registry.map_imperatively(model.DataManagerHistoryAssociation, model.DataManagerHistoryAssociation.table, properties=dict(
    history=relation(model.History),
    user=relation(model.User,
        backref='data_manager_histories')
))

mapper_registry.map_imperatively(model.DataManagerJobAssociation, model.DataManagerJobAssociation.table, properties=dict(
    job=relation(model.Job,
        backref=backref('data_manager_association', uselist=False),
        uselist=False)
))

class_mapper(model.HistoryDatasetCollectionAssociation).add_property(
    "creating_job_associations", relation(model.JobToOutputDatasetCollectionAssociation, viewonly=True))


# Helper methods.
def db_next_hid(self, n=1):
    """
    db_next_hid( self )

    Override __next_hid to generate from the database in a concurrency safe way.
    Loads the next history ID from the DB and returns it.
    It also saves the future next_id into the DB.

    :rtype:     int
    :returns:   the next history id
    """
    session = object_session(self)
    table = self.table
    trans = session.begin()
    try:
        if "postgres" not in session.bind.dialect.name:
            next_hid = select([table.c.hid_counter], table.c.id == model.cached_id(self)).with_for_update().scalar()
            table.update(table.c.id == self.id).execute(hid_counter=(next_hid + n))
        else:
            stmt = table.update().where(table.c.id == model.cached_id(self)).values(hid_counter=(table.c.hid_counter + n)).returning(table.c.hid_counter)
            next_hid = session.execute(stmt).scalar() - n
        trans.commit()
        return next_hid
    except Exception:
        trans.rollback()
        raise


model.History._next_hid = db_next_hid  # type: ignore


def _workflow_invocation_update(self):
    session = object_session(self)
    table = self.table
    now_val = now()
    stmt = table.update().values(update_time=now_val).where(and_(table.c.id == self.id, table.c.update_time < now_val))
    session.execute(stmt)


model.WorkflowInvocation.update = _workflow_invocation_update  # type: ignore


class GalaxyModelMapping(SharedModelMapping):
    security_agent: GalaxyRBACAgent
    thread_local_log: Optional[local]
    create_tables: bool
    User: Type
    GalaxySession: Type


def init(file_path, url, engine_options=None, create_tables=False, map_install_models=False,
        database_query_profiling_proxy=False, object_store=None, trace_logger=None, use_pbkdf2=True,
        slow_query_log_threshold=0, thread_local_log: Optional[local] = None, log_query_counts=False) -> GalaxyModelMapping:
    """Connect mappings to the database"""
    if engine_options is None:
        engine_options = {}
    # Connect dataset to the file path
    model.Dataset.file_path = file_path
    # Connect dataset to object store
    model.Dataset.object_store = object_store
    # Use PBKDF2 password hashing?
    model.User.use_pbkdf2 = use_pbkdf2
    # Load the appropriate db module
    engine = build_engine(url, engine_options, database_query_profiling_proxy, trace_logger, slow_query_log_threshold, thread_local_log=thread_local_log, log_query_counts=log_query_counts)

    # Connect the metadata to the database.
    metadata.bind = engine

    model_modules = [model]
    if map_install_models:
        import galaxy.model.tool_shed_install.mapping  # noqa: F401
        from galaxy.model import tool_shed_install
        galaxy.model.tool_shed_install.mapping.init(url=url, engine_options=engine_options, create_tables=create_tables)
        model_modules.append(tool_shed_install)

    result = GalaxyModelMapping(model_modules, engine=engine)

    # Create tables if needed
    if create_tables:
        metadata.create_all()
        install_timestamp_triggers(engine)
        install_views(engine)

    result.create_tables = create_tables
    # load local galaxy security policy
    result.security_agent = GalaxyRBACAgent(result)
    result.thread_local_log = thread_local_log
    return result
