import { getArgs, replaceLabel, splitMarkdown } from "./parse";

describe("parse.ts", () => {
    describe("getArgs", () => {
        it("parses simple directive expression", () => {
            const args = getArgs("job_metrics(job_id=THISFAKEID)");
            expect(args.name).toBe("job_metrics");
        });
    });

    describe("splitMarkdown", () => {
        it("strip leading whitespace by default", () => {
            const { sections } = splitMarkdown("\n```galaxy\njob_metrics(job_id=THISFAKEID)\n```");
            expect(sections.length).toBe(1);
        });

        it("should not strip leading whitespace if disabled", () => {
            const { sections } = splitMarkdown("\n```galaxy\njob_metrics(job_id=THISFAKEID)\n```", true);
            expect(sections.length).toBe(2);
            expect(sections[0].content).toBe("\n");
        });
    });

    describe("replaceLabel", () => {
        it("should leave unaffected markdown alone", () => {
            const input = "some random\n`markdown content`\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(result);
        });

        it("should leave unaffected galaxy directives alone", () => {
            const input = "some random\n`markdown content`\n```galaxy\ncurrent_time()\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(result);
        });

        it("should leave galaxy directives of same type with other labels alone", () => {
            const input = "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(output=moo)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(result);
        });

        it("should leave galaxy directives of other types with same labels alone", () => {
            const input = "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(input=from)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(result);
        });

        it("should swap simple directives of specified type", () => {
            const input = "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(output=from)\n```\n";
            const output = "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(output=to)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(output);
        });

        it("should swap single quoted directives of specified type", () => {
            const input = "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(output='from')\n```\n";
            const output = "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(output=to)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(output);
        });

        it("should swap single quoted directives of specified type with extra args", () => {
            const input =
                "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(footer='cow', output='from', title=dog)\n```\n";
            const output =
                "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(footer='cow', output=to, title=dog)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(output);
        });

        it("should swap double quoted directives of specified type", () => {
            const input = 'some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(output="from")\n```\n';
            const output = "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(output=to)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(output);
        });

        it("should swap double quoted directives of specified type with extra args", () => {
            const input =
                "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(footer='cow', output=\"from\", title=dog)\n```\n";
            const output =
                "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(footer='cow', output=to, title=dog)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(output);
        });

        it("should leave non-arguments alone", () => {
            const input =
                "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(title='cow from farm', output=from)\n```\n";
            const output =
                "some random\n`markdown content`\n```galaxy\nhistory_dataset_embedded(title='cow from farm', output=to)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(output);
        });

        // not a valid workflow label per se but make sure we're escaping the regex to be safe
        it("should not be messed up by labels containing regexp content", () => {
            const input = "```galaxy\nhistory_dataset_embedded(output='from(')\n```\n";
            const output = "```galaxy\nhistory_dataset_embedded(output=to$1)\n```\n";
            const result = replaceLabel(input, "output", "from(", "to$1");
            expect(result).toBe(output);
        });

        it("should not swallow leading newlines", () => {
            const input = "\n```galaxy\nhistory_dataset_embedded(output='from')\n```\n";
            const output = "\n```galaxy\nhistory_dataset_embedded(output=to)\n```\n";
            const result = replaceLabel(input, "output", "from", "to");
            expect(result).toBe(output);
        });
    });
});
