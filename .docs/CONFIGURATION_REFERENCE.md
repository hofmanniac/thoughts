# Thoughts Framework - Configuration Reference

## Configuration Hierarchy

The Thoughts framework uses a hierarchical configuration system that allows for flexible and maintainable setups:

1. **Framework Defaults** - Base settings built into the framework
2. **Cortex Configuration** - Application-level blueprint
3. **Workspace Configuration** - Instance-specific overrides
4. **Agent Configuration** - Agent-specific behaviors  
5. **Session Configuration** - Session-specific parameters
6. **Runtime Configuration** - Dynamic updates during execution

## Thoughts Configuration Format

The Thoughts framework uses a unique configuration schema built around behaviors and conversational patterns:

### Core Structure
```json
{
  "name": "AgentName",
  "Behaviors": [/* Array of behavior definitions */],
  "Channels": {/* Output channel configurations */}
}
```

### Behavior Definition
```json
{
  "Task": "TaskName",
  "repeat": true,  // Optional: allows task repetition
  "steps": [/* Array of steps to execute */]
}
```

### Step Types

#### Express Step
Defines an agent persona with training instructions:
```json
{
  "Express": "PersonaName",
  "train": [
    {"Role": "Primary role definition"},
    {"Continue": "Additional instruction"},
    {"History": 5},  // Number of previous interactions to remember
    {"StartInstruction": "Initial greeting or instruction"}
  ]
}
```

#### Ask Step
Prompts for user input:
```json
{"Ask": "PROMPT_TEXT:"}
```

### Channel Configuration
Defines how the agent outputs responses:
```json
{
  "Channels": {
    "Default": [
      {
        "Write": "#",           // Output destination
        "prompt": "BOT:",       // Display prompt
        "speed": 0.01          // Typing speed simulation
      }
    ]
  }
}
```

## Cortex Configuration

### Basic Structure
```json
{
  "name": "MyApplication",
  "version": "1.0.0",
  "description": "Description of the AI application",
  "agents": { /* Agent definitions */ },
  "memory": { /* Memory system configuration */ },
  "operations": { /* Available operations */ },
  "tools": { /* Tool registry */ },
  "orchestration": { /* Agent coordination patterns */ },
  "workspace_template": { /* Default workspace settings */ }
}
```

### Agent Definitions
```json
{
  "agents": {
    "assistant": {
      "type": "conversational",
      "config": "./agents/assistant.json",
      "capabilities": ["chat", "search", "analysis"],
      "memory_access": ["conversation", "facts"],
      "tools": ["web_search", "calculator"]
    },
    "researcher": {
      "type": "research",
      "operations": [
        {
          "type": "prompt",
          "template": "Research the topic: {query}",
          "model": "gpt-4"
        },
        {
          "type": "web_search",
          "max_results": 10
        }
      ]
    }
  }
}
```

### Memory System Configuration
```json
{
  "memory": {
    "conversation": {
      "type": "temporal",
      "backend": "file",
      "path": "./memory/conversations",
      "max_tokens": 8000,
      "cleanup_policy": "rolling"
    },
    "facts": {
      "type": "graph",
      "backend": "networkx", 
      "persistent": true,
      "path": "./memory/facts.json"
    },
    "vectors": {
      "type": "vector",
      "backend": "chroma",
      "path": "./memory/vectors",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "similarity_threshold": 0.7
    }
  }
}
```

### Operation Definitions
```json
{
  "operations": {
    "smart_prompt": {
      "type": "prompt",
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 1000,
      "fallback": {
        "model": "gpt-3.5-turbo",
        "max_retries": 3
      }
    },
    "web_research": {
      "type": "composite",
      "steps": [
        {"operation": "web_search", "max_results": 5},
        {"operation": "extract_content"},
        {"operation": "summarize"}
      ]
    }
  }
}
```

## Agent Configuration

