import axios from "axios";
import { getAppRoot } from "onload/loadConfig";
import { rethrowSimple } from "utils/simple-error";

export async function sendErrorReportTool(dataset, message, email, transcript) {
    const payload = {
        dataset_id: dataset.id,
        message,
        email,
        transcript,
    };
    const url = `${getAppRoot()}api/user-reporting/error`;
    try {
        const { data } = await axios.post(url, payload);
        return data.messages;
    } catch (e) {
        rethrowSimple(e);
    }
}
