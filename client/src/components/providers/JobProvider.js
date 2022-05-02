import axios from "axios";
import { getAppRoot } from "onload/loadConfig";
import { SingleQueryProvider } from "components/providers/SingleQueryProvider";
import { rethrowSimple } from "utils/simple-error";
import { stateIsTerminal } from "./utils";
import { cleanPaginationParameters } from "./utils";

async function jobDetails({ jobid }) {
    const url = `${getAppRoot()}api/jobs/${jobid}?full=True`;
    try {
        const { data } = await axios.get(url);
        return data;
    } catch (e) {
        rethrowSimple(e);
    }
}

async function jobProblems({ jobid }) {
    const url = `${getAppRoot()}api/jobs/${jobid}/common_problems`;
    try {
        const { data } = await axios.get(url);
        return data;
    } catch (e) {
        rethrowSimple(e);
    }
}

export const JobDetailsProvider = SingleQueryProvider(jobDetails, stateIsTerminal);
export const JobProblemProvider = SingleQueryProvider(jobProblems, stateIsTerminal);

export function jobsProvider(ctx, callback, extraParams = {}) {
    const { apiUrl, ...requestParams } = ctx;
    const cleanParams = cleanPaginationParameters(requestParams);
    const promise = axios.get(apiUrl, { params: { ...cleanParams, ...extraParams } });

    // Must return a promise that resolves to an array of items
    return promise.then((data) => {
        // Pluck the array of items off our axios response
        const items = data.data;
        callback && callback(data);
        // Must return an array of items or an empty array if an error occurred
        return items || [];
    });
}
