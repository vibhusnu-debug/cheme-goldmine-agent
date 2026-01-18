# agent_logic.py

# --- IMPORTS ---
import os
from dotenv import load_dotenv
from typing import TypedDict, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from tavily import TavilyClient
from config import TRUSTED_DOMAINS

# Load our secrets from the .env file
load_dotenv()

# --- 1. DEFINE THE BRAIN & TOOLS ---
# We use GPT-4o because it is best at complex reasoning
llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # <--- NEWEST STABLE VERSION (Llama 3.3)
    temperature=0,
    api_key=os.environ["GROQ_API_KEY"]
)
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# --- 2. DEFINE THE MEMORY (STATE) ---
# This is the "Shared Notebook" passed between the AI stations
class AgentState(TypedDict):
    topic: str              # The user input (e.g., "Heat Exchangers")
    plan: List[str]         # The list of sub-topics to research
    research_data: str      # The raw text found on the internet
    final_content: str      # The polished final chapter

# --- 3. STATION 1: THE PLANNER ---
def planner_node(state: AgentState):
    print(f"--- 1. Planning Chapter for: {state['topic']} ---")
    
    prompt = f"""
    You are a Chemical Engineering Professor.
    Create a detailed 4-point chapter outline for the topic: {state['topic']}.
    The outline MUST include:
    1. Theoretical Principles & Assumptions
    2. Key Mathematical Formulas (Derivations)
    3. Industrial Equipment & Applications
    4. A Complex Solved Example Problem
    
    Return ONLY the 4 lines of text.
    """
    
    # Ask the LLM
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Clean the response into a list
    plan = response.content.split('\n')
    return {"plan": plan}

# --- 4. STATION 2: THE RESEARCHER ---
def research_node(state: AgentState):
    print("--- 2. Researching Trusted Sources ---")
    aggregated_text = ""
    
    # Loop through each item in the plan
    for sub_topic in state['plan']:
        if len(sub_topic) < 3: continue # Skip empty lines
        
        query = f"chemical engineering {state['topic']} {sub_topic}"
        print(f"   -> Searching: {query}")
        
        # SEARCH THE WEB (Restricted to our Whitelist)
        results = tavily.search(
            query=query,
            include_domains=TRUSTED_DOMAINS,
            max_results=2, # Get top 2 results per sub-topic
            search_depth="advanced"
        )
        
        # Add findings to our "Notebook"
        for res in results['results']:
            aggregated_text += f"\nSOURCE: {res['url']}\nCONTENT: {res['content']}\n"
            
    return {"research_data": aggregated_text}

# --- 5. STATION 3: THE WRITER ---
def writer_node(state: AgentState):
    print("--- 3. Writing Final Chapter ---")
    
    prompt = f"""
    You are the "Ultimate Chemical Engineering Resource" generator.
    Your goal is to write a high-quality university textbook chapter on: {state['topic']}.
    
    Use the following research data:
    {state['research_data']}
    
    STRICT FORMATTING RULES:
    1. Use clearly defined Headers (##).
    2. ALL Math/Formulas must be in LaTeX format (enclose in $$).
    3. Include a "Key Constants" table if data is available.
    4. The "Solved Example" must show step-by-step substitution of values.
    5. Tone: Academic, rigorous, precise.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_content": response.content}

# --- 6. CONNECTING THE FACTORY ---
workflow = StateGraph(AgentState)

# Add the stations (Nodes)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", research_node)
workflow.add_node("writer", writer_node)

# Connect the stations (Edges)
workflow.set_entry_point("planner")      # Start at Planner
workflow.add_edge("planner", "researcher") # Go to Researcher
workflow.add_edge("researcher", "writer")  # Go to Writer
workflow.add_edge("writer", END)           # Finish

# Compile the machine
app_engine = workflow.compile()