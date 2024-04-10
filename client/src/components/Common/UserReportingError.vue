<template>
    <div>
        <div class="page-container edit-attr">
            <div class="response-message"></div>
        </div>
        <h3 class="h-lg">Dataset Error Report</h3>
        <p v-if="notifications && !notifications.variant" v-html="notifications[0].text" />
        <span v-else-if="notifications && notifications.variant">
            <BAlert :variant="notifications.variant">
                <span v-html="notifications[0].text" />
            </BAlert>
        </span>
        <div v-if="hasDetails(commandOutputs)">
            <h4 class="h-md">Details</h4>
            <div v-for="(commandOutput, index) in commandOutputs" :key="index">
                <div v-if="hasMessages(commandOutput.detail)">
                    <p class="mt-3 mb-1">{{ commandOutput.text }}</p>
                    <div v-for="(value, index) in commandOutput.detail" :key="index">
                        <pre class="rounded code">{{ value }}</pre>
                    </div>
                </div>
            </div>
        </div>
        <h4 class="mt-3 h-md">Troubleshooting</h4>
        <p>
            There are a number of helpful resources to self diagnose and correct problems.
            <br />
            Start here:
            <b>
                <a
                    href="https://training.galaxyproject.org/training-material/faqs/galaxy/analysis_troubleshooting.html"
                    target="_blank">
                    My job ended with an error. What can I do?
                </a>
            </b>
        </p>
        <h4 class="mb-3 h-md">Issue Report</h4>
        <BAlert v-for="(resultMessage, index) in resultMessages" :key="index" :variant="resultMessage[1]" show>
            <span v-html="renderMarkdown(resultMessage[0])"></span>
        </BAlert>
        <div v-if="showForm" id="fieldsAndButton">
            <span class="mr-2 font-weight-bold">{{ "Your email address" | l }}</span>
            <span v-if="!!currentUser?.email">{{ currentUser?.email }}</span>
            <span v-else>{{ "You must be logged in to receive emails" | l }}</span>
            <FormElement
                id="dataset-error-message"
                v-model="message"
                :area="true"
                title="Please provide detailed information on the activities leading to this issue:" />
            <BLink
                :aria-expanded="isExpanded ? 'true' : 'false'"
                aria-controls="collapse-previous"
                @click="isExpanded = !isExpanded">
                ({{ title }}) Error transcript:
            </BLink>
            <BCollapse id="collapse-previous" v-model="isExpanded">
                <pre class="rounded code">{{ transcript }}</pre></BCollapse
            ><br />
            <BButton
                id="dataset-error-submit"
                variant="primary"
                class="mt-3"
                :disabled="disableSubmit"
                @click="submit(currentUser?.email)">
                <FontAwesomeIcon icon="bug" class="mr-1" />Report
            </BButton>
        </div>
    </div>
</template>

<script>
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { BAlert, BButton, BCollapse, BLink } from "bootstrap-vue";
import FormElement from "components/Form/FormElement";
import { mapState } from "pinia";

import { getGalaxyInstance } from "@/app";
import { useMarkdown } from "@/composables/markdown";
import { useUserStore } from "@/stores/userStore";

import { sendErrorReport } from "../DatasetInformation/services";

export default {
    components: {
        FontAwesomeIcon,
        FormElement,
        BAlert,
        BButton,
        BCollapse,
        BLink,
    },
    props: {
        dataset: {
            type: Object,
            required: false,
            default: () => {},
        },
        commandOutputs: {
            type: Array,
            default: () => [],
        },
        notifications: {
            type: Array,
            default: () => [],
        },
        transcript: {
            type: String,
            default: "",
        },
    },
    setup() {
        const { renderMarkdown } = useMarkdown({ openLinksInNewPage: true });
        return { renderMarkdown };
    },
    data() {
        return {
            message: null,
            errorMessage: null,
            resultMessages: [],
            isExpanded: false,
        };
    },
    computed: {
        ...mapState(useUserStore, ["currentUser"]),
        showForm() {
            const noResult = !this.resultMessages.length;
            const hasError = this.resultMessages.some((msg) => msg[1] === "danger");
            return noResult || hasError;
        },
        disableSubmit() {
            const isEmailActive = !getGalaxyInstance().config.show_inactivity_warning;
            return !this.currentUser?.email || !isEmailActive;
        },
        title() {
            return this.isExpanded ? `-` : `+`;
        },
    },
    methods: {
        onError(err) {
            this.errorMessage = err;
        },
        submit(userEmailJob) {
            const email = userEmailJob || this.currentUserEmail;
            const message = this.message;
            const report_type = this.transcript ? "tool" : "dataset";
            sendErrorReport(email, message, report_type, this.dataset, this.transcript).then(
                (resultMessages) => {
                    this.resultMessages = resultMessages;
                },
                (errorMessage) => {
                    this.errorMessage = errorMessage;
                }
            );
        },
        hasDetails(outputs) {
            return (
                outputs
                    .map(({ detail }) => detail)
                    .flat(Infinity)
                    .filter((item) => item.length > 0).length > 0
            );
        },
        hasMessages(output) {
            return output.filter((item) => item.length > 0).length > 0;
        },
    },
};
</script>
