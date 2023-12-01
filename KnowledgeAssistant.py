
# Importing Dependencies
import streamlit as st
import json
from openai import AzureOpenAI
from langchain.tools import BaseTool


st.title("Knowledge Assistant")


# Setting up AzureOpenAI Environment
client = AzureOpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_version= "2023-07-01-preview",
    api_key="a5c4e09a50dd4e13a69e7ef19d07b48c",
    # base_url="https://danielingitaraj.openai.azure.com/"
    base_url="https://danielingitaraj.openai.azure.com/openai/deployments/DanielGPT4/chat/completions?api-version=2023-07-01-preview"
)


# Initializing chat history

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":"You are a knowledge assistant dedicated to sharing information and assisting learners.\nYour responses are informative and designed to aid learning. You offer explanations, examples, and resources to support the learning process. Remember current date is 30/11/2023 and for getting latest data you can search the internet using master_search. And finally provide a detailed descriptive answer with source attribution."}]

# Display chat messages from history on app rerun
for message in st.session_state.messages[1:]:
    try:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # st.markdown(message.content)
    except:
        continue


from duckduckgo_search import DDGS
import asyncio
import json
from typing import Optional

# tool function

async def master_search(input_json: str) -> dict:
    params = json.loads(input_json)

    operation = params.get('operation')
    keywords = params.get('keywords')
    region = params.get('region', 'wt-wt')
    max_results = params.get('max_results', 5)
    to_lang = params.get('to_lang', 'en')
    place = params.get('place')

    with DDGS() as ddgs:
        if operation == 'text':
            return [r for r in ddgs.text(keywords, region=region, max_results=max_results)]
        elif operation == 'image':
            return [r for r in ddgs.images(keywords, region=region, max_results=max_results)]
        elif operation == 'video':
            return [r for r in ddgs.videos(keywords, region=region, max_results=max_results)]
        elif operation == 'news':
            return [r for r in ddgs.news(keywords, region=region, max_results=max_results)]
        elif operation == 'map':
            return [r for r in ddgs.maps(keywords, place=place, max_results=max_results)]
        elif operation == 'translate':
            return ddgs.translate(keywords, to=to_lang)
        elif operation == 'suggestions':
            return [r for r in ddgs.suggestions(keywords, region=region)]
        else:
            raise ValueError("Invalid operation. Please choose from: 'text', 'image', 'video', 'news', 'map', 'translate', 'suggestions'.")

async def async_master_search(input_json):
    result = await master_search(input_json)
    return result



# Defining the tools or functions
functions = [
                {
                    "name": "master_search",
                    "description": "Utilizes multiple search operations (text, image, video, news, map, translate, suggestions) to retrieve relevant information based on the specified operation and keywords. This tool is designed to provide diverse search capabilities using a single function.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "The type of search operation to perform. Options include 'text', 'image', 'video', 'news', 'map', 'translate', 'suggestions'."
                            },
                            "keywords": {
                                "type": "string",
                                "description": "The keywords to search for in the specified operation."
                            },
                            "region": {
                                "type": "string",
                                "description": "Optional. The region to perform the search in. Defaults to 'wt-wt'."
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Optional. The maximum number of results to return. If not provided, all results will be returned."
                            },
                            "to_lang": {
                                "type": "string",
                                "description": "Optional. The target language for the 'translate' operation. Defaults to 'en'."
                            },
                            "place": {
                                "type": "string",
                                "description": "Optional. The place for the 'map' operation. If not provided, the 'keywords' parameter will be used."
                            }
                        },
                        "required": ["operation", "keywords"]
                    }
                }
            ]


# get completions

def get_completion(messages=None, func=None, function_call="auto",
                   temperature=0, max_tokens=1000, top_p=1, frequency_penalty=0,
                   presence_penalty=0, stop=None):
    # Set default values if parameters are not provided
    messages = messages or []
    functions = func or []
    
    # Make API call with provided parameters
    response = client.chat.completions.create(
        messages= messages,
        model="DanielGPT4",
        functions=func,
        function_call=function_call,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop
    )
    return response.choices[0].message



def get_answer():
    message = st.session_state.messages.copy()
    with st.spinner("Thinking..."):

        response = get_completion(messages=message, func=functions)
        print(response)

        while True:
            if response.function_call:
                response.content = "null"
                message.append(response)
                function_name = response.function_call.name

                if function_name == "master_search":
                    print("Searching Internet")
                    with st.expander("Searching Internet..."):
                        st.write(json.loads(response.function_call.arguments))

                    # Call the asynchronous master_search function
                    function_response = asyncio.run(async_master_search(response.function_call.arguments))
                    print(function_response)

                    # st.experimental_show("Searching Internet Completed.")


                    message.append({
                        "role": "function",
                        "name": function_name,
                        "content": str(function_response),
                    })

                    print(function_response)
                    with st.expander("Extracting Details..."):
                        st.write(str(function_response)[:100])

                    response = get_completion(messages=message, func=functions)
                    print(response)

                    continue

            else:
                with st.expander("Generating Response"):
                    st.write("...")
                print("Returning Final Response")

                st.session_state.messages.append({"role": "assistant", "content": response.content})
                # print(response)

                return response.content







# def get_answer():
#     message  = st.session_state.messages.copy()
#     # print(message)
#     print("Generating First Response")
#     with st.spinner("Thinking..."):
#         # think = st.empty()
#         response = get_completion(messages= message, func= functions)
#         # print(response)

#         while True:
#             if response.function_call:
#                 # st.write()
#                 response.content = "null"
#                 message.append(response)
#                 function_name = response.function_call.name
#                 if function_name == "master_search":
#                     print("Searching Internet")
#                     loop = asyncio.get_event_loop()
#                     function_response = loop.run_until_complete(master_search(response.function_call.arguments))

#                     print(function_response)
#                     with st.expander("Searching Internet"):
#                         st.write(json.loads(response.function_call.arguments))
#                     message.append(
#                         {
#                             "role": "function",
#                             "name": function_name,
#                             "content": function_response,
#                         }
#                     )
#                     print(message)
#                     with st.expander("Extracting Details"):
#                         st.write(function_response[:100]+"...")
#                     print("generating response after function call")
#                     # response = get_completion(messages= message, functions= functions)
#                     response = get_completion(messages= message, func= functions)
#                     print(response)
#                     continue
#             else:
#                 with st.expander("Generating Response"):
#                     st.write("...")
#                     # time.sleep(2)
#                 print("Returning Final Response")
#                 st.session_state.messages.append({"role": "assistant", "content": response.content})
#                 print(response)
#                 return response.content


# Accept user input
if prompt := st.chat_input("Enter your query here."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    answer = get_answer()

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(answer)
