# Thoughts Framework - Architecture

## Core Architecture Overview

The Thoughts framework is built around a central component called the **Cortex**, which serves as the primary coordination layer for all workspace management, agent lifecycle, and session orchestration. The Cortex operates at a higher abstraction level than individual components like orchestrators, agents, or memory systems.

## The Cortex

### Definition
The Cortex represents the application blueprint - a configuration that defines the structure, capabilities, and coordination logic for AI applications. A Cortex configuration specifies what agents are available, how they interact, what memory systems to use, and how sessions should be managed. 

### Cortex vs Workspace Separation
- **Cortex Configuration**: The application definition and coordination logic (the "app")
- **Workspace**: A running instance of a Cortex configuration for a specific user/purpose (the "instance")

A single Cortex configuration can spawn multiple independent Workspaces, each with their own state, sessions, and data isolation.

### Cortex Configuration Responsibilities

#### Application Definition
- **Agent Specifications**: Define available agent types, their capabilities, and interaction patterns
- **Memory Architecture**: Specify memory system types, backends, and consistency requirements
- **Communication Patterns**: Define how agents communicate and coordinate within the application
- **Tool Registry**: Catalog of available tools and their access patterns
- **Orchestration Logic**: Rules and patterns for agent coordination and task routing

#### Workspace Template
- **Resource Templates**: Define resource allocation patterns for workspace instances
- **Configuration Inheritance**: Establish configuration hierarchy and override patterns
- **Isolation Boundaries**: Define what gets isolated per workspace vs shared across instances
- **Scaling Patterns**: Specify how workspace instances should scale and distribute

### Workspace Instance Responsibilities

#### Runtime Management
- **Instance Lifecycle**: Handle workspace creation, suspension, resumption, and termination
- **State Management**: Maintain consistent state for this specific workspace instance
- **Resource Allocation**: Manage actual resource usage within defined boundaries
- **Session Management**: Handle discrete interaction sessions for this workspace

#### Execution Context
- **Agent Instances**: Running agent instances configured per the Cortex specification  
- **Memory State**: Actual memory contents and state for this workspace
- **Active Sessions**: Current and historical sessions specific to this workspace
- **Context Isolation**: Maintain separation from other workspace instances

## Architecture Layers

### Layer 1: Cortex Configuration Layer
The application definition layer that specifies structure and coordination patterns.

**Components:**
- **App Definition**: Core application structure and capabilities specification
- **Configuration Schema**: Template for workspace configuration inheritance
- **Coordination Patterns**: Agent interaction and communication pattern definitions
- **Resource Templates**: Specification for workspace resource allocation patterns

### Layer 1b: Workspace Runtime Layer  
The foundational runtime layer that provides actual workspace boundaries and resource management.

**Components:**
- **Workspace Controller**: Individual workspace instance lifecycle management
- **Resource Manager**: Actual resource coordination and allocation for this workspace
- **State Coordinator**: Consistent state management for this workspace instance
- **Instance Manager**: Management of this specific workspace's runtime state

### Layer 2: Agent Management
Handles all aspects of agent lifecycle and coordination within the workspace.

**Components:**
- **Agent Registry**: Catalog of available agents and their metadata
- **Agent Factory**: Agent instantiation and configuration
- **Agent Supervisor**: Runtime monitoring and health management
- **Communication Hub**: Inter-agent message routing and coordination

### Layer 3: Session Control
Manages discrete interaction sessions and their persistence.

**Components:**
- **Session Manager**: Session creation, tracking, and lifecycle
- **Context Manager**: Session context preservation and restoration
- **Persistence Layer**: Session state serialization and storage
- **History Tracker**: Interaction history and audit trail management

### Layer 4: Memory Integration
Provides unified interface to various memory systems and ensures consistency.

**Components:**
- **Memory Interface**: Abstraction layer for different memory backends
- **Memory Router**: Intelligent routing of memory operations based on content type
- **Consistency Manager**: Ensures memory consistency across concurrent operations
- **Memory Optimizer**: Performance optimization and garbage collection

### Layer 5: Execution Layer
The actual execution components that perform work within the managed environment.

**Components:**
- **Orchestrator**: Determines which agent to invoke for specific tasks
- **Agent Runtime**: Individual agent execution environments
- **Tool Registry**: Available tools and their execution contexts
- **Interface Adapters**: External system integration points

## Cortex vs Workspace Architecture

### Cortex Configuration Structure
```
Cortex Configuration (App Definition)
├── Agent Specifications
│   ├── Agent Types
│   ├── Capability Definitions  
│   └── Interaction Patterns
├── Memory Architecture
│   ├── Memory System Types
│   ├── Backend Configurations
│   └── Consistency Models
├── Communication Patterns
│   ├── Agent-to-Agent Protocols
│   ├── Event Patterns
│   └── Coordination Logic
├── Tool Registry
│   ├── Available Tool Types
│   ├── Tool Configurations
│   └── Access Control Templates
└── Orchestration Logic
    ├── Task Routing Rules
    ├── Agent Selection Logic
    └── Workflow Definitions
```

