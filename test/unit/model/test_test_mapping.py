"""
This module contains tests for the utility functions in the test_mapping module.
"""

from contextlib import contextmanager

import pytest
from sqlalchemy import (
    Column,
    create_engine,
    Index,
    Integer,
    select,
    UniqueConstraint
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import registry, Session

from . test_mapping import (
    are_same_entity_collections,
    dbcleanup,
    dbcleanup_wrapper,
    delete_from_database,
    get_stored_obj,
    has_index,
    has_unique_constraint,
    persist,
)


def test_persist(session):
    """
    Verify item is stored in database.
    We call persist() with default arg value: `return_id=True`. Passing `False` results
    in the same functionality except the return value of the funtion is `None`.
    """
    instance = Foo()
    instance_id = persist(session, instance)  # store instance in database
    assert instance_id == 1  # id was assigned
    assert instance not in session  # instance was expunged from session

    stored_instance = _get_stored_instance_by_id(session, Foo, instance_id)
    assert stored_instance.id == instance.id  # instance can be retrieved by id
    assert stored_instance is not instance  # retrieved instance is not the same object


def test_get_stored_obj_must_have_obj_id_xor_where_clause():
    """
    Verify that function must be called with either obj_id or where_clause, but not both.
    """
    with pytest.raises(AssertionError):
        get_stored_obj(None, None, obj_id=1, where_clause='a')
    with pytest.raises(AssertionError):
        get_stored_obj(None, None, obj_id=None, where_clause=None)


def test_get_stored_obj_by_id(session):
    """Verify item is retrieved from database by id."""
    instance = Foo()
    id = persist(session, instance)

    stored_instance = get_stored_obj(session, Foo, id)
    assert stored_instance.id == instance.id


def test_get_stored_obj_by_where_clause(session):
    """Verify item is retrieved from database by a custom WHERE clause."""
    instance1 = Foo()
    instance2 = Foo()
    id1 = persist(session, instance1)
    id2 = persist(session, instance2)

    where_clause = Foo.__table__.c.id == id1
    stored_instance = get_stored_obj(session, Foo, where_clause=where_clause)
    assert stored_instance.id == instance1.id

    where_clause = Foo.__table__.c.id == id2
    stored_instance = get_stored_obj(session, Foo, where_clause=where_clause)
    assert stored_instance.id == instance2.id


def test_delete_from_database_one_item(session):
    """Verify item is deleted from database."""
    instance = Foo()
    id = persist(session, instance)  # store instance in database

    stored_instance = _get_stored_instance_by_id(session, Foo, id)
    assert stored_instance is not None  # instance is present in database

    delete_from_database(session, instance)  # delete instance from database

    with pytest.raises(NoResultFound):  # instance no longer present in database
        stored_instance = _get_stored_instance_by_id(session, Foo, id)


def test_delete_from_database_multiple_items(session):
    """Verify multiple items are deleted from database."""
    instance1 = Foo()
    instance2 = Foo()
    id1 = persist(session, instance1)
    id2 = persist(session, instance2)

    delete_from_database(session, [instance1, instance2])

    with pytest.raises(NoResultFound):
        _get_stored_instance_by_id(session, Foo, id1)
    with pytest.raises(NoResultFound):
        _get_stored_instance_by_id(session, Foo, id2)


def test_dbcleanup_by_id(session):
    instance = Foo()
    with dbcleanup(session, instance) as instance_id:
        stored_instance = _get_stored_instance_by_id(session, Foo, instance_id)
        assert stored_instance  # has been stored in the database

    with pytest.raises(NoResultFound):  # has been deleted from the database
        _get_stored_instance_by_id(session, Foo, instance_id)


def test_dbcleanup_by_where_clause(session):
    instance = Foo()
    where_clause = Foo.__table__.c.id == 1

    with dbcleanup(session, instance, where_clause):
        stored_instance = _get_stored_instance_by_id(session, Foo, where_clause)
        assert stored_instance  # has been stored in the database

    with pytest.raises(NoResultFound):  # has been deleted from the database
        _get_stored_instance_by_id(session, Foo, stored_instance.id)


def test_dbcleanup_wrapper(session):
    """
    Verify dbcleanup_wrapper has same effect as dbcleanup context manager,
    and yields the object instance.
    """
    @contextmanager  # we need a context manager to similate scope
    def managed(a, b):
        yield from dbcleanup_wrapper(a, b)

    instance = Foo()
    # this will call dbcleanup_wrapper that stores instance in the database and returns a reference to it
    with managed(session, instance) as instance2:
        assert instance2 is instance  # instance2 should be a reference to instance
        stored_instance = _get_stored_instance_by_id(session, Foo, instance.id)
        assert stored_instance  # has been stored in the database

    # on exit we expect the entity to be deleted from the database
    with pytest.raises(NoResultFound):  # has been deleted from the database
        _get_stored_instance_by_id(session, Foo, instance.id)


def test_has_index(session):
    assert has_index(Bar.__table__, ('field1',))
    assert not has_index(Foo.__table__, ('field1',))


def test_has_unique_constraint(session):
    assert has_unique_constraint(Bar.__table__, ('field2',))
    assert not has_unique_constraint(Foo.__table__, ('field1',))


def test_are_same_entity_collections(session):
    foo1 = Foo()
    foo2 = Foo()
    foo3 = Foo()
    persist(session, foo1)
    persist(session, foo2)
    persist(session, foo3)

    stored_foo1 = _get_stored_instance_by_id(session, Foo, foo1.id)
    stored_foo2 = _get_stored_instance_by_id(session, Foo, foo2.id)
    stored_foo3 = _get_stored_instance_by_id(session, Foo, foo3.id)

    expected = [foo1, foo2]

    assert are_same_entity_collections([stored_foo1, stored_foo2], expected)
    assert are_same_entity_collections([stored_foo2, stored_foo1], expected)
    assert not are_same_entity_collections([stored_foo1, stored_foo3], expected)
    assert not are_same_entity_collections([stored_foo1, stored_foo1, stored_foo2], expected)


# Test utilities

mapper_registry = registry()


@mapper_registry.mapped
class Foo:
    __tablename__ = 'foo'
    id = Column(Integer, primary_key=True)
    field1 = Column(Integer)


@mapper_registry.mapped
class Bar:
    __tablename__ = 'bar'
    id = Column(Integer, primary_key=True)
    field1 = Column(Integer)
    field2 = Column(Integer)
    __table_args__ = (
        Index('ix', 'field1'),
        UniqueConstraint('field2'),
    )


@pytest.fixture(scope='module')
def engine():
    """Create connection engine. (Fixture is module-scoped)."""
    db_uri = 'sqlite:///:memory:'  # We only need sqlite for these tests
    return create_engine(db_uri)


@pytest.fixture(scope='module')
def init(engine):
    """Create database objects. (Fixture is module-scoped)."""
    mapper_registry.metadata.create_all(engine)


@pytest.fixture
def session(init, engine):
    """Provides a basic session object, closed on exit."""
    with Session(engine) as s:
        yield s


def _get_stored_instance_by_id(session, cls_, id):
    statement = select(Foo).where(cls_.__table__.c.id == id)
    return session.execute(statement).scalar_one()
