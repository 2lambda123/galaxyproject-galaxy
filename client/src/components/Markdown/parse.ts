const FUNCTION_ARGUMENT_VALUE_REGEX = `\\s*(?:[\\w_\\-]+|\\"[^\\"]+\\"|\\'[^\\']+\\')\\s*`;
const FUNCTION_ARGUMENT_REGEX = `\\s*[\\w\\|]+\\s*=` + FUNCTION_ARGUMENT_VALUE_REGEX;
const FUNCTION_CALL_LINE = `\\s*(\\w+)\\s*\\(\\s*(?:(${FUNCTION_ARGUMENT_REGEX})(,${FUNCTION_ARGUMENT_REGEX})*)?\\s*\\)\\s*`;
const FUNCTION_CALL_LINE_TEMPLATE = new RegExp(FUNCTION_CALL_LINE, "m");

type DefaultSection = { name: "default"; content: string };
type GalaxyDirectiveSection = { name: string; content: string; args: { [key: string]: string } };
type Section = DefaultSection | GalaxyDirectiveSection;

type WorkflowLabelKind = "input" | "output" | "step";

export function splitMarkdown(markdown: string, preserveWhitespace: boolean = false) {
    const sections: Section[] = [];
    const markdownErrors = [];
    let digest = markdown;
    while (digest.length > 0) {
        const galaxyStart = digest.indexOf("```galaxy");
        if (galaxyStart != -1) {
            const galaxyEnd = digest.substr(galaxyStart + 1).indexOf("```");
            if (galaxyEnd != -1) {
                if (galaxyStart > 0) {
                    const rawContent = digest.substr(0, galaxyStart);
                    const defaultContent = rawContent.trim();
                    if (preserveWhitespace || defaultContent) {
                        sections.push({
                            name: "default",
                            content: preserveWhitespace ? rawContent : defaultContent,
                        });
                    }
                }
                const galaxyEndIndex = galaxyEnd + 4;
                const galaxySection = digest.substr(galaxyStart, galaxyEndIndex);
                let args = null;
                try {
                    args = getArgs(galaxySection);
                    sections.push(args);
                } catch (e) {
                    markdownErrors.push({
                        error: "Found an unresolved tag.",
                        line: galaxySection,
                    });
                }
                digest = digest.substr(galaxyStart + galaxyEndIndex);
            } else {
                digest = digest.substr(galaxyStart + 1);
            }
        } else {
            sections.push({
                name: "default",
                content: digest,
            });
            break;
        }
    }
    return { sections, markdownErrors };
}

export function replaceLabel(
    markdown: string,
    labelType: WorkflowLabelKind,
    fromLabel: string,
    toLabel: string
): string {
    const { sections } = splitMarkdown(markdown, true);

    function rewriteSection(section: Section) {
        if ("args" in section) {
            const directiveSection = section as GalaxyDirectiveSection;
            const args = directiveSection.args;
            if (!(labelType in args)) {
                return section;
            }
            const labelValue = args[labelType];
            if (labelValue != fromLabel) {
                return section;
            }
            // we've got a section with a matching label and type...
            const newArgs = { ...args };
            newArgs[labelType] = toLabel;
            const argRexExp = namedArgumentRegex(labelType);
            const escapedToLabel = escapeRegExpReplacement(toLabel);
            const content = directiveSection.content.replace(argRexExp, `$1${escapedToLabel}`);
            return {
                name: directiveSection.name,
                args: newArgs,
                content: content,
            };
        } else {
            return section;
        }
    }

    const rewrittenSections = sections.map(rewriteSection);
    const rewrittenMarkdown = rewrittenSections.map((section) => section.content).join("");
    return rewrittenMarkdown;
}

export function getArgs(content: string): GalaxyDirectiveSection {
    const galaxy_function = FUNCTION_CALL_LINE_TEMPLATE.exec(content);
    if (galaxy_function == null) {
        throw Error("Failed to parse galaxy directive");
    }
    type ArgsType = { [key: string]: string };
    const args: ArgsType = {};
    const function_name = galaxy_function[1] as string;
    // we need [... ] to return empty string, if regex doesn't match
    const function_arguments = [...content.matchAll(new RegExp(FUNCTION_ARGUMENT_REGEX, "g"))];
    for (let i = 0; i < function_arguments.length; i++) {
        if (function_arguments[i] === undefined) {
            continue;
        }
        const arguments_str = function_arguments[i]?.toString().replace(/,/g, "").trim();
        if (arguments_str) {
            const [key, val] = arguments_str.split("=");
            if (key == undefined || val == undefined) {
                throw Error("Failed to parse galaxy directive");
            }
            args[key.trim()] = val.replace(/['"]+/g, "").trim();
        }
    }
    return {
        name: function_name,
        args: args,
        content: content,
    };
}

function namedArgumentRegex(argument: string): RegExp {
    return new RegExp(`(\\s*${argument}\\s*=)` + FUNCTION_ARGUMENT_VALUE_REGEX);
}

// https://stackoverflow.com/questions/3446170/escape-string-for-use-in-javascript-regex
function escapeRegExpReplacement(value: string): string {
    return value.replace(/\$/g, "$$$$");
}