### Workspace Instance Structure  
```
Workspace Instance (Runtime State)
├── Workspace Metadata
│   ├── Instance ID
│   ├── User/Purpose Context
│   └── Cortex Configuration Reference
├── Agent Pool
│   ├── Live Agent Instances
│   ├── Agent Runtime State
│   └── Communication Channels
├── Session Store
│   ├── Active Sessions
│   ├── Session History
│   └── Context Snapshots
├── Memory State
│   ├── Vector Store Data
│   ├── Graph Store Data
│   ├── Temporal Store Data
│   └── Custom Backend Data
└── Runtime Resources
    ├── Allocated Resources
    ├── Tool Instances
    └── External Connections
```

### Instance Isolation
Each workspace instance operates as an isolated environment with:
- **Data Isolation**: Complete separation of memory contents and session data
- **Resource Isolation**: Independent resource allocation and usage tracking
- **State Isolation**: Isolated runtime state that doesn't affect other instances
- **Configuration Isolation**: Instance-specific configuration overrides and customizations

### Multi-Instance Patterns
A single Cortex configuration can support:
- **User-Specific Workspaces**: Each user gets their own workspace instance
- **Purpose-Specific Workspaces**: Different workspace instances for different use cases
- **Environment-Specific Workspaces**: Development, staging, and production instances
- **Tenant-Specific Workspaces**: Multi-tenant isolation in enterprise deployments

## Session Architecture

### Session Lifecycle
1. **Session Initialization**
   - Create session context within workspace
   - Initialize agent states and memory contexts
   - Establish session-specific resource allocations

2. **Session Execution**
   - Route interactions through appropriate agents
   - Maintain session state consistency
   - Track interaction history and context evolution

3. **Session Persistence**
   - Capture session state snapshots
   - Serialize context and memory states
   - Store session metadata and history

4. **Session Restoration**
   - Reload session context and state
   - Reinitialize agent configurations
   - Restore memory contexts and tool access

### Context Management
- **Session Context**: Interaction-specific information and state
- **Agent Context**: Agent-specific memory and configuration state
- **Workspace Context**: Shared workspace-level information and resources
- **Global Context**: Framework-level configuration and system state

## Agent Orchestration

### Agent Coordination Models

#### Single-Agent Mode
- Direct agent invocation for simple use cases
- Session context passed directly to agent
- Minimal coordination overhead

#### Multi-Agent Collaborative Mode
- Agents work together on shared tasks
- Cortex coordinates resource access and communication
- Shared memory and context management

#### Multi-Agent Competitive Mode
- Multiple agents provide alternative approaches
- Cortex manages result comparison and selection
- Isolated execution with result aggregation

#### Pipeline Mode
- Sequential agent execution in defined workflows
- Context flows through agent pipeline
- Cortex manages pipeline state and error handling

### Communication Patterns
- **Direct Communication**: Agent-to-agent direct messaging
- **Broadcast Communication**: One-to-many message distribution
- **Event-Driven Communication**: Asynchronous event-based coordination
- **Shared State Communication**: Communication through shared memory/context

## Memory Architecture

### Memory System Integration
The Cortex provides a unified interface to heterogeneous memory systems:

#### Vector Memory
- Semantic search and similarity matching
- Document and conversation embedding storage
- Cross-agent knowledge sharing

#### Graph Memory
- Relationship tracking and knowledge graphs
- Entity recognition and connection mapping
- Temporal relationship evolution

#### Temporal Memory
- Time-series event tracking
- Conversation flow and decision history
- Contextual memory based on time windows

#### Custom Memory Backends
- Plugin architecture for specialized memory systems
- Standard interface contract for integration
- Cortex-managed lifecycle and consistency

### Memory Consistency Models
- **Strong Consistency**: All agents see identical memory state
- **Eventual Consistency**: Memory updates propagate asynchronously
- **Session Consistency**: Consistent memory view within session boundaries
- **Causal Consistency**: Memory updates respect causal ordering

## Configuration Architecture

### Configuration Hierarchy
1. **Framework Defaults**: Base configuration for all components across the framework
2. **Cortex Configuration**: Application-level definitions (the "app blueprint")
3. **Workspace Configuration**: Instance-specific overrides and customizations  
4. **Agent Configuration**: Agent-specific behavior within the workspace instance
5. **Session Configuration**: Session-specific parameters and constraints
6. **Runtime Configuration**: Dynamic configuration updates during execution

### Configuration Inheritance Pattern
- **Cortex Configuration** defines the application structure and default behaviors
- **Workspace Instances** inherit from Cortex config but can override specific settings
- **Multiple Workspaces** can share the same Cortex config while maintaining independent state
- **Configuration Updates** to Cortex affect new workspace instances, not existing ones

### Configuration Sources
- **JSON Files**: Declarative configuration for rapid setup
- **API Configuration**: Programmatic configuration through framework APIs
- **Environment Variables**: System-level configuration injection
- **Dynamic Updates**: Runtime configuration changes through Cortex APIs

### Configuration Composition
- **Inheritance Chains**: How configurations inherit and override through the hierarchy
- **Environment Binding**: Development/staging/production configuration variants
- **Template System**: Reusable configuration components and mixins
- **Validation Pipeline**: Schema validation and dependency checking at load time

