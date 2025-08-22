# AI Career Copilot - Agentic AI Career Assistant

**_An intelligent career management system built on the A2A protocol with Google ADK agents for academic research and demonstration purposes._**

## **IMPORTANT DISCLAIMERS**

**ACADEMIC USE ONLY**: This source code is provided **EXCLUSIVELY FOR ACADEMIC RESEARCH, EDUCATIONAL PURPOSES, AND DEMONSTRATION**. It is **NOT INTENDED FOR PRODUCTION USE** and should **NOT** be deployed in any commercial, production, or live environment.

**NO WARRANTY**: This software is provided "AS IS" without warranty of any kind. The authors and contributors make no representations about the suitability, reliability, or accuracy of this software for any purpose.

**SECURITY NOTICE**: This is a research prototype with simplified security implementations. It contains known security vulnerabilities and should **NEVER** be used in environments where security is a concern.

**LIABILITY DISCLAIMER**: By using this software, you agree that the authors and contributors are not liable for any damages, losses, or issues that may arise from its use.

**COMPLIANCE**: Users are responsible for ensuring compliance with all applicable laws, regulations, and ethical guidelines when using this software.

---

## **Table of Contents**

- [Overview](#overview)
- [Product Features](#product-features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the System](#running-the-system)
- [Usage Examples](#usage-examples)
- [Agent Details](#agent-details)
- [API Reference](#api-reference)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## **Overview**

The AI Career Copilot is a comprehensive, research-oriented career management system that demonstrates the capabilities of agentic AI systems in career assistance. Built on the Agent-to-Agent (A2A) protocol using Google's Agent Developer Kit (ADK), it showcases how multiple specialized AI agents can collaborate to provide end-to-end career support.

This system is designed to:
- Demonstrate multi-agent AI architectures
- Showcase A2A protocol implementation
- Provide research insights into AI-powered career assistance
- Serve as a reference implementation for agentic AI systems

---

## **Product Features**

### **Core Intelligence**
- **Multi-Agent Orchestration**: 18 specialized AI agents working together
- **Context-Aware Processing**: Agents maintain conversation context and user history
- **Real-Time Learning**: Continuous improvement through user interactions
- **Hallucination Reduction**: Advanced RAG and verification systems

### **Career Management**
- **Intelligent Job Matching**: AI-powered recommendations based on skills, experience, and preferences
- **Resume Tailoring**: Automated customization for specific job applications with ATS optimization
- **Application Tracking**: Comprehensive job application lifecycle management
- **Interview Coaching**: Mock interviews with AI feedback, scoring, and improvement suggestions
- **Negotiation Support**: Salary negotiation guidance and offer comparison analysis

### **Workflow Automation**
- **Referral Management**: Smart referral planning and outreach automation
- **Follow-up Scheduling**: Automated follow-up reminders and tracking
- **Compliance Monitoring**: Real-time compliance checking for applications and communications
- **Outreach Campaigns**: Automated outreach to recruiters and hiring managers

### **Advanced Capabilities**
- **Multilingual Support**: Career assistance in multiple languages
- **Voice Integration**: Real-time voice interactions for hands-free operation
- **Partner API Integration**: Direct integration with LinkedIn, Indeed, Google Jobs, and other platforms
- **Prompt Library**: Centralized prompt management with A/B testing capabilities

### **Analytics & Insights**
- **Performance Tracking**: Monitor application success rates and interview performance
- **Skill Gap Analysis**: Identify areas for improvement and skill development
- **Market Intelligence**: Real-time job market insights and salary data
- **Progress Visualization**: Interactive dashboards showing career development progress

---

## **System Architecture**

### **High-Level Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │   A2A Server    │    │   Agent Pool    │
│   (Mesop)      │◄──►│   (FastAPI)     │◄──►│   (18 Agents)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   State Mgmt    │    │   Task Mgmt     │    │   Persistence   │
│   (Mesop)      │    │   (MongoDB)     │    │   (MongoDB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Agent Architecture**
```
Orchestrator Agent (Master Coordinator)
├── Onboarding Agent (User Profile Creation)
├── Profile Graph Agent (Skill & Experience Mapping)
├── Job Ingestor Agent (Job Data Collection)
├── Matcher Agent (Job-Candidate Matching)
├── Resume Tailor Agent (Resume Customization)
├── Comms Agent (Communication Management)
├── Tracker Agent (Application Tracking)
├── Apply Agent (Application Submission)
├── Referral Agent (Referral Planning)
├── Outreach Agent (Recruiter Outreach)
├── Compliance Agent (Regulatory Compliance)
├── Interview Coach Agent (Interview Preparation)
├── Negotiation Coach Agent (Salary Negotiation)
├── Prompt Library Agent (Prompt Management)
├── Voice Agent (Voice Interactions)
├── Partner APIs Agent (Platform Integration)
└── Multilingual Agent (Language Support)
```

### **Technology Stack**
- **Frontend**: Mesop (Python-based UI framework)
- **Backend**: FastAPI (Python web framework)
- **AI Framework**: Google ADK (Agent Developer Kit)
- **LLM**: Gemini 2.0 Flash (Google AI)
- **Database**: MongoDB Cloud Atlas
- **Message Queue**: Azure Service Bus (optional)
- **Vector Search**: Azure AI Search (optional)
- **File Storage**: Azure Blob Storage (optional)

---

## **Prerequisites**

### **System Requirements**
- **Operating System**: macOS 10.15+, Ubuntu 20.04+, Windows 10+
- **Python**: 3.12 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 2GB free disk space
- **Network**: Internet connection for API access

### **Required Accounts & APIs**
1. **Google AI Platform**: [Get API Key](https://makersuite.google.com/app/apikey)
2. **MongoDB Cloud Atlas**: [Create Free Cluster](https://www.mongodb.com/cloud/atlas)
3. **Azure OpenAI** (Optional): [Azure Portal](https://portal.azure.com/)
4. **Azure AI Search** (Optional): [Azure Portal](https://portal.azure.com/)
5. **Azure Blob Storage** (Optional): [Azure Portal](https://portal.azure.com/)
6. **Azure Service Bus** (Optional): [Azure Portal](https://portal.azure.com/)

### **Software Dependencies**
- **Python 3.12+**: [Download](https://www.python.org/downloads/)
- **UV Package Manager**: [Install Guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Git**: [Download](https://git-scm.com/downloads)
- **MongoDB Compass** (Optional): [Download](https://www.mongodb.com/products/compass)

---

## **Installation & Setup**

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/your-username/A2A-RV-HR.git
cd A2A-RV-HR
```

### **Step 2: Environment Setup**
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# Google AI Platform (Required)
GOOGLE_API_KEY=your_google_api_key_here

# MongoDB Cloud Atlas (Required)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/a2a
MONGODB_DB=a2a

# Azure OpenAI (Optional)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT_GPT4O=gpt-4o
AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI=gpt-4o-mini

# UI Configuration
A2A_UI_HOST=0.0.0.0
A2A_UI_PORT=12000
DEBUG_MODE=true
```

### **Step 3: Install Dependencies**

#### **Option A: Using UV (Recommended)**
```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to the june directory
cd june

# Sync dependencies using UV
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

#### **Option B: Using pip**
```bash
# Navigate to the june directory
cd june

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### **Step 4: Install UI Dependencies**
```bash
# Navigate to UI directory
cd ../ui

# Install UI dependencies
uv sync

# Activate UI virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

### **Step 5: Verify Installation**
```bash
# Test core functionality
cd ../june
python -c "from agents.orchestrator.agent import OrchestratorAgent; print('Core agents working')"

# Test UI functionality
cd ../ui
python -c "from main import app; print('UI framework working')"
```

---

## **Running the System**

### **Step 1: Start the UI Server**
```bash
# Navigate to UI directory
cd ui

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows

# Start the UI server
uv run main.py --port 12000
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:12000 (Press CTRL+C to quit)
```

### **Step 2: Access the Web Interface**
Open your browser and navigate to: `http://localhost:12000`

### **Step 3: Start Individual Agents (Optional)**
```bash
# Navigate to june directory
cd june

# Activate virtual environment
source .venv/bin/activate

# Start Orchestrator Agent
python -m agents.orchestrator --host localhost --port 11001

# Start Job Ingestor Agent
python -m agents.job_ingestor --host localhost --port 11004

# Start other agents as needed...
```

**Agent Ports:**
- Orchestrator: 11001
- Onboarding: 11002
- Profile Graph: 11003
- Job Ingestor: 11004
- Matcher: 11005
- Resume Tailor: 11006
- Comms: 11007
- Tracker: 11008
- Apply: 11009
- Referral: 11010
- Outreach: 11011
- Compliance: 11012
- Interview Coach: 11013
- Negotiation Coach: 11014
- Prompt Library: 11015
- Voice: 11016
- Partner APIs: 11017
- Multilingual: 11018

---

## **Usage Examples**

### **Example 1: Career Planning Session**

**User Prompt:**
```
"I'm a software engineer with 5 years of experience in Python and React. 
I want to transition to a machine learning role. Can you help me plan this transition?"
```

**Agents Triggered:**
1. **Orchestrator Agent** - Analyzes request and creates workflow
2. **Profile Graph Agent** - Maps current skills and identifies gaps
3. **Job Ingestor Agent** - Searches for relevant ML job opportunities
4. **Matcher Agent** - Matches user profile with job requirements
5. **Resume Tailor Agent** - Suggests resume modifications

**Sample Output:**
```json
{
  "workflow": "career_transition_planning",
  "current_skills": ["Python", "React", "Web Development"],
  "target_skills": ["Machine Learning", "TensorFlow", "Data Science"],
  "skill_gaps": ["ML Algorithms", "Deep Learning", "Statistics"],
  "recommended_jobs": [
    {
      "title": "Machine Learning Engineer",
      "company": "TechCorp",
      "match_score": 0.75,
      "required_skills": ["Python", "ML", "TensorFlow"]
    }
  ],
  "resume_suggestions": [
    "Add ML projects section",
    "Highlight Python programming experience",
    "Include relevant coursework in statistics"
  ]
}
```

### **Example 2: Interview Preparation**

**User Prompt:**
```
"I have an interview tomorrow for a Senior Data Scientist position. 
Can you help me prepare with some practice questions?"
```

**Agents Triggered:**
1. **Orchestrator Agent** - Routes to Interview Coach
2. **Interview Coach Agent** - Generates role-specific questions
3. **Profile Graph Agent** - Analyzes user's background
4. **Compliance Agent** - Ensures interview guidelines compliance

**Sample Output:**
```json
{
  "interview_type": "senior_data_scientist",
  "questions": [
    {
      "category": "Technical",
      "question": "Explain the difference between supervised and unsupervised learning",
      "difficulty": "Intermediate",
      "expected_answer_points": [
        "Supervised learning uses labeled data",
        "Unsupervised learning finds patterns in unlabeled data"
      ]
    },
    {
      "category": "Behavioral",
      "question": "Describe a challenging project you led",
      "difficulty": "Senior",
      "expected_answer_points": [
        "Project scope and challenges",
        "Leadership approach",
        "Outcomes and learnings"
      ]
    }
  ],
  "preparation_tips": [
    "Review your ML project portfolio",
    "Prepare STAR method responses",
    "Research the company's ML initiatives"
  ]
}
```

### **Example 3: Job Application Workflow**

**User Prompt:**
```
"I found a great job posting for a Product Manager role. 
Can you help me apply and track this application?"
```

**Agents Triggered:**
1. **Orchestrator Agent** - Initiates application workflow
2. **Apply Agent** - Manages application submission
3. **Resume Tailor Agent** - Customizes resume for the role
4. **Tracker Agent** - Sets up application tracking
5. **Comms Agent** - Schedules follow-up reminders

**Sample Output:**
```json
{
  "application_id": "app_12345",
  "status": "submitted",
  "resume_customizations": [
    "Emphasized product management experience",
    "Added relevant metrics and KPIs",
    "Highlighted stakeholder management skills"
  ],
  "tracking_setup": {
    "follow_up_date": "2024-01-15",
    "reminder_frequency": "weekly",
    "next_action": "Send follow-up email"
  },
  "application_metrics": {
    "submission_time": "2024-01-08T10:30:00Z",
    "estimated_response_time": "5-7 business days"
  }
}
```

---

## **Agent Details**

### **Core Orchestration Agents**

#### **1. Orchestrator Agent**
- **Purpose**: Master coordinator for all career workflows
- **Capabilities**: Task decomposition, workflow planning, agent coordination
- **Input**: Natural language career requests
- **Output**: Structured workflow plans and task assignments

#### **2. Onboarding Agent**
- **Purpose**: User profile creation and initial setup
- **Capabilities**: Skill assessment, experience mapping, goal setting
- **Input**: User background information
- **Output**: Comprehensive user profile and career objectives

#### **3. Profile Graph Agent**
- **Purpose**: Dynamic skill and experience mapping
- **Capabilities**: Skill gap analysis, career path visualization, competency tracking
- **Input**: User profile updates and new experiences
- **Output**: Skill graphs, career progression maps, development recommendations

### **Job Management Agents**

#### **4. Job Ingestor Agent**
- **Purpose**: Collect and process job opportunities
- **Capabilities**: Multi-platform job scraping, data normalization, opportunity filtering
- **Input**: Job search criteria and preferences
- **Output**: Curated job listings with relevance scores

#### **5. Matcher Agent**
- **Purpose**: Match candidates with job opportunities
- **Capabilities**: AI-powered matching algorithms, skill alignment, cultural fit assessment
- **Input**: User profile and job requirements
- **Output**: Job-candidate match scores and recommendations

#### **6. Resume Tailor Agent**
- **Purpose**: Customize resumes for specific applications
- **Capabilities**: ATS optimization, keyword matching, content customization
- **Input**: Base resume and job description
- **Output**: Tailored resume with job-specific optimizations

### **Application Management Agents**

#### **7. Apply Agent**
- **Purpose**: Manage job application submissions
- **Capabilities**: Application tracking, submission automation, status monitoring
- **Input**: Job application details and user preferences
- **Output**: Application confirmations and tracking information

#### **8. Tracker Agent**
- **Purpose**: Monitor application status and progress
- **Capabilities**: Status tracking, timeline management, milestone tracking
- **Input**: Application updates and status changes
- **Output**: Progress reports and action recommendations

### **Communication Agents**

#### **9. Comms Agent**
- **Purpose**: Manage all career-related communications
- **Capabilities**: Email automation, follow-up scheduling, communication templates
- **Input**: Communication preferences and schedules
- **Output**: Automated messages and communication logs

#### **10. Outreach Agent**
- **Purpose**: Proactive recruiter and hiring manager outreach
- **Capabilities**: Contact discovery, personalized messaging, campaign management
- **Input**: Outreach targets and messaging strategy
- **Output**: Outreach campaigns and response tracking

### **Coaching & Development Agents**

#### **11. Interview Coach Agent**
- **Purpose**: Interview preparation and practice
- **Capabilities**: Mock interviews, feedback generation, improvement suggestions
- **Input**: Interview details and user background
- **Output**: Practice questions, feedback, and preparation tips

#### **12. Negotiation Coach Agent**
- **Purpose**: Salary and benefits negotiation support
- **Capabilities**: Market research, offer analysis, negotiation strategies
- **Input**: Job offers and user preferences
- **Output**: Negotiation strategies and counter-offer recommendations

### **Specialized Agents**

#### **13. Compliance Agent**
- **Purpose**: Ensure regulatory and ethical compliance
- **Capabilities**: Compliance checking, risk assessment, guideline enforcement
- **Input**: Actions and communications for review
- **Output**: Compliance reports and recommendations

#### **14. Prompt Library Agent**
- **Purpose**: Centralized prompt management and optimization
- **Capabilities**: Prompt versioning, A/B testing, performance optimization
- **Input**: Prompt variations and test parameters
- **Output**: Optimized prompts and performance metrics

#### **15. Voice Agent**
- **Purpose**: Voice-based interactions
- **Capabilities**: Speech-to-text, text-to-speech, voice command processing
- **Input**: Voice commands and queries
- **Output**: Spoken responses and voice-based actions

#### **16. Partner APIs Agent**
- **Purpose**: Integration with external platforms
- **Capabilities**: LinkedIn, Indeed, Google Jobs integration, data synchronization
- **Input**: Platform-specific requests and credentials
- **Output**: Platform data and integration status

#### **17. Multilingual Agent**
- **Purpose**: Multi-language career assistance
- **Capabilities**: Language detection, translation, cultural adaptation
- **Input**: Queries in various languages
- **Output**: Responses in appropriate languages

---

## **API Reference**

### **Core Endpoints**

#### **Conversation Management**
```http
POST /conversation/create
POST /conversation/list
GET /conversation/{id}
```

#### **Message Handling**
```http
POST /message/send
GET /message/list
GET /message/pending
```

#### **Task Management**
```http
POST /task/send
POST /task/send_subscribe
GET /task/list
GET /task/{id}
```

#### **Agent Management**
```http
POST /agent/register
GET /agent/list
GET /agent/{id}
```

### **WebSocket Endpoints**
```http
WS /ws/conversation/{id}
WS /ws/task/{id}
```

### **Response Formats**

#### **Standard Response**
```json
{
  "jsonrpc": "2.0",
  "id": "request_id",
  "result": {
    "data": "response_data",
    "metadata": {}
  }
}
```

#### **Error Response**
```json
{
  "jsonrpc": "2.0",
  "id": "request_id",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {}
  }
}
```

---

## **Development Guide**

### **Project Structure**
```
A2A-RV-HR/
├── june/                          # Core agent framework
│   ├── agents/                    # All AI agents
│   │   ├── orchestrator/         # Master coordinator
│   │   ├── job_ingestor/         # Job data collection
│   │   ├── matcher/              # Job-candidate matching
│   │   └── ...                   # Other agents
│   ├── common/                    # Shared utilities
│   │   ├── utils/                # Utility functions
│   │   ├── server/               # A2A server implementation
│   │   └── types/                # Type definitions
│   └── requirements.txt           # Python dependencies
├── ui/                            # Web interface
│   ├── components/                # UI components
│   ├── pages/                     # Page implementations
│   ├── service/                   # Backend services
│   ├── state/                     # State management
│   └── pyproject.toml            # UI dependencies
├── env.example                    # Environment template
├── requirements.txt               # Main dependencies
└── README.md                      # This file
```

### **Adding New Agents**

#### **Step 1: Create Agent Directory**
```bash
cd june/agents
mkdir my_new_agent
cd my_new_agent
```

#### **Step 2: Implement Core Files**
```python
# agent.py
from google.adk.agents.llm_agent import LlmAgent

class MyNewAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "application/json"]
    
    def __init__(self):
        self._agent = self._build_agent()
    
    def _build_agent(self) -> LlmAgent:
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="my_new_agent",
            description="Description of what this agent does",
            instruction="Instructions for the agent",
            tools=[]
        )
```

#### **Step 3: Create Task Manager**
```python
# task_manager.py
from common.server.task_manager import InMemoryTaskManager

class MyNewAgentTaskManager(InMemoryTaskManager):
    def __init__(self, agent: MyNewAgent):
        super().__init__()
        self.agent = agent
```

#### **Step 4: Create Main Entry Point**
```python
# __main__.py
from common.server import A2AServer
from .agent import MyNewAgent
from .task_manager import MyNewAgentTaskManager

def main():
    agent = MyNewAgent()
    task_manager = MyNewAgentTaskManager(agent)
    
    server = A2AServer(
        agent_card=agent_card,
        task_manager=task_manager,
        host="localhost",
        port=11019
    )
    server.start()

if __name__ == "__main__":
    main()
```

#### **Step 5: Update Configuration**
```bash
# Add to env.example
A2A_AGENT_URLS=http://localhost:11001,...,http://localhost:11019
```

### **Testing Agents**

#### **Unit Testing**
```bash
cd june
python -m pytest tests/agents/test_my_new_agent.py -v
```

#### **Integration Testing**
```bash
# Start the agent
python -m agents.my_new_agent --host localhost --port 11019

# Test from another terminal
curl -X POST http://localhost:11019/task/send \
  -H "Content-Type: application/json" \
  -d '{"method": "task/send", "params": {...}}'
```

---

## **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```bash
# Error: ModuleNotFoundError: No module named 'common'
# Solution: Ensure you're in the correct directory and virtual environment
cd june
source .venv/bin/activate
python -c "from common.types import Message; print('OK')"
```

#### **2. MongoDB Connection Issues**
```bash
# Error: Connection refused
# Solution: Check MongoDB URI and network access
# Verify: MONGODB_URI in .env file
# Test: mongosh "your_connection_string"
```

#### **3. Google API Key Issues**
```bash
# Error: Invalid API key
# Solution: Verify GOOGLE_API_KEY in .env
# Check: https://makersuite.google.com/app/apikey
```

#### **4. Port Already in Use**
```bash
# Error: Address already in use
# Solution: Change port or kill existing process
lsof -ti:12000 | xargs kill -9
# or
uv run main.py --port 12001
```

#### **5. UV Sync Issues**
```bash
# Error: uv sync failed
# Solution: Clear cache and retry
uv cache clean
uv sync
```

### **Debug Mode**
```bash
# Enable debug logging
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# Start with verbose output
uv run main.py --port 12000 --log-level debug
```

### **Log Files**
```bash
# Check application logs
tail -f logs/app.log

# Check error logs
tail -f logs/error.log
```

---

## **Contributing**

### **Development Setup**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `python -m pytest`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### **Code Standards**
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for all classes and methods
- Write comprehensive tests
- Update documentation for new features

### **Testing Guidelines**
- Maintain >90% code coverage
- Include unit tests for all new functionality
- Add integration tests for agent interactions
- Test error handling and edge cases

---

## **License**

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## **Acknowledgments**

- **Google ADK Team** - For the Agent Developer Kit framework
- **MongoDB** - For the database infrastructure
- **FastAPI** - For the web framework
- **Mesop** - For the UI framework
- **OpenAI** - For LLM capabilities
- **Azure** - For cloud services integration

---

## **Support**

For academic research questions, development issues, or general inquiries:

- **Issues**: [GitHub Issues](https://github.com/your-username/A2A-RV-HR/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/A2A-RV-HR/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/A2A-RV-HR/wiki)

---

## **Version History**

- **v1.0.0** - Initial academic release with 18 agents
- **v0.9.0** - Beta version with core functionality
- **v0.8.0** - Alpha version with basic agent framework

---

**Last Updated**: August 2025  
**Version**: 1.0.0  
**Status**: Academic Research Release
