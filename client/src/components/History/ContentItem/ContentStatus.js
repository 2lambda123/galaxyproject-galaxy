export default {
    /** is uploading and not ready */
    upload: {
        status: "warning",
        text: "This dataset is currently uploading.",
    },
    /** the job that will produce the dataset queued in the runner */
    queued: {
        status: "warning",
        text: "This job is waiting to run.",
    },
    /** the job that will produce the dataset is running */
    running: {
        status: "warning",
        text: "This job is currently running.",
    },
    /** metadata for the dataset is being discovered/set */
    setting_metadata: {
        status: "warning",
        text: "Metadata is being auto-detected.",
    },
    /** was created without a tool */
    new: {
        status: "warning",
        text: "This is a new dataset and not all of its data are available yet.",
    },
    /** job is being created, but not put into job queue yet */
    waiting: {
        status: "default",
    },
    /** has no data */
    empty: {
        status: "danger",
        text: "No data",
    },
    /** has successfully completed running */
    ok: {
        status: "success",
    },
    /** the job that will produce the dataset paused */
    paused: {
        status: "info",
        text: "This job is paused. Use the 'Resume Paused Jobs' in the history menu to resume.",
    },
    /** metadata discovery/setting failed or errored (but otherwise ok) */
    failed_metadata: {
        status: "danger",
    },
    /** the tool producing this dataset failed */
    error: {
        status: "danger",
        text: "An error occurred with this dataset",
    },
    /** deleted while uploading */
    discarded: {
        status: "danger",
        text: "The job creating this dataset was cancelled before completion.",
    },
    //TODO: not in trans.app.model.Dataset.states - is in database
    /** not accessible to the current user (i.e. due to permissions) */
    noPermission: {
        status: "danger",
        text: "You do not have permission to view this dataset.",
    },
    // found in job-state summary model?
    // this an actual state value or something derived from deleted prop?
    deleted: {
        status: "danger",
    },
    loading: {
        status: "warning",
    },
};
