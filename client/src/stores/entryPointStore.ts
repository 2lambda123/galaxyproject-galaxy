import axios from "axios";
import isEqual from "lodash.isequal";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { useResourceWatcher } from "@/composables/resourceWatcher";
import { getAppRoot } from "@/onload/loadConfig";
import { rethrowSimple } from "@/utils/simple-error";

const ACTIVE_POLLING_INTERVAL = 10000;

// TODO: replace with the corresponding autogenerated model when ready
interface EntryPoint {
    model_class: "InteractiveToolEntryPoint";
    id: string;
    job_id: string;
    name: string;
    active: boolean;
    created_time: string;
    modified_time: string;
    output_datasets_ids: string[];
    target?: string;
}

export const useEntryPointStore = defineStore("entryPointStore", () => {
    const { startWatchingResource: startWatchingEntryPoints } = useResourceWatcher(fetchEntryPoints, {
        shortPollingInterval: ACTIVE_POLLING_INTERVAL,
        enableBackgroundPolling: false, // No need to poll in the background
    });

    const entryPoints = ref<EntryPoint[]>([]);

    const entryPointsForJob = computed(() => {
        return (jobId: string) => entryPoints.value.filter((entryPoint) => entryPoint["job_id"] === jobId);
    });

    const entryPointsForHda = computed(() => {
        return (hdaId: string) =>
            entryPoints.value.filter((entryPoint) => entryPoint["output_datasets_ids"].includes(hdaId));
    });

    async function fetchEntryPoints() {
        const url = `${getAppRoot()}api/entry_points`;
        const params = { running: true };
        try {
            const response = await axios.get(url, { params: params });
            updateEntryPoints(response.data);
        } catch (e) {
            rethrowSimple(e);
        }
    }

    function updateEntryPoints(data: EntryPoint[]) {
        let hasChanged = entryPoints.value.length !== data.length ? true : false;
        if (entryPoints.value.length === 0) {
            entryPoints.value = data;
        } else {
            const newEntryPoints = [];
            for (const ep of data) {
                const olderEntryPoint = entryPoints.value.filter((item) => item.id === ep.id)[0];
                if (!hasChanged && !isEqual(olderEntryPoint, ep)) {
                    hasChanged = true;
                }
                if (olderEntryPoint) {
                    newEntryPoints.push(mergeEntryPoints(olderEntryPoint, ep));
                }
            }
            if (hasChanged) {
                entryPoints.value = newEntryPoints;
            }
        }
    }

    function mergeEntryPoints(original: EntryPoint, updated: EntryPoint) {
        return { ...original, ...updated };
    }

    function removeEntryPoint(toolId: string) {
        const index = entryPoints.value.findIndex((ep) => {
            return ep.id === toolId ? true : false;
        });
        if (index >= 0) {
            entryPoints.value.splice(index, 1);
        }
    }

    return {
        entryPoints,
        entryPointsForJob,
        entryPointsForHda,
        fetchEntryPoints,
        updateEntryPoints,
        removeEntryPoint,
        startWatchingEntryPoints,
    };
});
