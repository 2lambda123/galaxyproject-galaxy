import { useLocalStorage } from "@vueuse/core";
import { computed, customRef, ref } from "vue";

import { useHashedUserId } from "./hashedUserId";

/**
 * Local storage composable specific to current user.
 * @param key
 * @param initialValue
 */
export function useUserLocalStorage<T>(key: string, initialValue: T) {
    const { hashedUserId } = useHashedUserId();

    const storedRef = computed(() => {
        if (hashedUserId.value) {
            return useLocalStorage(`${key}-${hashedUserId.value}`, initialValue);
        } else {
            return ref(initialValue);
        }
    });

    const currentValue = customRef((track, trigger) => ({
        get() {
            track();
            return storedRef.value.value;
        },
        set(newValue) {
            storedRef.value.value = newValue;
            trigger();
        },
    }));

    return currentValue;
}
