import os
import bs4
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.tools.retriever import create_retriever_tool
from langgraph.prebuilt import chat_agent_executor
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the model
model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Set environment variables
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize components
memory = SqliteSaver.from_conn_string(":memory:")
search = TavilySearchResults(max_results=2)

# Load and process documents
bs4_strainer = bs4.SoupStrainer(class_=("post-title", "post-header", "post-content"))
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs={"parse_only": bs4_strainer},
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)

vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

retriever_tool = create_retriever_tool(
    retriever,
    "langsmith_search",
    "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!",
)

tools = [search, retriever_tool]

# Create agent executor
agent_executor = chat_agent_executor.create_tool_calling_executor(model, tools, checkpointer=memory)

# Config with required thread_id
config = {"configurable": {"thread_id": "abc123"}}

# Chat history file
chat_history_file = "chat_history.txt"

# Function to load chat history from file
def load_chat_history(file_path):
    messages = []
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("User: "):
                    content = line[len("User: "):].strip()
                    messages.append(HumanMessage(content=content))
                elif line.startswith("AI: "):
                    content = line[len("AI: "):].strip()
                    messages.append(AIMessage(content=content))
    return messages

# Function to save a message to file
def save_message_to_file(file_path, role, content):
    with open(file_path, "a") as file:
        file.write(f"{role}: {content}\n") # Can only write in English for now

# Load previous chat history
messages = load_chat_history(chat_history_file)

# Main interaction loop
while True:
    user_input = input("> ")
    if user_input.lower() in ["exit", "quit"]:
        break
    
    usr_msg = HumanMessage(content=user_input)
    messages.append(usr_msg)
    save_message_to_file(chat_history_file, "User", user_input)
    
    response = agent_executor.invoke({"messages": messages}, config=config)
    ai_msg = AIMessage(content=response["messages"][-1].content)
    
    print(ai_msg.content)
    messages.append(ai_msg)
    save_message_to_file(chat_history_file, "AI", ai_msg.content)
