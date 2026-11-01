# Thoughts Framework - Developer Guide

## Getting Started

### Installation & Setup
```bash
pip install thoughts-framework
# or for development
git clone https://github.com/hofmanniac/thoughts
cd thoughts
pip install -e .
```

### Quick Start
```python
from thoughts.agent import Agent
from thoughts.context import Context

# Create a workspace context
context = Context(persist_session=True)

# Initialize an agent
agent = Agent()

# Load configuration from JSON
agent.load_from_config(context, "examples/example.json")

# Execute the agent
result = agent.execute(context)
```

## Core Patterns

### Understanding Thoughts Configuration Format

The Thoughts framework uses a unique configuration format built around **Behaviors**, **Tasks**, and **Steps**:

#### Core Configuration Elements

**Behaviors**: Top-level behavior definitions that define what the agent can do
- `Task`: Named task within the behavior  
- `repeat`: Whether the task can be repeated
- `steps`: Array of steps to execute in sequence

**Steps**: Individual actions the agent takes
- `Express`: Define an agent persona with training
- `Ask`: Prompt for user input
- Custom operations and rules

**Express Training**: Instructions for agent personas
- `Role`: Primary role definition
- `Continue`: Additional instructions 
- `History`: Number of previous interactions to remember
- `StartInstruction`: Initial greeting or instruction

**Channels**: Output formatting and display options
- `Write`: Output destination 
- `prompt`: Display prompt text
- `speed`: Typing speed simulation

### Configuration-Driven Development

#### Basic Agent Configuration
```json
{
  "name": "SimpleAssistant",
  "Behaviors": [
    {
      "Task": "Chat",
      "repeat": true,
      "steps": [
        {
          "Express": "Assistant",
          "train": [
            {"Role": "You are a helpful assistant."},
            {"Continue": "Answer questions helpfully and ask follow-up questions."},
            {"History": 4}
          ]
        },
        {"Ask": "YOU:"}
      ]
    }
  ],
  "Channels": {
    "Default": [{"Write": "#", "prompt": "BOT:", "speed": 0.01}]
  }
}
```

#### Multi-Step Agent Configuration
```json
{
  "name": "ResearchAssistant",
  "Behaviors": [
    {
      "Task": "Research",
      "steps": [
        {
          "Express": "Researcher",
          "train": [
            {"Role": "You are a research assistant."},
            {"Continue": "Research the given topic thoroughly."},
            {"History": 6}
          ]
        },
        {
          "Express": "Reviewer", 
          "train": [
            {"Role": "You are a critical reviewer."},
            {"Continue": "Review and validate the research findings."},
            {"History": 3}
          ]
        },
        {"Ask": "TOPIC:"}
      ]
    }
  ],
  "Channels": {
    "Default": [{"Write": "#", "prompt": "RESEARCH:", "speed": 0.02}]
  }
}
```

### Programmatic Development

#### Custom Agent Implementation
```python
from thoughts.agent import BaseAgent
from thoughts.operations import Operation

class CustomAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.custom_state = {}
    
    def execute(self, context):
        # Custom execution logic
        result = self.process_input(context.current_input)
        context.add_response(result)
        return result
    
    def process_input(self, input_text):
        # Domain-specific processing
        return f"Processed: {input_text}"
```

#### Custom Operation Implementation
```python
from thoughts.operations import BaseOperation

class DatabaseLookup(BaseOperation):
    def __init__(self, config):
        self.connection_string = config.get("connection_string")
        self.query_template = config.get("query_template")
    
    def execute(self, context, **kwargs):
        query = self.query_template.format(**kwargs)
        # Execute database query
        results = self.execute_query(query)
        return {"results": results, "count": len(results)}
```

### Memory System Integration

#### Vector Memory Example
```python
from thoughts.memory import VectorMemory

# Configure vector memory
memory_config = {
    "type": "chroma",
    "path": "./memory/vectors",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}

memory = VectorMemory(memory_config)
context = Context(memory_system=memory)

# Store and retrieve information
memory.store("user_preferences", {"theme": "dark", "language": "en"})
preferences = memory.retrieve("user settings")
```

#### Graph Memory Example  
```python
from thoughts.memory import GraphMemory

# Configure graph memory
memory_config = {
    "type": "networkx",
    "persistent": True,
    "path": "./memory/graph.json"
}

memory = GraphMemory(memory_config)

# Add relationships
memory.add_node("user1", type="user", name="John")
memory.add_node("project1", type="project", name="AI Assistant")
memory.add_edge("user1", "project1", relationship="owns")
```

## Common Patterns

### Error Handling Patterns

#### Graceful Degradation
```json
{
  "operations": [
    {
      "type": "prompt",
      "model": "gpt-4",
      "fallback": {
        "model": "gpt-3.5-turbo",
        "on_error": "continue"
      }
    }
  ]
}
```

#### Retry Strategies
```python
from thoughts.operations import PromptOperation

class RobustPrompt(PromptOperation):
    def execute(self, context, **kwargs):
        max_retries = self.config.get("max_retries", 3)
        
        for attempt in range(max_retries):
            try:
                return super().execute(context, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
```

### Session Management Patterns

#### Long-Running Conversations
```python
# Create persistent session
context = Context(
    session_id="user_123_daily",
    persist_session=True,
    max_session_length=100
)

agent = Agent()
agent.load_from_config(context, "configs/conversational.json")

# Multiple interactions maintain context
agent.execute(context)  # First interaction
# ... time passes ...
agent.execute(context)  # Continues previous conversation
```

