import axios from "axios";
import { getAppRoot } from "onload/loadConfig";
import { rethrowSimple } from "utils/simple-error";

export async function sendErrorReport(email, message, report_type = "dataset", dataset = {}, transcript = null) {
    let url = "";
    const payload = {
        dataset_id: dataset.id,
        message,
        email,
        transcript,
    };
    if (report_type == "tool") {
        url = `${getAppRoot()}api/user-reporting/error`;
    } else {
        url = `${getAppRoot()}api/jobs/${dataset.creating_job}/error`;
    }
    try {
        const { data } = await axios.post(url, payload);
        return data.messages;
    } catch (e) {
        rethrowSimple(e);
    }
}

export async function setAttributes(datasetId, settings, operation) {
    const payload = {
        dataset_id: datasetId,
        operation: operation,
        ...settings,
    };
    const url = `${getAppRoot()}dataset/set_edit`;
    try {
        const { data } = await axios.put(url, payload);
        return data;
    } catch (e) {
        rethrowSimple(e);
    }
}
