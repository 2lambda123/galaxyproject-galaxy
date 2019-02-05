/**
 * Central Vuex store
 */

import Vue from "vue";
import Vuex from "vuex";

// initial use of central store for search parameter housing. Test was to see if
// we could set store values from a component (CommunityTags.vue) and observe
// changes in legacy code (see grid-view.js)
import { gridSearchStore } from "./gridSearchStore";
import { tagStore } from "./tagStore";

Vue.use(Vuex);

export default new Vuex.Store({
    modules: { 
        gridSearch: gridSearchStore, 
        tags: tagStore 
    }
});
