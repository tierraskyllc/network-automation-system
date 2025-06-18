"""
Network LangChain Processor

Main processor for handling natural language requests and converting them
to network automation tasks.
"""

import asyncio
import structlog
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.callbacks import AsyncCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import BaseTool

from ..core.config import get_settings
from .prompts import NetworkPromptTemplates
from .tools import NetworkLangChainTools
from .chains import NetworkChains

logger = structlog.get_logger(__name__)
settings = get_settings()


class NetworkCallbackHandler(AsyncCallbackHandler):
    """Custom callback handler for network automation tasks"""
    
    def __init__(self):
        self.logs = []
        self.start_time = None
        self.end_time = None
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Called when LLM starts running"""
        self.start_time = datetime.utcnow()
        logger.info("LLM processing started", prompts_count=len(prompts))
    
    async def on_llm_end(self, response, **kwargs):
        """Called when LLM ends running"""
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info("LLM processing completed", duration=duration)
    
    async def on_llm_error(self, error: Exception, **kwargs):
        """Called when LLM encounters an error"""
        logger.error("LLM processing error", error=str(error))
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Called when tool starts running"""
        tool_name = serialized.get("name", "unknown")
        logger.info("Tool execution started", tool=tool_name, input=input_str)
    
    async def on_tool_end(self, output: str, **kwargs):
        """Called when tool ends running"""
        logger.info("Tool execution completed", output_length=len(output))
    
    async def on_tool_error(self, error: Exception, **kwargs):
        """Called when tool encounters an error"""
        logger.error("Tool execution error", error=str(error))
    
    async def on_agent_action(self, action, **kwargs):
        """Called when agent takes an action"""
        logger.info("Agent action", tool=action.tool, tool_input=action.tool_input)
    
    async def on_agent_finish(self, finish, **kwargs):
        """Called when agent finishes"""
        logger.info("Agent finished", output=finish.return_values)


