import requests
import urllib


def __append_word_to_user_agent(word):

    # set requests User-Agent
    old_default_user_agent = requests.utils.default_user_agent

    def new_default_user_agent(*args):
        return f"{old_default_user_agent(*args)} {word}"

    requests.utils.default_user_agent = new_default_user_agent

    # set urllib User-Agent
    old_build_opener = urllib.request.build_opener

    # def old_user_agent(opener):
    #     user_agent_tuple = next((t for t in opener.addheaders
    #         if t[0].lower() == 'user-agent'), None)
    #     if user_agent_tuple is None:
    #         return f"Python-urllib/{urllib.request.__version__}"
    #     else:
    #         return user_agent_tuple[1]

    def modify_user_agent_header(header):
        if header[0].lower() == "user-agent":
            return (header[0], f"{header[1]} {word}")
        return header

    def new_build_opener(*handlers):
        opener = old_build_opener(*handlers)
        # agent = f"{old_user_agent(opener)} {word}"
        # opener.addheaders.append(("User-Agent", agent))
        opener.addheaders = [ modify_user_agent_header(header)
           for header in opener.addheaders ]
        return opener

    urllib.request.build_opener = new_build_opener


__append_word_to_user_agent("galaxy")
