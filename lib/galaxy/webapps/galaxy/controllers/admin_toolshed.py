import json
import logging
import os

from tool_shed.util import repository_util
from galaxy import util, web
from .admin import AdminGalaxy

log = logging.getLogger(__name__)


class AdminToolshed(AdminGalaxy):

    @web.expose
    def display_image_in_repository(self, trans, **kwd):
        """
        Open an image file that is contained in an installed tool shed repository or that is referenced by a URL for display.  The
        image can be defined in either a README.rst file contained in the repository or the help section of a Galaxy tool config that
        is contained in the repository.  The following image definitions are all supported.  The former $PATH_TO_IMAGES is no longer
        required, and is now ignored.
        .. image:: https://raw.github.com/galaxy/some_image.png
        .. image:: $PATH_TO_IMAGES/some_image.png
        .. image:: /static/images/some_image.gif
        .. image:: some_image.jpg
        .. image:: /deep/some_image.png
        """
        repository_id = kwd.get('repository_id', None)
        relative_path_to_image_file = kwd.get('image_file', None)
        if repository_id and relative_path_to_image_file:
            repository = repository_util.get_tool_shed_repository_by_id(trans.app, repository_id)
            if repository:
                repo_files_dir = repository.repo_files_directory(trans.app)
                # The following line sometimes returns None.  TODO: Figure out why.
                path_to_file = repository_util.get_absolute_path_to_file_in_repository(repo_files_dir, relative_path_to_image_file)
                if path_to_file and os.path.exists(path_to_file):
                    file_name = os.path.basename(relative_path_to_image_file)
                    try:
                        extension = file_name.split('.')[-1]
                    except Exception:
                        extension = None
                    if extension:
                        mimetype = trans.app.datatypes_registry.get_mimetype_by_extension(extension)
                        if mimetype:
                            trans.response.set_content_type(mimetype)
                    return open(path_to_file, 'rb')
        return None