### Conversational Agent
```json
{
  "name": "Assistant",
  "Behaviors": [
    {
      "Task": "Chat",
      "repeat": true,
      "steps": [
        {
          "Express": "Assistant",
          "train": [
            {"Role": "You are a helpful AI assistant."},
            {"Continue": "1. Answer questions helpfully and accurately."},
            {"Continue": "2. If you don't know something, say so clearly."},
            {"Continue": "3. Ask follow-up questions to better help the user."},
            {"History": 10},
            {"StartInstruction": "Greet the user and ask how you can help them today."}
          ]
        },
        {"Ask": "USER:"}
      ]
    }
  ],
  "Channels": {
    "Default": [{"Write": "#", "prompt": "ASSISTANT:", "speed": 0.01}]
  }
}
```

### Research Agent
```json
{
  "name": "Researcher",
  "Behaviors": [
    {
      "Task": "Research",
      "steps": [
        {
          "Express": "Researcher",
          "train": [
            {"Role": "You are a thorough research specialist."},
            {"Continue": "Research topics comprehensively using available sources."},
            {"Continue": "Provide citations and verify information accuracy."},
            {"Continue": "Structure findings in a clear, organized manner."},
            {"History": 8}
          ]
        },
        {
          "Express": "Analyst", 
          "train": [
            {"Role": "You are a critical analyst."},
            {"Continue": "Analyze the research findings for patterns and insights."},
            {"Continue": "Identify gaps, contradictions, or areas needing more research."},
            {"History": 5}
          ]
        },
        {"Ask": "RESEARCH TOPIC:"}
      ]
    }
  ],
  "Channels": {
    "Default": [{"Write": "#", "prompt": "RESEARCH:", "speed": 0.02}]
  }
}
```

### Multi-Behavior Agent
```json
{
  "name": "TaskExecutor",
  "Behaviors": [
    {
      "Task": "Planning",
      "steps": [
        {
          "Express": "Planner",
          "train": [
            {"Role": "You are a task planning specialist."},
            {"Continue": "Break down complex tasks into manageable steps."},
            {"Continue": "Consider dependencies and optimal sequencing."},
            {"History": 3}
          ]
        }
      ]
    },
    {
      "Task": "Execution", 
      "repeat": true,
      "steps": [
        {
          "Express": "Executor",
          "train": [
            {"Role": "You are a task executor."},
            {"Continue": "Execute tasks efficiently and report results."},
            {"Continue": "Handle errors gracefully and suggest alternatives."},
            {"History": 5}
          ]
        },
        {"Ask": "TASK:"}
      ]
    }
  ],
  "Channels": {
    "Default": [{"Write": "#", "prompt": "EXECUTOR:", "speed": 0.015}]
  }
}
```

## Memory Configuration

### Vector Memory (Chroma)
```json
{
  "type": "vector",
  "backend": "chroma",
  "config": {
    "path": "./memory/chroma_db",
    "collection_name": "thoughts_memory",
    "embedding_function": {
      "type": "sentence_transformers",
      "model": "all-MiniLM-L6-v2"
    },
    "distance_metric": "cosine",
    "index_params": {
      "ef_construction": 200,
      "M": 16
    }
  }
}
```

### Graph Memory (NetworkX)
```json
{
  "type": "graph",
  "backend": "networkx",
  "config": {
    "graph_type": "DiGraph",
    "persistent": true,
    "storage": {
      "format": "json",
      "path": "./memory/graph.json",
      "auto_save": true,
      "save_interval": 300
    },
    "node_attributes": ["type", "created_at", "importance"],
    "edge_attributes": ["relationship", "confidence", "timestamp"]
  }
}
```

### File-based Memory
```json
{
  "type": "file",
  "backend": "json",
  "config": {
    "base_path": "./memory/files",
    "structure": "hierarchical",
    "compression": true,
    "encryption": {
      "enabled": false,
      "key_source": "environment"
    },
    "backup": {
      "enabled": true,
      "interval": "daily",
      "retention": "30d"
    }
  }
}
```

## Tool Configuration

