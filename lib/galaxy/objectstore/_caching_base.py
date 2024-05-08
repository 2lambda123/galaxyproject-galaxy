import logging
import os
import shutil
from typing import (
    Any,
    Dict,
    Optional,
)

from galaxy.exceptions import (
    ObjectInvalid,
    ObjectNotFound,
)
from galaxy.objectstore import ConcreteObjectStore
from galaxy.util import (
    directory_hash_id,
    ExecutionTimer,
    unlink,
)
from galaxy.util.path import safe_relpath
from ._util import fix_permissions
from .caching import (
    CacheTarget,
    InProcessCacheMonitor,
)

log = logging.getLogger(__name__)


class CachingConcreteObjectStore(ConcreteObjectStore):
    staging_path: str
    extra_dirs: Dict[str, str]
    config: Any
    cache_updated_data: bool
    enable_cache_monitor: bool
    cache_size: int
    cache_monitor: Optional[InProcessCacheMonitor] = None
    cache_monitor_interval: int

    def _construct_path(
        self,
        obj,
        base_dir=None,
        dir_only=None,
        extra_dir=None,
        extra_dir_at_root=False,
        alt_name=None,
        obj_dir=False,
        in_cache=False,
        **kwargs,
    ):
        # extra_dir should never be constructed from provided data but just
        # make sure there are no shenannigans afoot
        if extra_dir and extra_dir != os.path.normpath(extra_dir):
            log.warning("extra_dir is not normalized: %s", extra_dir)
            raise ObjectInvalid("The requested object is invalid")
        # ensure that any parent directory references in alt_name would not
        # result in a path not contained in the directory path constructed here
        if alt_name:
            if not safe_relpath(alt_name):
                log.warning("alt_name would locate path outside dir: %s", alt_name)
                raise ObjectInvalid("The requested object is invalid")
            # alt_name can contain parent directory references, but S3 will not
            # follow them, so if they are valid we normalize them out
            alt_name = os.path.normpath(alt_name)

        object_id = self._get_object_id(obj)
        rel_path = os.path.join(*directory_hash_id(object_id))

        if extra_dir is not None:
            if extra_dir_at_root:
                rel_path = os.path.join(extra_dir, rel_path)
            else:
                rel_path = os.path.join(rel_path, extra_dir)

        # for JOB_WORK directory
        if obj_dir:
            rel_path = os.path.join(rel_path, str(object_id))
        if base_dir:
            base = self.extra_dirs.get(base_dir)
            assert base
            return os.path.join(base, rel_path)

        if not dir_only:
            rel_path = os.path.join(rel_path, alt_name if alt_name else f"dataset_{object_id}.dat")

        if in_cache:
            return self._get_cache_path(rel_path)

        return rel_path

    def _get_cache_path(self, rel_path: str) -> str:
        return os.path.abspath(os.path.join(self.staging_path, rel_path))

    def _in_cache(self, rel_path: str) -> bool:
        """Check if the given dataset is in the local cache and return True if so."""
        cache_path = self._get_cache_path(rel_path)
        return os.path.exists(cache_path)

    def _pull_into_cache(self, rel_path) -> bool:
        ipt_timer = ExecutionTimer()
        # Ensure the cache directory structure exists (e.g., dataset_#_files/)
        rel_path_dir = os.path.dirname(rel_path)
        if not os.path.exists(self._get_cache_path(rel_path_dir)):
            os.makedirs(self._get_cache_path(rel_path_dir), exist_ok=True)
        # Now pull in the file
        file_ok = self._download(rel_path)
        fix_permissions(self.config, self._get_cache_path(rel_path_dir))
        log.debug("_pull_into_cache: %s\n\n\n\n\n\n", ipt_timer)
        return file_ok

    def _get_data(self, obj, start=0, count=-1, **kwargs):
        rel_path = self._construct_path(obj, **kwargs)
        # Check cache first and get file if not there
        if not self._in_cache(rel_path):
            self._pull_into_cache(rel_path)
        # Read the file content from cache
        data_file = open(self._get_cache_path(rel_path))
        data_file.seek(start)
        content = data_file.read(count)
        data_file.close()
        return content

    def _exists(self, obj, **kwargs):
        in_cache = exists_remotely = False
        rel_path = self._construct_path(obj, **kwargs)
        dir_only = kwargs.get("dir_only", False)
        base_dir = kwargs.get("base_dir", None)

        # check job work directory stuff early to skip API hits.
        if dir_only and base_dir:
            if not os.path.exists(rel_path):
                os.makedirs(rel_path, exist_ok=True)
            return True

        in_cache = self._in_cache(rel_path)
        exists_remotely = self._exists_remotely(rel_path)
        dir_only = kwargs.get("dir_only", False)
        base_dir = kwargs.get("base_dir", None)
        if dir_only:
            if in_cache or exists_remotely:
                return True
            else:
                return False

        # TODO: Sync should probably not be done here. Add this to an async upload stack?
        if in_cache and not exists_remotely:
            self._push_to_os(rel_path, source_file=self._get_cache_path(rel_path))
            return True
        elif exists_remotely:
            return True
        else:
            return False

    def _create(self, obj, **kwargs):
        if not self._exists(obj, **kwargs):
            # Pull out locally used fields
            extra_dir = kwargs.get("extra_dir", None)
            extra_dir_at_root = kwargs.get("extra_dir_at_root", False)
            dir_only = kwargs.get("dir_only", False)
            alt_name = kwargs.get("alt_name", None)

            # Construct hashed path
            rel_path = os.path.join(*directory_hash_id(self._get_object_id(obj)))

            # Optionally append extra_dir
            if extra_dir is not None:
                if extra_dir_at_root:
                    rel_path = os.path.join(extra_dir, rel_path)
                else:
                    rel_path = os.path.join(rel_path, extra_dir)

            # Create given directory in cache
            cache_dir = os.path.join(self.staging_path, rel_path)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            # If instructed, create the dataset in cache & in S3
            if not dir_only:
                rel_path = os.path.join(rel_path, alt_name if alt_name else f"dataset_{self._get_object_id(obj)}.dat")
                open(os.path.join(self.staging_path, rel_path), "w").close()
                self._push_to_os(rel_path, from_string="")
        return self

    def _empty(self, obj, **kwargs):
        if self._exists(obj, **kwargs):
            return self._size(obj, **kwargs) == 0
        else:
            raise ObjectNotFound(f"objectstore.empty, object does not exist: {obj}, kwargs: {kwargs}")

    def _size(self, obj, **kwargs):
        rel_path = self._construct_path(obj, **kwargs)
        if self._in_cache(rel_path):
            try:
                return os.path.getsize(self._get_cache_path(rel_path))
            except OSError as ex:
                log.info("Could not get size of file '%s' in local cache, will try Azure. Error: %s", rel_path, ex)
        elif self._exists_remotely(rel_path):
            return self._get_remote_size(rel_path)
        log.warning("Did not find dataset '%s', returning 0 for size", rel_path)
        return 0

    def _get_filename(self, obj, **kwargs):
        base_dir = kwargs.get("base_dir", None)
        dir_only = kwargs.get("dir_only", False)
        obj_dir = kwargs.get("obj_dir", False)
        sync_cache = kwargs.get("sync_cache", True)

        rel_path = self._construct_path(obj, **kwargs)

        # for JOB_WORK directory
        if base_dir and dir_only and obj_dir:
            return os.path.abspath(rel_path)

        cache_path = self._get_cache_path(rel_path)
        if not sync_cache:
            return cache_path

        # Check if the file exists in the cache first, always pull if file size in cache is zero
        if self._in_cache(rel_path) and (dir_only or os.path.getsize(self._get_cache_path(rel_path)) > 0):
            return cache_path

        # Check if the file exists in persistent storage and, if it does, pull it into cache
        elif self._exists(obj, **kwargs):
            if dir_only:
                self._download_directory_into_cache(rel_path, cache_path)
                return cache_path
            else:
                if self._pull_into_cache(rel_path):
                    return cache_path
        raise ObjectNotFound(f"objectstore.get_filename, no cache_path: {obj}, kwargs: {kwargs}")

    def _download_directory_into_cache(self, rel_path, cache_path):
        # azure, pithos, irod, and cloud did not do this prior to refactoring so I am assuming
        # there is just operations that fail with these object stores,
        # I'm placing a no-op here to match their behavior but we should
        # maybe implement this for those object stores.
        pass

    def _delete(self, obj, entire_dir=False, **kwargs):
        rel_path = self._construct_path(obj, **kwargs)
        extra_dir = kwargs.get("extra_dir", None)
        base_dir = kwargs.get("base_dir", None)
        dir_only = kwargs.get("dir_only", False)
        obj_dir = kwargs.get("obj_dir", False)
        try:
            # Remove temporary data in JOB_WORK directory
            if base_dir and dir_only and obj_dir:
                shutil.rmtree(os.path.abspath(rel_path))
                return True

            # For the case of extra_files, because we don't have a reference to
            # individual files/keys we need to remove the entire directory structure
            # with all the files in it. This is easy for the local file system,
            # but requires iterating through each individual key in S3 and deleing it.
            if entire_dir and extra_dir:
                shutil.rmtree(self._get_cache_path(rel_path), ignore_errors=True)
                return self._delete_remote_all(rel_path)
            else:
                # Delete from cache first
                unlink(self._get_cache_path(rel_path), ignore_errors=True)
                # Delete from S3 as well
                if self._exists_remotely(rel_path):
                    return self._delete_existing_remote(rel_path)
        except OSError:
            log.exception("%s delete error", self._get_filename(obj, **kwargs))
        return False

    def _update_from_file(self, obj, file_name=None, create=False, **kwargs):
        if create:
            self._create(obj, **kwargs)

        if self._exists(obj, **kwargs):
            rel_path = self._construct_path(obj, **kwargs)
            # Chose whether to use the dataset file itself or an alternate file
            if file_name:
                source_file = os.path.abspath(file_name)
                # Copy into cache
                cache_file = self._get_cache_path(rel_path)
                try:
                    if source_file != cache_file and self.cache_updated_data:
                        # FIXME? Should this be a `move`?
                        shutil.copy2(source_file, cache_file)
                    fix_permissions(self.config, cache_file)
                except OSError:
                    log.exception("Trouble copying source file '%s' to cache '%s'", source_file, cache_file)
            else:
                source_file = self._get_cache_path(rel_path)

            self._push_to_os(rel_path, source_file)

        else:
            raise ObjectNotFound(
                f"objectstore.update_from_file, object does not exist: {str(obj)}, kwargs: {str(kwargs)}"
            )

    @property
    def cache_target(self) -> CacheTarget:
        print("GRABBING CACHE_TARGET>...")
        return CacheTarget(
            self.staging_path,
            self.cache_size,
            0.9,
        )

    def _shutdown_cache_monitor(self) -> None:
        self.cache_monitor and self.cache_monitor.shutdown()

    def _start_cache_monitor_if_needed(self):
        if self.enable_cache_monitor:
            self.cache_monitor = InProcessCacheMonitor(self.cache_target, self.cache_monitor_interval)

    def _get_remote_size(self, rel_path: str) -> int:
        raise NotImplementedError()

    def _exists_remotely(self, rel_path: str) -> bool:
        raise NotImplementedError()

    def _push_to_os(self, rel_path, source_file: Optional[str] = None, from_string: Optional[str] = None) -> None:
        raise NotImplementedError()

    # def _get_object_id(self, obj: Any) -> str:
    #    raise NotImplementedError()

    def _download(self, rel_path: str) -> bool:
        raise NotImplementedError()

    # Do not need to override these if instead replacing _delete
    def _delete_existing_remote(self, rel_path) -> bool:
        raise NotImplementedError()

    def _delete_remote_all(self, rel_path) -> bool:
        raise NotImplementedError()
