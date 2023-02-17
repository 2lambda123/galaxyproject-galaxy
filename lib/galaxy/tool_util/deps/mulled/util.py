"""Utilities for working with mulled abstractions outside the mulled package."""

import collections
import hashlib
import logging
import os
import re
import sys
import tarfile
import threading
from io import BytesIO
from typing import (
    List,
    TYPE_CHECKING,
)

import packaging.version
import requests

if TYPE_CHECKING:
    from galaxy.tool_util.deps.container_resolvers import ResolutionCache

log = logging.getLogger(__name__)

QUAY_REPOSITORY_API_ENDPOINT = "https://quay.io/api/v1/repository"
BUILD_NUMBER_REGEX = re.compile(r"\d+$")
PARSED_TAG = collections.namedtuple("PARSED_TAG", "tag version build_string build_number")
MULLED_SOCKET_TIMEOUT = 12
QUAY_VERSIONS_CACHE_EXPIRY = 300
NAMESPACE_HAS_REPO_NAME_KEY = "galaxy.tool_util.deps.container_resolvers.mulled.util:namespace_repo_names"
TAG_CACHE_KEY = "galaxy.tool_util.deps.container_resolvers.mulled.util:tag_cache"


def default_mulled_conda_channels_from_env():
    if "DEFAULT_MULLED_CONDA_CHANNELS" in os.environ:
        return os.environ["DEFAULT_MULLED_CONDA_CHANNELS"].split(",")
    else:
        return None


def create_repository(namespace, repo_name, oauth_token):
    assert oauth_token
    headers = {"Authorization": f"Bearer {oauth_token}"}
    data = {
        "repository": repo_name,
        "namespace": namespace,
        "description": "",
        "visibility": "public",
    }
    requests.post("https://quay.io/api/v1/repository", json=data, headers=headers, timeout=MULLED_SOCKET_TIMEOUT)


def quay_versions(namespace, pkg_name, session=None):
    """Get all version tags for a Docker image stored on quay.io for supplied package name."""
    data = quay_repository(namespace, pkg_name, session=session)

    if "error_type" in data and data["error_type"] == "invalid_token":
        return []

    if "tags" not in data:
        raise Exception(f"Unexpected response from quay.io - no tags description found [{data}]")

    return [tag for tag in data["tags"].keys() if tag != "latest"]


def quay_repository(namespace, pkg_name, session=None):
    assert namespace is not None
    assert pkg_name is not None
    url = f"https://quay.io/api/v1/repository/{namespace}/{pkg_name}"
    if not session:
        session = requests.session()
    response = session.get(url, timeout=MULLED_SOCKET_TIMEOUT)
    data = response.json()
    return data


def _get_namespace(namespace: str) -> List[str]:
    log.debug(f"Querying {QUAY_REPOSITORY_API_ENDPOINT} for repos within {namespace}")
    next_page = None
    repo_names = []
    repos_headers = {"Accept-encoding": "gzip", "Accept": "application/json"}
    while True:
        repos_parameters = {"public": "true", "namespace": namespace, "next_page": next_page}
        repos_response = requests.get(
            QUAY_REPOSITORY_API_ENDPOINT, headers=repos_headers, params=repos_parameters, timeout=MULLED_SOCKET_TIMEOUT
        )
        repos_response_json = repos_response.json()
        repos = repos_response_json["repositories"]
        repo_names += [r["name"] for r in repos]
        next_page = repos_response_json.get("next_page")
        if not next_page:
            break
    return repo_names


def _namespace_has_repo_name(namespace: str, repo_name: str, resolution_cache: "ResolutionCache") -> bool:
    """
    Get all quay containers in the biocontainers repo
    """
    # resolution_cache.mulled_resolution_cache is the persistent variant of the resolution cache
    preferred_resolution_cache = resolution_cache.mulled_resolution_cache or resolution_cache
    cache_key = NAMESPACE_HAS_REPO_NAME_KEY
    if preferred_resolution_cache is not None:
        try:
            cached_namespace = preferred_resolution_cache.get(cache_key)
            if cached_namespace:
                return repo_name in cached_namespace
        except KeyError:
            # preferred_resolution_cache may be a beaker Cache instance, which
            # raises KeyError if key is not present on `.get`
            pass
    repo_names = _get_namespace(namespace)
    if preferred_resolution_cache is not None:
        preferred_resolution_cache[cache_key] = repo_names
    return repo_name in repo_names


