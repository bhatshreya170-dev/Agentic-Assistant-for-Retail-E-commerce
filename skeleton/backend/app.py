import os
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool
from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
import time
from queue import Queue, Empty
import threading
import random
import re
from langchain.memory import ConversationBufferMemory

# Custom Callback Handler to capture agent steps and yield them for streaming
class AgentStepCallbackHandler(BaseCallbackHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_agent_action(self, action, **kwargs):
        self.queue.put({"type": "action", "tool": action.tool, "tool_input": action.tool_input, "log": action.log})

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.queue.put({"type": "tool_start", "tool_name": serialized["name"], "input": input_str})

    def on_tool_end(self, output, **kwargs):
        self.queue.put({"type": "tool_end", "output": output})

    def on_agent_finish(self, finish, **kwargs):
        self.queue.put({"type": "agent_finish", "log": finish.log})
        
        output_str = finish.return_values["output"]
        
        try:
            # The output from the agent should be a JSON string.
            # First, let's try to clean it up from common LLM mistakes.
            
            # 1. Remove markdown fences
            cleaned_str = re.sub(r"```json\n?|\n?```", "", output_str)
            
            # 2. Replace single quotes with double quotes
            cleaned_str = cleaned_str.replace("'", '"')
            
            # 3. Fix missing comma between properties on different lines
            cleaned_str = re.sub(r'"\s*\n\s*"', '",\n"', cleaned_str)
            
            # 4. Try to parse it
            json.loads(cleaned_str)
            
            # If it parses, we send it
            self.queue.put({"type": "final_answer", "content": cleaned_str})

        except Exception as e:
            # If parsing fails after all our attempts, it means the LLM
            # produced a severely malformed output.
            print(f"--- ERROR: Could not parse LLM output as JSON ---\n{output_str}\n---")
            error_message = "I'm sorry, I seem to have gotten my thoughts tangled up and couldn't format my response correctly. Could you please try rephrasing your request?"
            # We still need to send a valid JSON object in the 'final_answer'
            error_json = json.dumps({"conversation": error_message})
            self.queue.put({"type": "final_answer", "content": error_json})

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        # This can be used for streaming LLM output token by token if needed
        # For now, we'll focus on agent steps and final answer
        pass


# Load environment variables
load_dotenv()

# --- Data Loading ---
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, "data/products.json"), "r") as f:
        products = json.load(f)
    with open(os.path.join(base_dir, "data/projects.json"), "r") as f:
        projects = json.load(f)
    with open(os.path.join(base_dir, "data/trends.json"), "r") as f:
        trends = json.load(f)
    return products, projects, trends

PRODUCTS, PROJECTS, TRENDS = load_data()

# --- Agent Tools ---

@tool
def get_trend(query: str) -> str:
    """
    Identifies a trend from the user's query based on keywords.
    This simulates the Trend Spotter Agent.
    """
    query_lower = query.lower()
    for trend in TRENDS:
        for keyword in trend["keywords"]:
            if keyword in query_lower:
                print(f"Found trend: {trend['name']}")
                return trend["name"]
    return "No specific trend identified."

@tool
def get_projects_for_trend(trend_name: str) -> list[str]:
    """
    Finds all projects associated with a given trend and returns their names.
    This simulates the Project Planner Agent.
    """
    normalized_trend_name = trend_name.strip().lower()
    matching_projects = [p['name'] for p in PROJECTS if p["trend"].strip().lower() == normalized_trend_name]
    if matching_projects:
        print(f"Found {len(matching_projects)} projects for {trend_name}: {matching_projects}")
        return matching_projects
    return []

