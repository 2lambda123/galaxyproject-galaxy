import { contentUpdate, getAllContentByFilter } from "./queries";

/**
 * Content operations
 */

export async function hideSelectedContent(history, type_ids) {
    return await contentUpdate(history, type_ids, {
        visible: false,
    });
}

export async function unhideSelectedContent(history, type_ids) {
    return await contentUpdate(history, type_ids, {
        visible: true,
    });
}

export async function deleteSelectedContent(history, type_ids) {
    return await contentUpdate(history, type_ids, {
        deleted: true,
    });
}

export async function undeleteSelectedContent(history, type_ids) {
    return await contentUpdate(history, type_ids, {
        deleted: false,
    });
}

export async function purgeSelectedContent(history, type_ids) {
    return await contentUpdate(history, type_ids, {
        deleted: true,
        purged: true,
    });
}

export async function unhideAllHiddenContent(history) {
    const filter = { visible: false };
    const selection = await getAllContentByFilter(history, filter);
    if (selection.length) {
        const type_ids = selection.map((c) => c.type_id);
        return await unhideSelectedContent(history, type_ids);
    }
    return [];
}

export async function deleteAllHiddenContent(history) {
    const filter = { visible: false };
    const selection = await getAllContentByFilter(history, filter);
    if (selection.length) {
        const type_ids = selection.map((c) => c.type_id);
        return await deleteSelectedContent(history, type_ids);
    }
    return [];
}

export async function purgeAllDeletedContent(history) {
    const filter = { deleted: true, purged: false };
    const selection = await getAllContentByFilter(history, filter);
    if (selection.length) {
        const type_ids = selection.map((c) => c.type_id);
        return await purgeSelectedContent(history, type_ids);
    }
    return [];
}