### JSON-to-API Mapping
- **Parser Architecture**: How JSON configurations become runtime objects
- **Dynamic Loading**: Runtime configuration updates without workspace restart
- **Type System**: Strong typing for configuration validation and IntelliSense
- **Error Handling**: Configuration error reporting and recovery strategies

## Operations Architecture

### Operation Types
- **Core Operations**: Built-in framework operations (prompting, memory access, routing)
- **Interface Operations**: External system integrations (REST APIs, databases, files)
- **Control Operations**: Flow control (conditionals, loops, switches, branching)
- **Custom Operations**: User-defined operations and plugins for domain logic

### Rules Engine Integration
- **Fact Store**: How facts are stored and managed within workspace memory systems
- **Rule Evaluation**: Forward and backward chaining execution patterns
- **Unification Engine**: Pattern matching and variable binding mechanisms
- **Context Integration**: How rules interact with agent context and workspace memory

## Error Handling & Recovery Architecture

### Error Categories
- **Configuration Errors**: Invalid JSON, missing dependencies, schema violations
- **Runtime Errors**: Agent failures, memory system failures, operation timeouts
- **Integration Errors**: External API failures, network issues, authentication problems
- **Resource Errors**: Memory exhaustion, disk space, concurrent access limits

### Recovery Strategies
- **Graceful Degradation**: Fallback behaviors when components fail or are unavailable
- **Session Recovery**: Restore sessions after workspace failures with state consistency
- **Agent Restart**: Automatic agent recovery and state restoration after crashes
- **Circuit Breakers**: Prevent cascade failures in distributed deployments

## Security & Isolation Architecture

### Workspace Isolation
- **Process Isolation**: Separate processes for workspace instances when needed
- **Memory Isolation**: Prevent cross-workspace memory access and data leakage
- **File System Isolation**: Sandboxed file access per workspace with defined boundaries
- **Network Isolation**: Controlled external access per workspace based on configuration

### Agent Security
- **Tool Sandboxing**: Restrict agent tool access based on workspace configuration
- **API Key Management**: Secure credential handling per workspace instance
- **Audit Logging**: Complete audit trail of agent actions and decision points
- **Permission Models**: Role-based access to workspace resources and capabilities

## Integration Points

### External System Integration
- **API Endpoints**: RESTful interfaces for external system interaction
- **Event Streams**: Real-time event publishing and consumption
- **Database Connectors**: Direct database integration for data persistence
- **Message Queues**: Asynchronous message processing integration

### Framework Extensions
- **Plugin Architecture**: Standard interfaces for framework extensions
- **Custom Agents**: User-defined agent implementations
- **Custom Memory Systems**: Specialized memory backend implementations
- **Custom Tools**: Domain-specific tool implementations

## Deployment Patterns

### Single-Node Deployment
- **All-in-one**: Cortex, workspaces, and agents on single machine
- **Resource Sharing**: Efficient resource utilization patterns for development
- **Local Memory**: File-based and in-memory backends for simple deployments

### Distributed Deployment  
- **Cortex Controller**: Central coordination node managing workspace distribution
- **Workspace Nodes**: Distributed workspace execution across multiple machines
- **Shared Memory**: Network-attached memory systems for cross-workspace access
- **Service Mesh**: Inter-component communication patterns and service discovery

### Cloud-Native Patterns
- **Container Orchestration**: Kubernetes deployment strategies and resource management
- **Auto-scaling**: Dynamic workspace and agent scaling based on demand
- **State Management**: Persistent volume strategies for session and memory data
- **Multi-Region**: Cross-region workspace distribution for global deployments

## Monitoring & Observability Architecture

### Metrics Collection
- **Workspace Metrics**: Resource usage, session counts, performance characteristics
- **Agent Metrics**: Response times, error rates, tool usage patterns
- **Memory Metrics**: Storage utilization, query performance, cache hit rates
- **System Metrics**: CPU, memory, disk usage patterns across deployment

### Distributed Tracing
- **Request Flows**: Trace requests across agents and operations in multi-agent scenarios
- **Context Propagation**: Maintain trace context through agent chains and tool calls
- **Performance Profiling**: Identify bottlenecks in agent workflows and operations
- **Error Attribution**: Link errors to specific agents, operations, and configurations

## Scalability Considerations

### Horizontal Scaling
- **Multi-Workspace Deployment**: Independent workspace scaling across nodes
- **Agent Pool Scaling**: Dynamic agent instance management and load balancing
- **Memory System Scaling**: Distributed memory backend support for large deployments
- **Load Distribution**: Intelligent request routing and load balancing strategies

### Performance Optimization
- **Resource Pooling**: Efficient resource reuse across sessions and workspace instances
- **Lazy Loading**: On-demand component initialization to reduce startup overhead
- **Caching Strategies**: Multi-level caching for configuration, memory, and computation
- **Asynchronous Operations**: Non-blocking operation support throughout the framework

This architecture positions the Cortex as the central nervous system that coordinates all framework components while maintaining clean separation of concerns and enabling flexible deployment patterns.