### Web Search Tool
```json
{
  "name": "web_search",
  "type": "web_api",
  "config": {
    "provider": "duckduckgo",
    "api_key": "${DUCKDUCKGO_API_KEY}",
    "max_results": 10,
    "safe_search": true,
    "timeout": 30,
    "rate_limit": {
      "requests_per_minute": 60,
      "backoff_strategy": "exponential"
    }
  },
  "schema": {
    "name": "search_web",
    "description": "Search the web for information",
    "parameters": {
      "query": {"type": "string", "required": true},
      "max_results": {"type": "integer", "default": 5, "max": 20}
    }
  }
}
```

### Database Tool  
```json
{
  "name": "database_query",
  "type": "database",
  "config": {
    "connection_string": "${DATABASE_URL}",
    "driver": "postgresql",
    "pool_size": 5,
    "timeout": 30,
    "allowed_operations": ["SELECT", "INSERT", "UPDATE"],
    "security": {
      "sql_injection_protection": true,
      "query_validation": true,
      "result_limit": 1000
    }
  }
}
```

### File System Tool
```json
{
  "name": "file_operations",
  "type": "filesystem",
  "config": {
    "base_path": "./workspace_files",
    "allowed_extensions": [".txt", ".json", ".md", ".csv"],
    "max_file_size": "10MB",
    "permissions": {
      "read": true,
      "write": true,
      "delete": false,
      "execute": false
    },
    "sandbox": {
      "enabled": true,
      "chroot": true
    }
  }
}
```

## Orchestration Configuration

### Pipeline Orchestration
```json
{
  "orchestration": {
    "type": "pipeline",
    "config": {
      "stages": [
        {
          "name": "input_processing",
          "agent": "input_processor",
          "timeout": 30,
          "retry_policy": "exponential_backoff"
        },
        {
          "name": "analysis", 
          "agent": "analyzer",
          "parallel": true,
          "max_concurrent": 3,
          "condition": {
            "type": "previous_success",
            "stage": "input_processing"
          }
        },
        {
          "name": "synthesis",
          "agent": "synthesizer", 
          "depends_on": ["analysis"],
          "final_stage": true
        }
      ],
      "error_handling": {
        "strategy": "fail_fast",
        "cleanup_on_failure": true
      }
    }
  }
}
```

### Collaborative Orchestration
```json
{
  "orchestration": {
    "type": "collaborative",
    "config": {
      "agents": ["researcher", "analyst", "reviewer"],
      "coordination": {
        "communication_pattern": "mesh",
        "shared_memory": true,
        "consensus_mechanism": "weighted_voting",
        "decision_threshold": 0.7
      },
      "workflow": {
        "max_iterations": 5,
        "convergence_criteria": "agreement_threshold",
        "timeout": 300
      }
    }
  }
}
```

## Workspace Configuration

### Development Workspace
```json
{
  "workspace": {
    "environment": "development",
    "debug": true,
    "logging": {
      "level": "DEBUG",
      "format": "detailed",
      "output": ["console", "file"]
    },
    "resources": {
      "memory_limit": "1GB",
      "execution_timeout": 300,
      "concurrent_sessions": 5
    },
    "persistence": {
      "sessions": true,
      "memory": true,
      "logs": true,
      "cleanup_interval": "1h"
    }
  }
}
```

### Production Workspace
```json
{
  "workspace": {
    "environment": "production",
    "debug": false,
    "logging": {
      "level": "INFO",
      "format": "json",
      "output": ["file", "elasticsearch"]
    },
    "resources": {
      "memory_limit": "4GB", 
      "execution_timeout": 120,
      "concurrent_sessions": 100
    },
    "monitoring": {
      "metrics": true,
      "tracing": true,
      "health_checks": true
    },
    "security": {
      "isolation": "strict",
      "audit_logging": true,
      "rate_limiting": true
    }
  }
}
```

## Environment Variables