def mulled_tags_for(
    namespace, image, tag_prefix=None, resolution_cache=None, session=None, expire=QUAY_VERSIONS_CACHE_EXPIRY
):
    """Fetch remote tags available for supplied image name.

    The result will be sorted so newest tags are first.
    """
    if resolution_cache is not None:
        # Following check is pretty expensive against biocontainers... don't even bother doing it
        # if can't cache the response.
        if not _namespace_has_repo_name(namespace, image, resolution_cache):
            log.info(f"skipping mulled_tags_for [{image}] no repository")
            return []

    cache_key = TAG_CACHE_KEY
    if resolution_cache is not None:
        if resolution_cache.mulled_resolution_cache is not None:
            # Use persistent cache if possible. Since tags query is lightweight use a relatively short expiry time.
            resolution_cache = resolution_cache.mulled_resolution_cache._get_cache(
                "mulled_tag_cache", {"expire": expire}
            )
        if cache_key not in resolution_cache:
            resolution_cache[cache_key] = collections.defaultdict(dict)
        tag_cache = resolution_cache.get(cache_key)
    else:
        tag_cache = collections.defaultdict(dict)

    tags_cached = False
    try:
        tags = tag_cache[namespace][image]
        tags_cached = True
    except KeyError:
        pass

    if not tags_cached:
        tags = quay_versions(namespace, image, session)
        tag_cache[namespace][image] = tags

    if tag_prefix is not None:
        tags = [t for t in tags if t.startswith(tag_prefix)]
    tags = version_sorted(tags)
    return tags


def split_tag(tag):
    """Split mulled image tag into conda version and conda build."""
    return tag.rsplit("--", 1)


def parse_tag(tag):
    """Decompose tag of mulled images into version, build string and build number."""
    version = tag.rsplit(":")[-1]
    build_string = "-1"
    build_number = -1
    match = BUILD_NUMBER_REGEX.search(version)
    if match:
        build_number = int(match.group(0))
    if "--" in version:
        version, build_string = version.rsplit("--", 1)
    elif "-" in version:
        # Should be mulled multi-container image tag
        version, build_string = version.rsplit("-", 1)
    else:
        # We don't have a build number, and the BUILD_NUMBER_REGEX above is only accurate for build strings,
        # so set build number to -1. Any matching image:version combination with a build number
        # will be considered newer.
        build_number = -1
    return PARSED_TAG(
        tag=tag,
        version=packaging.version.parse(version),
        build_string=packaging.version.parse(build_string),
        build_number=build_number,
    )


def version_sorted(elements):
    """Sort iterable based on loose description of "version" from newest to oldest."""
    elements = (parse_tag(tag) for tag in elements)
    elements = sorted(elements, key=lambda tag: tag.build_string, reverse=True)
    elements = sorted(elements, key=lambda tag: tag.build_number, reverse=True)
    elements = sorted(elements, key=lambda tag: tag.version, reverse=True)
    return [e.tag for e in elements]


Target = collections.namedtuple("Target", ["package_name", "version", "build", "package"])


def build_target(package_name, version=None, build=None, tag=None):
    """Use supplied arguments to build a :class:`Target` object."""
    if tag is not None:
        assert version is None
        assert build is None
        version, build = split_tag(tag)

    # conda package and quay image names are lowercase
    return Target(package_name.lower(), version, build, package_name)


def conda_build_target_str(target):
    rval = target.package_name
    if target.version:
        rval += f"={target.version}"

        if target.build:
            rval += f"={target.build}"

    return rval


def _simple_image_name(targets, image_build=None):
    target = targets[0]
    suffix = ""
    if target.version is not None:
        build = target.build
        if build is None and image_build is not None and image_build != "0":
            # Special case image_build == "0", which has been built without a suffix
            print("WARNING: Hard-coding image build instead of using Conda build - this is not recommended.")
            build = image_build
        suffix += f":{target.version}"
        if build is not None:
            suffix += f"--{build}"
    return f"{target.package_name}{suffix}"


def sort_build_targets(build_targets):
    """Sort build targets by package name.
    
    >>> ordered_targets = [Target(package_name='bioblend=1.0.0', version=None, build=None, package='bioblend=1.0.0'), Target(package_name='galaxyxml=0.4.14', version=None, build=None, package='galaxyxml=0.4.14')]
    >>> unordered_targets = reversed(ordered_targets)
    >>> assert ordered_targets == sort_build_targets(ordered_targets)
    >>> assert ordered_targets == sort_build_targets(unordered_targets)
    """
    return sorted(build_targets, key=lambda t: t.package_name)


def v1_image_name(targets, image_build=None, name_override=None):
    """Generate mulled hash version 1 container identifier for supplied arguments.

    If a single target is specified, simply use the supplied name and version as
    the repository name and tag respectively. If multiple targets are supplied,
    hash the package names and versions together as the repository name. For mulled
    version 1 containers the image build is the repository tag (if supplied).

    >>> single_targets = [build_target("samtools", version="1.3.1")]
    >>> v1_image_name(single_targets)
    'samtools:1.3.1'
    >>> multi_targets = [build_target("samtools", version="1.3.1"), build_target("bwa", version="0.7.13")]
    >>> v1_image_name(multi_targets)
    'mulled-v1-b06ecbd9141f0dbbc0c287375fc0813adfcbdfbd'
    >>> multi_targets_on_versionless = [build_target("samtools", version="1.3.1"), build_target("bwa")]
    >>> v1_image_name(multi_targets_on_versionless)
    'mulled-v1-bda945976caa5734347fbf7f35066d9f58519e0c'
    >>> multi_targets_versionless = [build_target("samtools"), build_target("bwa")]
    >>> v1_image_name(multi_targets_versionless)
    'mulled-v1-fe8faa35dbf6dc65a0f7f5d4ea12e31a79f73e40'
    """
    if name_override is not None:
        print(
            "WARNING: Overriding mulled image name, auto-detection of 'mulled' package attributes will fail to detect result."
        )
        return name_override

    targets = list(targets)
    if len(targets) == 1:
        return _simple_image_name(targets, image_build=image_build)
    else:
        targets_order = sort_build_targets(targets)
        requirements_buffer = "\n".join(map(conda_build_target_str, targets_order))
        m = hashlib.sha1()
        m.update(requirements_buffer.encode())
        suffix = "" if not image_build else f":{image_build}"
        return f"mulled-v1-{m.hexdigest()}{suffix}"


