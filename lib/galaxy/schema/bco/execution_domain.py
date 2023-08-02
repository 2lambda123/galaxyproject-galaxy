# generated by datamodel-codegen:
#   filename:  https://opensource.ieee.org/2791-object/ieee-2791-schema/-/raw/master/execution_domain.json
#   timestamp: 2022-09-13T23:51:50+00:00

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import (
    Dict,
    List,
    Optional,
)

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    RootModel,
)


class ExternalDataEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ..., description="Description of the service that is accessed", example=["HIVE", "access to e-utils"]
    )
    url: str = Field(
        ...,
        description="The endpoint to be accessed.",
        example=["https://hive.biochemistry.gwu.edu/dna.cgi?cmd=login"],
    )


class Uri(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: Optional[str] = None
    uri: AnyUrl
    access_time: Optional[datetime] = Field(
        None, description="Time stamp of when the request for this data was submitted"
    )
    sha1_checksum: Optional[str] = Field(
        None, description="output of hash function that produces a message digest", pattern="[A-Za-z0-9]+"
    )


class ObjectId(RootModel):
    root: str = Field(
        ...,
        description="A unique identifier that should be applied to each IEEE-2791 Object instance, generated and assigned by a IEEE-2791 database engine. IDs should never be reused",
    )


class ContributionEnum(Enum):
    authoredBy = "authoredBy"
    contributedBy = "contributedBy"
    createdAt = "createdAt"
    createdBy = "createdBy"
    createdWith = "createdWith"
    curatedBy = "curatedBy"
    derivedFrom = "derivedFrom"
    importedBy = "importedBy"
    importedFrom = "importedFrom"
    providedBy = "providedBy"
    retrievedBy = "retrievedBy"
    retrievedFrom = "retrievedFrom"
    sourceAccessedBy = "sourceAccessedBy"


class Contributor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Name of contributor", example=["Charles Darwin"])
    affiliation: Optional[str] = Field(
        None, description="Organization the particular contributor is affiliated with", example=["HMS Beagle"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="electronic means for identification and communication purposes",
        example=["name@example.edu"],
    )
    contribution: List[ContributionEnum] = Field(
        ..., description="type of contribution determined according to PAV ontology"
    )
    orcid: Optional[AnyUrl] = Field(
        None,
        description="Field to record author information. ORCID identifiers allow for the author to curate their information after submission. ORCID identifiers must be valid and must have the prefix ‘https://orcid.org/’",
        example=["http://orcid.org/0000-0002-1825-0097"],
    )


class ScriptItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uri: Optional[Uri] = None


class SoftwarePrerequisite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Names of software prerequisites", example=["HIVE-hexagon"])
    version: str = Field(..., description="Versions of the software prerequisites", example=["babajanian.1"])
    uri: Uri


class ExecutionDomain(BaseModel):
    model_config = ConfigDict(extra="forbid")

    script: List[ScriptItem] = Field(
        ...,
        description="points to a script object or objects that was used to perform computations for this IEEE-2791 Object instance.",
    )
    script_driver: str = Field(
        ...,
        description="Indication of the kind of executable that can be launched in order to perform a sequence of commands described in the script in order to run the pipelin",
        example=["hive", "cwl-runner", "shell"],
    )
    software_prerequisites: List[SoftwarePrerequisite] = Field(
        ...,
        description="Minimal necessary prerequisites, library, tool versions needed to successfully run the script to produce this IEEE-2791 Object.",
    )
    external_data_endpoints: List[ExternalDataEndpoint] = Field(
        ...,
        description="Minimal necessary domain-specific external data source access in order to successfully run the script to produce this IEEE-2791 Object.",
    )
    environment_variables: Dict[str, str] = Field(
        ...,
        description="Environmental parameters that are useful to configure the execution environment on the target platform.",
    )