### Required Variables
```bash
# LLM Provider Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...

# Memory System Configuration  
CHROMA_DB_PATH=./memory/chroma
REDIS_URL=redis://localhost:6379

# External Services
SEARCH_API_KEY=...
DATABASE_URL=postgresql://user:pass@host:5432/db

# Framework Configuration
THOUGHTS_LOG_LEVEL=INFO
THOUGHTS_MAX_MEMORY=4GB
THOUGHTS_SESSION_TTL=24h
```

### Optional Variables
```bash
# Performance Tuning
THOUGHTS_CACHE_SIZE=1000
THOUGHTS_WORKER_THREADS=4
THOUGHTS_BATCH_SIZE=10

# Security
THOUGHTS_ENCRYPTION_KEY=...
THOUGHTS_RATE_LIMIT=100

# Development
THOUGHTS_DEBUG=true
THOUGHTS_PROFILE=true
```

## Configuration Validation

### JSON Schema Example
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {"type": "string", "minLength": 1},
    "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
    "agents": {
      "type": "object",
      "patternProperties": {
        "^[a-zA-Z][a-zA-Z0-9_]*$": {
          "type": "object",
          "properties": {
            "type": {"enum": ["conversational", "research", "tool"]},
            "operations": {"type": "array", "minItems": 1}
          },
          "required": ["type", "operations"]
        }
      }
    }
  },
  "required": ["name", "version", "agents"]
}
```

### Validation Command
```python
from thoughts.config import ConfigValidator

validator = ConfigValidator()
result = validator.validate_file("./config.json")

if not result.is_valid:
    for error in result.errors:
        print(f"Error at {error.path}: {error.message}")
```

## Configuration Templates

### Minimal Configuration
```json
{
  "name": "SimpleAgent",
  "Behaviors": [
    {
      "Task": "Chat",
      "steps": [
        {
          "Express": "Assistant",
          "train": [
            {"Role": "You are a helpful assistant."}
          ]
        },
        {"Ask": "YOU:"}
      ]
    }
  ],
  "Channels": {
    "Default": [{"Write": "#"}]
  }
}
```

### Full-Featured Configuration
```json
{
  "name": "EnterpriseAssistant",
  "Behaviors": [
    {
      "Task": "GeneralAssistance",
      "repeat": true,
      "steps": [
        {
          "Express": "Assistant",
          "train": [
            {"Role": "You are an enterprise AI assistant."},
            {"Continue": "1. Provide professional, accurate assistance."},
            {"Continue": "2. Maintain confidentiality and security."},
            {"Continue": "3. Ask clarifying questions when needed."},
            {"History": 15},
            {"StartInstruction": "Hello! I'm your enterprise assistant. How can I help you today?"}
          ]
        },
        {"Ask": "USER:"}
      ]
    },
    {
      "Task": "Research",
      "steps": [
        {
          "Express": "Researcher",
          "train": [
            {"Role": "You are a professional researcher."},
            {"Continue": "Research topics thoroughly using available resources."},
            {"Continue": "Provide source citations and verify information."},
            {"History": 8}
          ]
        },
        {
          "Express": "Analyst",
          "train": [
            {"Role": "You are a data analyst."},
            {"Continue": "Analyze findings and identify key insights."},
            {"Continue": "Present analysis in structured format."},
            {"History": 6}
          ]
        }
      ]
    },
    {
      "Task": "Planning",
      "steps": [
        {
          "Express": "Planner",
          "train": [
            {"Role": "You are a strategic planner."},
            {"Continue": "Break down complex projects into actionable steps."},
            {"Continue": "Consider resources, timelines, and dependencies."},
            {"History": 5}
          ]
        }
      ]
    }
  ],
  "Channels": {
    "Default": [{"Write": "#", "prompt": "ASSISTANT:", "speed": 0.008}],
    "Research": [{"Write": "#", "prompt": "RESEARCH:", "speed": 0.015}],
    "Analysis": [{"Write": "#", "prompt": "ANALYSIS:", "speed": 0.012}]
  }
}
```

This configuration reference provides comprehensive documentation for all configuration options available in the Thoughts framework, with practical examples for different use cases and deployment scenarios.