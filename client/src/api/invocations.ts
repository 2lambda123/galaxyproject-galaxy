import axios from "axios";

import { getAppRoot } from "@/onload";

import { ApiResponse, components, fetcher } from "./schema";

export type WorkflowInvocationElementView = components["schemas"]["WorkflowInvocationElementView"];
export type WorkflowInvocationCollectionView = components["schemas"]["WorkflowInvocationCollectionView"];
export type WorkflowInvocationStepStatesView = components["schemas"]["WorkflowInvocationStepStatesView"];
export type InvocationJobsSummary = components["schemas"]["InvocationJobsResponse"];
export type InvocationStep = components["schemas"]["InvocationStep"];

export const invocationsFetcher = fetcher.path("/api/invocations").method("get").create();
export const invocationFetcher = fetcher.path("/api/invocations/{invocation_id}").method("get").create();
export const jobsSummaryFetcher = fetcher.path("/api/invocations/{invocation_id}/jobs_summary").method("get").create();

export type WorkflowInvocation =
    | WorkflowInvocationElementView
    | WorkflowInvocationCollectionView
    | WorkflowInvocationStepStatesView;

export interface WorkflowInvocationStep {
    id: string;
}

export async function invocationForJob(params: { jobId: string }): Promise<WorkflowInvocation | null> {
    const { data } = await axios.get(`${getAppRoot()}api/invocations?job_id=${params.jobId}`);
    if (data.length > 0) {
        return data[0] as WorkflowInvocation;
    } else {
        return null;
    }
}

// TODO: Replace these provisional functions with fetchers after https://github.com/galaxyproject/galaxy/pull/16707 is merged
export async function fetchInvocationDetails(params: { id: string }): Promise<ApiResponse<WorkflowInvocation>> {
    const { data } = await invocationFetcher({ invocation_id: params.id });
    return {
        data,
    } as ApiResponse<WorkflowInvocation>;
}

export async function fetchInvocationStepStateDetails(params: {
    id: string;
}): Promise<ApiResponse<WorkflowInvocationStepStatesView>> {
    const { data } = await invocationFetcher({ invocation_id: params.id, view: "step_states" });
    return {
        data,
    } as ApiResponse<WorkflowInvocationStepStatesView>;
}

export async function fetchInvocationJobsSummary(params: { id: string }): Promise<ApiResponse<InvocationJobsSummary>> {
    const { data } = await jobsSummaryFetcher({ invocation_id: params.id });
    return {
        data,
    } as ApiResponse<InvocationJobsSummary>;
}

export async function fetchInvocationStep(params: { id: string }): Promise<ApiResponse<WorkflowInvocationStep>> {
    const { data } = await axios.get(`${getAppRoot()}api/invocations/steps/${params.id}`);
    return {
        data,
    } as ApiResponse<WorkflowInvocationStep>;
}