class NetworkLangChainProcessor:
    """Main processor for network automation using LangChain"""
    
    def __init__(self, db_session=None, user_context: Optional[Dict[str, Any]] = None):
        """
        Initialize the processor
        
        Args:
            db_session: Database session for accessing network data
            user_context: User context for permissions and preferences
        """
        self.db_session = db_session
        self.user_context = user_context or {}
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize components
        self.prompt_templates = NetworkPromptTemplates()
        self.tools = NetworkLangChainTools(db_session=db_session)
        self.chains = NetworkChains(llm=self.llm)
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize callback handler
        self.callback_handler = NetworkCallbackHandler()
        
        # Initialize agent
        self.agent_executor = None
        self._initialize_agent()
        
        self.logger = logger.bind(
            user_id=self.user_context.get("user_id"),
            username=self.user_context.get("username")
        )
    
    def _initialize_llm(self):
        """Initialize the language model"""
        if settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model_name=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                openai_api_key=settings.OPENAI_API_KEY,
                callbacks=[self.callback_handler]
            )
        else:
            # Fallback to Ollama or mock LLM
            logger.warning("OpenAI API key not configured, using mock LLM")
            return self._create_mock_llm()
    
    def _create_mock_llm(self):
        """Create a mock LLM for testing"""
        from langchain.llms.fake import FakeListLLM
        
        responses = [
            "I understand you want to check device status. Let me help you with that.",
            "I'll execute the show version command on the specified device.",
            "The command has been executed successfully. Here are the results.",
            "I've completed the network automation task as requested."
        ]
        
        return FakeListLLM(responses=responses)
    
    def _initialize_agent(self):
        """Initialize the LangChain agent"""
        try:
            # Get available tools
            tools = self.tools.get_all_tools()
            
            # Create system prompt
            system_prompt = self.prompt_templates.get_system_prompt()
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=tools,
                prompt=system_prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                memory=self.memory,
                verbose=True,
                max_iterations=10,
                max_execution_time=300,  # 5 minutes
                callbacks=[self.callback_handler]
            )
            
            self.logger.info("Agent initialized successfully", tools_count=len(tools))
            
        except Exception as e:
            self.logger.error("Failed to initialize agent", error=str(e))
            self.agent_executor = None
    
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language request
        
        Args:
            user_input: Natural language input from user
            context: Additional context for the request
            
        Returns:
            Dict[str, Any]: Processing result
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            if not user_input or not user_input.strip():
                return {
                    "success": False,
                    "error": "Empty input provided",
                    "timestamp": start_time.isoformat()
                }
            
            # Prepare context
            full_context = {
                **self.user_context,
                **(context or {}),
                "timestamp": start_time.isoformat()
            }
            
            # Log request
            self.logger.info(
                "Processing user request",
                input=user_input,
                context=full_context
            )
            
            # Process with agent
            if self.agent_executor:
                result = await self._process_with_agent(user_input, full_context)
            else:
                result = await self._process_with_chains(user_input, full_context)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Prepare response
            response = {
                "success": True,
                "result": result,
                "processing_time": processing_time,
                "timestamp": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
            
            self.logger.info(
                "Request processed successfully",
                processing_time=processing_time,
                result_type=type(result).__name__
            )
            
            return response
            
        except Exception as e:
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            self.logger.error(
                "Request processing failed",
                error=str(e),
                processing_time=processing_time
            )
            
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "timestamp": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
    
    async def _process_with_agent(self, user_input: str, context: Dict[str, Any]) -> Any:
        """Process request using LangChain agent"""
        try:
            # Prepare input with context
            agent_input = {
                "input": user_input,
                "context": context
            }
            
            # Run agent
            result = await self.agent_executor.ainvoke(agent_input)
            
            return result.get("output", result)
            
        except Exception as e:
            self.logger.error("Agent processing failed", error=str(e))
            raise
    
    async def _process_with_chains(self, user_input: str, context: Dict[str, Any]) -> Any:
        """Process request using LangChain chains (fallback)"""
        try:
            # Classify the request
            classification = await self.chains.classify_request(user_input)
            
            # Route to appropriate chain based on classification
            if classification.get("type") == "device_command":
                return await self.chains.execute_device_command(user_input, context)
            elif classification.get("type") == "device_info":
                return await self.chains.get_device_info(user_input, context)
            elif classification.get("type") == "topology_query":
                return await self.chains.query_topology(user_input, context)
            elif classification.get("type") == "workflow_execution":
                return await self.chains.execute_workflow(user_input, context)
            else:
                return await self.chains.general_response(user_input, context)
                
        except Exception as e:
            self.logger.error("Chain processing failed", error=str(e))
            raise
    
    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Returns:
            List[Dict[str, Any]]: Conversation messages
        """
        try:
            messages = self.memory.chat_memory.messages
            
            history = []
            for message in messages:
                if isinstance(message, HumanMessage):
                    history.append({
                        "type": "human",
                        "content": message.content,
                        "timestamp": getattr(message, "timestamp", None)
                    })
                elif isinstance(message, AIMessage):
                    history.append({
                        "type": "ai",
                        "content": message.content,
                        "timestamp": getattr(message, "timestamp", None)
                    })
                elif isinstance(message, SystemMessage):
                    history.append({
                        "type": "system",
                        "content": message.content,
                        "timestamp": getattr(message, "timestamp", None)
                    })
            
            return history
            
        except Exception as e:
            self.logger.error("Failed to get conversation history", error=str(e))
            return []
    
    async def clear_conversation_history(self):
        """Clear conversation history"""
        try:
            self.memory.clear()
            self.logger.info("Conversation history cleared")
        except Exception as e:
            self.logger.error("Failed to clear conversation history", error=str(e))
    
    async def add_context(self, context: Dict[str, Any]):
        """
        Add context to the processor
        
        Args:
            context: Additional context to add
        """
        self.user_context.update(context)
        self.logger.info("Context updated", new_context=context)
    
    def get_available_capabilities(self) -> Dict[str, Any]:
        """
        Get available capabilities and tools
        
        Returns:
            Dict[str, Any]: Available capabilities
        """
        return {
            "tools": [tool.name for tool in self.tools.get_all_tools()],
            "chains": self.chains.get_available_chains(),
            "memory_enabled": self.memory is not None,
            "agent_enabled": self.agent_executor is not None,
            "llm_model": getattr(self.llm, "model_name", "unknown")
        }