#### Workspace Templates
```python
# Define reusable workspace configuration
workspace_template = {
    "memory": {
        "conversation": {"max_tokens": 8000},
        "facts": {"type": "graph", "persistent": True}
    },
    "agents": {
        "default": "configs/assistant.json"
    },
    "tools": ["web_search", "calculator", "file_access"]
}

# Create workspace instances
user_workspace = Context.from_template(
    template=workspace_template,
    instance_id="user_123"
)
```

## Advanced Techniques

### Multi-Agent Orchestration

#### Collaborative Pattern
```json
{
  "orchestration": {
    "type": "collaborative",
    "agents": ["analyst", "researcher", "writer"],
    "coordination": {
      "shared_memory": true,
      "communication": "broadcast",
      "consensus": "majority"
    }
  }
}
```

#### Pipeline Pattern  
```json
{
  "orchestration": {
    "type": "pipeline",
    "stages": [
      {"agent": "input_processor", "timeout": 30},
      {"agent": "analyzer", "parallel": true},
      {"agent": "summarizer", "condition": "analysis_complete"}
    ]
  }
}
```

### Custom Memory Backends

#### Redis Memory Backend
```python
from thoughts.memory import BaseMemory
import redis

class RedisMemory(BaseMemory):
    def __init__(self, config):
        self.client = redis.Redis(
            host=config.get("host", "localhost"),
            port=config.get("port", 6379)
        )
    
    def store(self, key, value, namespace="default"):
        full_key = f"{namespace}:{key}"
        self.client.set(full_key, json.dumps(value))
    
    def retrieve(self, query, namespace="default"):
        # Implement search logic
        keys = self.client.keys(f"{namespace}:*{query}*")
        return [json.loads(self.client.get(key)) for key in keys]
```

### Tool Development

#### Web API Tool
```python
from thoughts.tools import BaseTool
import requests

class WeatherTool(BaseTool):
    def __init__(self, config):
        self.api_key = config.get("api_key")
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def execute(self, location, units="metric"):
        url = f"{self.base_url}/weather"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": units
        }
        
        response = requests.get(url, params=params)
        return response.json()
    
    @property
    def schema(self):
        return {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "location": {"type": "string", "required": True},
                "units": {"type": "string", "default": "metric"}
            }
        }
```

## Best Practices

### Configuration Management
- **Use environment-specific configs**: `config.dev.json`, `config.prod.json`
- **Keep secrets out of configs**: Use environment variables for API keys
- **Validate configurations**: Use JSON schemas for configuration validation
- **Version your configs**: Track configuration changes alongside code

### Performance Optimization
- **Lazy load components**: Initialize agents and tools only when needed
- **Cache expensive operations**: Store computation results in memory systems
- **Batch operations**: Group similar operations for efficiency
- **Monitor resource usage**: Track memory and compute usage patterns

### Error Handling
- **Fail fast**: Validate configurations and dependencies at startup
- **Provide fallbacks**: Always have backup strategies for critical operations
- **Log comprehensively**: Include context and configuration in error logs
- **Handle partial failures**: Design for graceful degradation in multi-agent scenarios

### Security Considerations
- **Isolate workspaces**: Ensure proper isolation between different users/tenants
- **Validate inputs**: Sanitize all external inputs and tool outputs
- **Secure credentials**: Use secure credential storage and rotation
- **Audit operations**: Log all agent actions for compliance and debugging

## Anti-Patterns to Avoid

### Configuration Anti-Patterns
- ❌ **Hardcoding values**: Embedding API keys or URLs in configuration files
- ❌ **Monolithic configs**: Single massive configuration files that are hard to maintain
- ❌ **Circular dependencies**: Agents or operations that depend on each other cyclically
- ❌ **Environment mixing**: Using production credentials in development configurations

### Development Anti-Patterns
- ❌ **Blocking operations**: Long-running synchronous operations that block the framework
- ❌ **Shared mutable state**: Global variables or shared objects without proper synchronization
- ❌ **Resource leaks**: Not properly cleaning up connections, files, or memory
- ❌ **Silent failures**: Catching exceptions without proper logging or handling

### Deployment Anti-Patterns
- ❌ **Single point of failure**: Deploying without redundancy or failover mechanisms
- ❌ **Unbounded resources**: Not setting limits on memory, compute, or storage usage
- ❌ **Missing monitoring**: Deploying without proper observability and alerting
- ❌ **Inconsistent environments**: Different configurations between development and production

## Troubleshooting Guide

### Common Issues

#### Configuration Loading Errors
```python
# Check configuration validity
from thoughts.config import validate_config

try:
    validate_config("path/to/config.json")
except ConfigurationError as e:
    print(f"Configuration error: {e.message}")
    print(f"Location: {e.path}")
```

#### Memory System Issues
```python
# Debug memory operations
context = Context(debug=True)
memory = context.memory_system

# Check memory health
health = memory.health_check()
print(f"Memory system status: {health}")
```

#### Agent Execution Problems
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add execution tracing
context = Context(trace=True)
agent.execute(context)

# Review execution trace
for step in context.execution_trace:
    print(f"{step.timestamp}: {step.operation} - {step.result}")
```

This developer guide provides practical examples and patterns for building with the Thoughts framework, covering everything from basic usage to advanced customization and deployment considerations.