def v2_image_name(targets, image_build=None, name_override=None):
    """Generate mulled hash version 2 container identifier for supplied arguments.

    If a single target is specified, simply use the supplied name and version as
    the repository name and tag respectively. If multiple targets are supplied,
    hash the package names as the repository name and hash the package versions (if set)
    as the tag.

    >>> single_targets = [build_target("samtools", version="1.3.1")]
    >>> v2_image_name(single_targets)
    'samtools:1.3.1'
    >>> single_targets = [build_target("samtools", version="1.3.1", build="py_1")]
    >>> v2_image_name(single_targets)
    'samtools:1.3.1--py_1'
    >>> single_targets = [build_target("samtools", version="1.3.1")]
    >>> v2_image_name(single_targets, image_build="0")
    'samtools:1.3.1'
    >>> single_targets = [build_target("samtools", version="1.3.1", build="py_1")]
    >>> v2_image_name(single_targets, image_build="0")
    'samtools:1.3.1--py_1'
    >>> multi_targets = [build_target("samtools", version="1.3.1"), build_target("bwa", version="0.7.13")]
    >>> v2_image_name(multi_targets)
    'mulled-v2-fe8faa35dbf6dc65a0f7f5d4ea12e31a79f73e40:4d0535c94ef45be8459f429561f0894c3fe0ebcf'
    >>> multi_targets_on_versionless = [build_target("samtools", version="1.3.1"), build_target("bwa")]
    >>> v2_image_name(multi_targets_on_versionless)
    'mulled-v2-fe8faa35dbf6dc65a0f7f5d4ea12e31a79f73e40:b0c847e4fb89c343b04036e33b2daa19c4152cf5'
    >>> multi_targets_versionless = [build_target("samtools"), build_target("bwa")]
    >>> v2_image_name(multi_targets_versionless)
    'mulled-v2-fe8faa35dbf6dc65a0f7f5d4ea12e31a79f73e40'
    """
    if name_override is not None:
        print(
            "WARNING: Overriding mulled image name, auto-detection of 'mulled' package attributes will fail to detect result."
        )
        return name_override

    targets = list(targets)
    if len(targets) == 1:
        return _simple_image_name(targets, image_build=image_build)
    else:
        targets_order = sort_build_targets(targets)
        package_name_buffer = "\n".join(map(lambda t: t.package_name, targets_order))
        package_hash = hashlib.sha1()
        package_hash.update(package_name_buffer.encode())

        versions = map(lambda t: t.version, targets_order)
        if any(versions):
            # Only hash versions if at least one package has versions...
            version_name_buffer = "\n".join(map(lambda t: t.version or "null", targets_order))
            version_hash = hashlib.sha1()
            version_hash.update(version_name_buffer.encode())
            version_hash_str = version_hash.hexdigest()
        else:
            version_hash_str = ""

        if not image_build:
            build_suffix = ""
        elif version_hash_str:
            # tagged verson is <version_hash>-<build>
            build_suffix = f"-{image_build}"
        else:
            # tagged version is simply the build
            build_suffix = image_build
        suffix = ""
        if version_hash_str or build_suffix:
            suffix = f":{version_hash_str}{build_suffix}"
        return f"mulled-v2-{package_hash.hexdigest()}{suffix}"


def get_file_from_recipe_url(url):
    """Downloads file at url and returns tarball"""
    if url.startswith("file://"):
        return tarfile.open(mode="r:bz2", name=url[7:])
    else:
        r = requests.get(url, timeout=MULLED_SOCKET_TIMEOUT)
        return tarfile.open(mode="r:bz2", fileobj=BytesIO(r.content))


def split_container_name(name):
    """
    Takes a container name (e.g. samtools:1.7--1) and returns a list (e.g. ['samtools', '1.7', '1'])
    >>> split_container_name('samtools:1.7--1')
    ['samtools', '1.7', '1']
    """
    return name.replace("--", ":").split(":")


class PrintProgress:
    def __init__(self):
        self.thread = threading.Thread(target=self.progress)
        self.stop = threading.Event()

    def progress(self):
        while not self.stop.is_set():
            print(".", end="")
            sys.stdout.flush()
            self.stop.wait(60)
        print("")

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop.set()
        self.thread.join()


image_name = v1_image_name  # deprecated

__all__ = (
    "build_target",
    "conda_build_target_str",
    "image_name",
    "mulled_tags_for",
    "quay_versions",
    "split_container_name",
    "split_tag",
    "Target",
    "v1_image_name",
    "v2_image_name",
    "version_sorted",
)
