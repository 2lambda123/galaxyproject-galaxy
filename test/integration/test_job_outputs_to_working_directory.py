"""Run various framework tool tests with outputs_to_working_directory."""

from base import integration_util


class JobOutputsToWorkingDirectoryIntegrationInstance(integration_util.IntegrationInstance):
    """Describe a Galaxy test instance with embedded pulsar configured."""

    framework_tool_and_types = True

    @classmethod
    def handle_galaxy_config_kwds(cls, config):
        config["outputs_to_working_directory"] = True


instance = integration_util.integration_module_instance(JobOutputsToWorkingDirectoryIntegrationInstance)

test_tools = integration_util.integration_tool_runner(["output_format", "output_empty_work_dir", "collection_creates_pair_from_work_dir"])
