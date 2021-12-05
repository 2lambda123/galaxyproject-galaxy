"""
This module no longer contains the mapping of data model classes to the
relational database.
The module will be revised during migration from SQLAlchemy Migrate to Alembic.
"""

import logging
from threading import local
from typing import Optional, Type

from galaxy import model
from galaxy.model import mapper_registry
from galaxy.model.base import SharedModelMapping
from galaxy.model.migrate.triggers.update_audit_table import install as install_timestamp_triggers
from galaxy.model.orm.engine_factory import build_engine
from galaxy.model.security import GalaxyRBACAgent
from galaxy.model.view.utils import install_views

log = logging.getLogger(__name__)

metadata = mapper_registry.metadata


class GalaxyModelMapping(SharedModelMapping):
    security_agent: GalaxyRBACAgent
    thread_local_log: Optional[local]
    User: Type
    GalaxySession: Type


def init(file_path, url, engine_options=None, create_tables=False, map_install_models=False,
        database_query_profiling_proxy=False, object_store=None, trace_logger=None, use_pbkdf2=True,
        slow_query_log_threshold=0, thread_local_log: Optional[local] = None, log_query_counts=False) -> GalaxyModelMapping:
    # Build engine
    engine = build_engine(
        url, engine_options, database_query_profiling_proxy, trace_logger, slow_query_log_threshold,
        thread_local_log=thread_local_log, log_query_counts=log_query_counts)

    # Create tables if needed
    if create_tables:
        mapper_registry.metadata.create_all(bind=engine)
        create_additional_database_objects(engine)
        if map_install_models:
            from galaxy.model.tool_shed_install import mapping as install_mapping  # noqa: F401
            install_mapping.create_database_objects(engine)

    # Configure model, build ModelMapping
    return configure_model_mapping(
        file_path, object_store, use_pbkdf2, engine, map_install_models, thread_local_log)


def create_additional_database_objects(engine):
    install_timestamp_triggers(engine)
    install_views(engine)


def configure_model_mapping(
    file_path,
    object_store,
    use_pbkdf2,
    engine,
    map_install_models,
    thread_local_log,
) -> GalaxyModelMapping:
    _configure_model(file_path, object_store, use_pbkdf2)
    return _build_model_mapping(engine, map_install_models, thread_local_log)


def _configure_model(file_path, object_store, use_pbkdf2):
    model.Dataset.file_path = file_path
    model.Dataset.object_store = object_store
    model.User.use_pbkdf2 = use_pbkdf2


def _build_model_mapping(engine, map_install_models, thread_local_log):
    model_modules = [model]
    if map_install_models:
        from galaxy.model import tool_shed_install
        model_modules.append(tool_shed_install)

    model_mapping = GalaxyModelMapping(model_modules, engine=engine)
    model_mapping.security_agent = GalaxyRBACAgent(model_mapping)
    model_mapping.thread_local_log = thread_local_log
    return model_mapping