@tool
def create_bundle_for_project(project_name: str) -> dict:
    """
    Creates a product bundle for a given project, intelligently selecting products
    based on category, ensuring at least one low-velocity item is included,
    and prioritizing high/medium velocity for the remaining items.
    It also uses an LLM to refine the project steps and generate catchy descriptions for low-velocity items.
    This simulates the Assortment Optimizer Agent.
    """
    project = next((p for p in PROJECTS if p['name'] == project_name.strip()), None)
    if not project:
        return {"error": f"Project '{project_name}' not found."}

    bundle = []
    used_skus = set()

    # --- Bundle Creation Logic ---

    # Create a copy of ingredients to manipulate
    ingredients = list(project['ingredients'])
    random.shuffle(ingredients)

    # 1. Attempt to place one low-velocity item
    low_velocity_placed = False
    for i, ingredient in enumerate(ingredients):
        required_category = ingredient['category']
        low_velocity_options = [p for p in PRODUCTS if p.get('category') == required_category and p.get('velocity') == 'low']
        if low_velocity_options:
            chosen_item = random.choice(low_velocity_options)
            bundle.append(chosen_item)
            used_skus.add(chosen_item['sku'])
            ingredients.pop(i) # Remove ingredient from list
            low_velocity_placed = True
            break

    # 2. Fill the rest of the bundle
    for ingredient in ingredients:
        required_category = ingredient['category']
        
        selected_item = None
        # Prioritize High -> Medium -> Low, avoiding already used SKUs if possible
        for velocity_level in ['high', 'medium', 'low']:
            options = [p for p in PRODUCTS if p.get('category') == required_category and p.get('velocity') == velocity_level and p.get('sku') not in used_skus]
            if options:
                selected_item = random.choice(options)
                break
        
        # If no unused item was found, fall back to any item from that category
        if not selected_item:
            for velocity_level in ['high', 'medium', 'low']:
                options = [p for p in PRODUCTS if p.get('category') == required_category and p.get('velocity') == velocity_level]
                if options:
                    selected_item = random.choice(options)
                    break

        if selected_item:
            bundle.append(selected_item)
            used_skus.add(selected_item['sku'])
        else:
            return {"error": f"Could not find a suitable product for category '{required_category}'"}

    # --- New LLM-based refinement ---

    # 1. Generate catchy descriptions for low-velocity items
    for item in bundle:
        if item.get('velocity') == 'low':
            prompt = f"The project is '{project['name']}'. The product is '{item['name']}'. Write a short, catchy phrase (max 15 words) to highlight why this product is a great addition to the project, making it more appealing to a customer. For example, for a red ribbon, you could say 'adds a pop of vibrant color to your creation!'"
            response = llm.invoke(prompt)
            item['catchy_description'] = response.content.strip().replace('"', '')


    # 2. Refine project steps
    original_steps = project.get('steps', [])
    if original_steps:
        items_list = ", ".join([f"'{item['name']}'" for item in bundle])
        original_steps_str = "\n".join(original_steps)
        prompt = f"You are a helpful assistant for a craft store. Your task is to refine a generic list of project steps to make them more specific and engaging based on the actual products selected for the project bundle. Project: '{project['name']}'. Bundle Items: {items_list}.\n\nGiven these items, refine the following steps. Rewrite them to be more inspiring and mention the specific products where appropriate. Keep the same number of steps. Do not include any introductory text like 'Refined Steps:'. Just provide the numbered list of steps.\n\nOriginal Steps:\n{original_steps_str}\n\nRefined Steps:"
        response = llm.invoke(prompt)
        response_content = response.content.strip()
        # Split into lines and clean each line
        refined_steps = []
        for step in response_content.split('\n'):
            step = step.strip()
            if step:
                # Remove markdown bolding and leading numbers/dots
                step = step.replace('**', '')
                if '.' in step and step.split('.')[0].isdigit():
                    step = '.'.join(step.split('.')[1:]).strip()
                refined_steps.append(step)
        project['steps'] = refined_steps


    print(f"Created bundle for {project_name}: {bundle}")
    project_with_bundle = project.copy()
    project_with_bundle['bundle'] = bundle
    project_with_bundle['project_name'] = project['name']
    return project_with_bundle



# --- LangChain Orchestration ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

tools = [get_trend, get_projects_for_trend, create_bundle_for_project]

# 1. Set up memory
# Note: This is a simple global memory for demonstration. In a real multi-user app,
# you would manage separate memory instances for each user session.
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# 2. Update the prompt to include chat history
template = """You are a friendly and helpful creative shopping assistant for a craft store. Your goal is to help users find and create DIY projects.

You have access to the following tools:
{tools}

**Conversation Flow:**

1.  When the user starts a new conversation (e.g., "winter projects"), your primary goal is to identify a trend. Use the `get_trend` tool.
2.  Once a trend is identified, use the `get_projects_for_trend` tool to get a list of project names.
3.  After you get the list of projects, your next response to the user MUST be to present these choices. Use the `Final Answer` format with the `choices` key.
4.  The user will then respond with one of the choices. Your job is to look at the user's input and the previous conversation history (`chat_history`). If the user's input exactly matches one of the project names you just offered, you MUST NOT use `get_trend` or `get_projects_for_trend` again. Instead, you MUST immediately use the `create_bundle_for_project` tool with the project name the user selected.
5.  After calling `create_bundle_for_project`, provide the final answer with the project details.

Here is the conversation history:
{chat_history}

Use the following format for your thoughts and actions:

Thought: Do I need to use a tool? Yes
Action: The action to take, should be one of [{tool_names}]
Action Input: The input to the action
Observation: The result of the action

When you have a response to say to the Human, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: A JSON object with a "conversation" key. If you have a list of projects to show, add a "choices" key containing the list of project names. If you have a final project bundle, add a "project" key containing the output from the `create_bundle_for_project` tool.

Input: {input}
{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(template)

# 3. Create the agent and agent executor with memory
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, memory=memory, handle_parsing_errors=True)


# --- Flask App ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/chat_stream", methods=["GET"])
def chat_stream():
    user_input = request.args.get("message")

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    def generate_events():
        q = Queue()
        callback_handler = AgentStepCallbackHandler(q)

        def run_agent():
            try:
                agent_executor.invoke(
                    {"input": user_input},
                    config={"callbacks": [callback_handler]}
                )
            except Exception as e:
                print(f"Agent execution error during streaming: {e}")
                q.put({"type": "error", "content": f"An error occurred: {str(e)}"})
            finally:
                q.put({"type": "stream_end"}) # Signal the end of the stream

        thread = threading.Thread(target=run_agent)
        thread.start()

        while True:
            try:
                event = q.get(timeout=1) # Wait for an event with a timeout
                if event.get("type") == "stream_end":
                    break # Exit loop when stream ends
                yield f"data: {json.dumps(event)}\n\n"
            except Empty:
                # Send a heartbeat or just continue if no event for 1 second
                # This keeps the connection alive and allows the client to detect disconnections
                yield "data: {}\n\n" # Heartbeat
            except Exception as e:
                print(f"Error in event generation: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': f'Error generating events: {str(e)}'})}\n\n"
                break

    return Response(generate_events(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True, port=5000)