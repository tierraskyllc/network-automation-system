# Hybrid Network Automation System
## LangGraph/LangChain/MCP with pyATS/Genie Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

A comprehensive network automation system that combines the power of LangGraph workflow orchestration, LangChain natural language processing, and Model Context Protocol (MCP) for intelligent network device management.

## 🚀 Features

### Core Capabilities
- **Natural Language Interface**: Interact with network devices using conversational commands
- **Intelligent Workflow Orchestration**: Complex multi-device operations with LangGraph
- **Rich Context Management**: MCP-powered device and topology awareness
- **Multi-Vendor Support**: pyATS/Genie integration for Cisco, Juniper, Arista, and more
- **Comprehensive Topology Discovery**: Automated network mapping and relationship tracking
- **Enterprise Security**: Role-based access control, audit logging, and credential management

### Supported Platforms
- **Cisco**: IOS, IOS-XE, IOS-XR, NX-OS, WLC (Wireless Controllers)
- **Juniper**: JunOS
- **Arista**: EOS
- **Future**: Palo Alto, Fortinet, F5, and more

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│                  (CLI + Web Dashboard)                      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Gateway                           │
│              (Authentication & Routing)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   LangChain     │  │   LangGraph     │  │   MCP Server    │
│   (NL Processing)│  │  (Workflows)    │  │  (Context)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Network Execution Layer                        │
│                 (pyATS/Genie)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Database                          │
│        (Devices, Topology, Commands, Audit)                │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 15+ with JSONB support
- **Caching**: Redis
- **Network Automation**: pyATS/Genie, Unicon
- **AI/ML**: LangChain, LangGraph, OpenAI/Ollama
- **Context Protocol**: Model Context Protocol (MCP)
- **Containerization**: Docker, Docker Compose
- **Monitoring**: Prometheus, Grafana
- **Testing**: pytest, pytest-asyncio

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher
- Redis 7 or higher
- Docker and Docker Compose (for containerized deployment)
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/network-automation-system.git
cd network-automation-system
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Start PostgreSQL and Redis with Docker
docker-compose -f deployment/docker-compose/docker-compose.dev.yml up -d postgres redis

# Run database migrations
alembic upgrade head
```

### 4. Configuration
```bash
# Copy environment template
cp configs/env.template .env

# Edit .env with your settings
# - Database connection
# - OpenAI API key (or Ollama endpoint)
# - Device credentials
```

### 5. Start the System
```bash
# Development mode
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or use Docker Compose
docker-compose -f deployment/docker-compose/docker-compose.dev.yml up
```

### 6. Access the System
- **API Documentation**: http://localhost:8000/docs
- **Web Interface**: http://localhost:3000
- **Monitoring**: http://localhost:3001 (Grafana)

## 📖 Documentation

### Quick Links
- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [API Reference](docs/api-reference.md)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)

### Architecture Documentation
- [System Architecture](docs/architecture/system-architecture.md)
- [Database Schema](docs/architecture/database-schema.md)
- [MCP Implementation](docs/architecture/mcp-implementation.md)
- [Security Model](docs/architecture/security-model.md)

### Operational Guides
- [Deployment Guide](docs/operations/deployment.md)
- [Monitoring Setup](docs/operations/monitoring.md)
- [Backup & Recovery](docs/operations/backup-recovery.md)
- [Troubleshooting](docs/operations/troubleshooting.md)

## 🎯 Usage Examples

### Natural Language Commands
```bash
# CLI Interface
network-automation interactive

> Add a new Cisco wireless controller at 192.168.1.10
> Show me the status of all access points on WLC-CORP-01
> Find all devices connected to VLAN 100
> Backup configurations of all core routers
```

### API Usage
```python
import httpx

# Execute command via API
async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:8000/api/v1/natural-language/process", 
        json={"input": "Show interface status on router-01"})
    print(response.json())
```

### Workflow Creation
```python
from src.langgraph_layer.workflows import WorkflowBuilder

# Create multi-device workflow
workflow = WorkflowBuilder() \
    .add_command_step("Backup Config", "show_running_config", "router-01") \
    .add_command_step("Update SNMP", "configure_snmp", "router-01", {"community": "new-string"}) \
    .add_validation_step("Verify Config", "show_running_config", "router-01") \
    .build("SNMP Update Workflow")
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run with coverage
pytest --cov=src --cov-report=html
```

## 🚀 Deployment

### Docker Compose (Recommended)
```bash
# Production deployment
docker-compose -f deployment/docker-compose/docker-compose.prod.yml up -d

# Development deployment
docker-compose -f deployment/docker-compose/docker-compose.dev.yml up -d
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f deployment/kubernetes/
```

## 🔧 Development

### Project Structure
```
src/
├── api/                 # FastAPI application
├── core/               # Database models and core utilities
├── langchain_layer/    # Natural language processing
├── langgraph_layer/    # Workflow orchestration
├── mcp_server/         # Model Context Protocol implementation
├── network_layer/      # Network device connectivity
└── topology/           # Network topology management

docs/                   # Documentation
tests/                  # Test suites
docker/                 # Docker configurations
deployment/             # Deployment configurations
monitoring/             # Monitoring configurations
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Monitoring

The system includes comprehensive monitoring with:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting
- **Application metrics**: Command execution, workflow performance
- **Infrastructure metrics**: Database, API, network connectivity

## 🔒 Security

- **Authentication**: JWT with multi-factor authentication
- **Authorization**: Role-based access control (RBAC)
- **Credential Management**: HashiCorp Vault integration
- **Audit Logging**: Comprehensive audit trail
- **Network Security**: Encrypted connections, credential rotation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/network-automation-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/network-automation-system/discussions)

## 🙏 Acknowledgments

- [pyATS/Genie](https://developer.cisco.com/pyats/) - Network automation framework
- [LangChain](https://langchain.com/) - LLM application framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - Context management standard
