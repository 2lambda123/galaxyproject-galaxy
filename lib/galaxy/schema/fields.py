import re

from pydantic import (
    BeforeValidator,
    Field,
    WithJsonSchema,
    PlainSerializer,
)
from typing_extensions import (
    Annotated,
    get_args,
    TypeAliasType,
)

from galaxy.security.idencoding import IdEncodingHelper

ENCODED_DATABASE_ID_PATTERN = re.compile("f?[0-9a-f]+")
ENCODED_ID_LENGTH_MULTIPLE = 16


class Security:
    security: IdEncodingHelper


def ensure_valid_id(v: str) -> str:
    len_v = len(v)
    if len_v % ENCODED_ID_LENGTH_MULTIPLE:
        raise ValueError("Invalid id length, must be multiple of 16")
    m = ENCODED_DATABASE_ID_PATTERN.fullmatch(v.lower())
    if not m:
        raise ValueError("Invalid characters in encoded ID")
    return v


def ensure_valid_folder_id(v):
    if not isinstance(v, str):
        raise TypeError("String required")
    if not v.startswith("F"):
        raise TypeError("Invalid library folder ID. Folder IDs must start with an 'F'")
    v = v[1:]
    ensure_valid_id(v)
    return v


_DecodedDatabaseIdField = Annotated[
    int,
    BeforeValidator(lambda database_id: Security.security.decode_id(database_id)),
    BeforeValidator(ensure_valid_id),
    PlainSerializer(lambda database_id: Security.security.encode_id(database_id), return_type=str, when_used="json"),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="serialization",
    ),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="validation",
    ),
]

_EncodedDatabaseIdField = Annotated[
    str,
    BeforeValidator(lambda database_id: Security.security.encode_id(database_id)),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="serialization",
    ),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="validation",
    ),
]

_LibraryFolderDatabaseIdField = Annotated[
    int,
    BeforeValidator(ensure_valid_folder_id),
    BeforeValidator(lambda database_id: Security.security.decode_id(database_id)),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="serialization",
    ),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="validation",
    ),
]

_EncodedLibraryFolderDatabaseIdField = Annotated[
    str,
    BeforeValidator(lambda database_id: Security.security.encode_id(f"F{database_id}")),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="serialization",
    ),
    WithJsonSchema(
        {"type": "string", "example": "0123456789ABCDEF", "pattern": "[0-9a-fA-F]+", "minLength": 16},
        mode="validation",
    ),
]

# It seems TypeAliasType is required for annotation to be picked up
DecodedDatabaseIdField = TypeAliasType("DecodedDatabaseIdField", _DecodedDatabaseIdField)
EncodedDatabaseIdField = TypeAliasType("EncodedDatabaseIdField", _EncodedDatabaseIdField)
LibraryFolderDatabaseIdField = TypeAliasType("LibraryFolderDatabaseIdField", _LibraryFolderDatabaseIdField)
EncodedLibraryFolderDatabaseIdField = TypeAliasType(
    "EncodedLibraryFolderDatabaseIdField", _EncodedLibraryFolderDatabaseIdField
)


def literal_to_value(arg):
    val = get_args(arg)
    if not val:
        return arg
    if len(val) > 1:
        raise Exception("Can't extract default argument for unions")
    return val[0]


def ModelClassField(default_value=...):
    """Represents a database model class name annotated as a constant
    pydantic Field.
    :param class_name: The name of the database class.
    :return: A constant pydantic Field with default annotations for model classes.
    """
    return Field(
        literal_to_value(default_value),
        title="Model class",
        description="The name of the database model class.",
    )
