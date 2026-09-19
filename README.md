# AI Data Analysis of Education (ADAEdu)

A comprehensive web application for analyzing student reflection data and generating insights for instructors. Built with Streamlit and Python, this system processes CSV files containing student reflections and provides topic analysis, student profiling, and report generation.

## 🚀 Features

**ADAEdu** provides a comprehensive suite of tools for educational data analysis:

- **Topic Analysis**: AI-powered classification of student reflection content using GPT models
- **Student Profiling**: Generate comprehensive HTML reports for individual students
- **Data Cleaning**: Tools for fixing ID inconsistencies and converting various file formats
- **Instructor Mode**: Streamlined interface focused on practical classroom insights
- **Report Generation**: Beautiful HTML reports with collapsible sections and modern styling
- **Summarization**: Executive, topic-wise, and per-student summaries for actionable insights

## 📋 Prerequisites

- **Python 3.8+**
- **OpenAI API Key** (for topic analysis functionality)
- **Google Drive Access** (for example data - see below)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sandrawiktor/ADAEdu.git
cd refAnalysisv0.1
```

### 2. Create Virtual Environment
```bash
# Using conda (recommended)
conda create -n reflectEnv python=3.9
conda activate reflectEnv

# Or using venv
python -m venv reflectEnv
source reflectEnv/bin/activate  # On Windows: reflectEnv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:
```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
```

### Groq for topic analysis

Topic Analysis supports OpenAI and Groq. To use Groq on Render, add
`GROQ_API_KEY` in the service's Environment settings, deploy the updated app,
and select **Groq** under **Analysis → AI provider**. For local development,
put the key in `.env`. An OpenAI key is not required for Groq topic analysis.

The default Groq model is `openai/gpt-oss-20b`. Set `GROQ_MODEL` to change the
default, or enter another supported chat model ID in the Model field.
Groq uses the existing OpenAI client library through its
[compatible endpoint](https://console.groq.com/docs/openai); no extra SDK is needed.
See [Groq's model list](https://console.groq.com/docs/models) for available models.
The provider selection applies to Topic Analysis; Summarization continues to use OpenAI.

## 📁 Example Data

**Google Drive Link**: [Example Data Folder](https://drive.google.com/drive/folders/1FDqLgNHI_BtXhNDInYPTdiFTumcjE3c7?usp=sharing)

This folder contains sample CSV files that demonstrate the expected data format:
- **Course CSV**: Contains student information and grades
- **Reflection CSV**: Contains student reflection responses
- **Results**: Example topic analysis outputs

**Note**: You'll need permission to access this folder. Contact the repository owner if you need access.

## 🚀 Running the Application

### Quick Start
```bash
# From the root directory
streamlit run application/view/analysis_UI/streamlit_app.py

# Or with PYTHONPATH set
PYTHONPATH=$PYTHONPATH:. streamlit run application/view/analysis_UI/streamlit_app.py
```

### Alternative Methods
```bash
# If you're in the application directory
cd application/view/analysis_UI
streamlit run streamlit_app.py

# With explicit Python path
python -m streamlit run streamlit_app.py
```

## 🐳 Run Docker Container

### 1. Prepare Environment Variables
```bash
# If needed
cp .env.example .env
# Then set OPENAI_API_KEY in .env
```

### 2. Build the Image
```bash
docker compose build
```

### 3. Start the Container
```bash
docker compose up
```

### 4. Start in Background (Optional)
```bash
docker compose up -d
```

### 5. Stop the Container
```bash
docker compose down
```

## 📖 Usage Guide

### 1. **Workflow Tab** - Getting Started
- Select a course folder from the dropdown
- Choose a reflection folder (e.g., "ref1", "ref2")
- Follow the usage instructions displayed

### 2. **Analysis Tab** - Topic Analysis
- Ensure you have a course and reflection selected
- Choose your topic classification prompt
- Run the analysis to process student reflections
- View results and download analysis data

### 3. **Data Cleaning Tab** - File Preparation
- Convert various reflection file formats to CSV
- Fix ID column inconsistencies
- Validate file integrity

### 4. **Generate Reports**
- Return to Workflow tab after running topic analysis
- Load reflection data
- Generate and download HTML student profile reports

## 📊 Data Requirements

### Course CSV Format
```csv
Student_ID,Name,Email,Section,Grade
12345,John Doe,john@email.com,A,85.5
12346,Jane Smith,jane@email.com,B,92.0
```

### Reflection CSV Format
```csv
Student_ID,Q1,Q2,Q3,Q4
12345,Reflection text 1,Reflection text 2,Reflection text 3,Reflection text 4
12346,Reflection text 1,Reflection text 2,Reflection text 3,Reflection text 4
```

## 🔧 Configuration

### OpenAI API Setup
1. Get your API key from [OpenAI Platform](https://platform.openai.com/)
2. Add it to your `.env` file
3. The system will automatically use it for topic analysis

### Custom Prompts
- Place your custom topic classification prompts in `application/model/prompts/`
- Use the filename `topic_analysis.json` for the default prompt
- Custom prompts can be selected during analysis

## 🏗️ Project Structure

**ADAEdu** is organized as follows:

```
refAnalysisv0.1/
├── application/
│   ├── config/              # Configuration and settings
│   ├── controller/          # API integrations and utilities
│   ├── html_builder/        # HTML report generation
│   ├── model/              # Data models and services
│   └── view/               # Streamlit UI components
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables (create this)
└── README.md              # This file
```

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure you're in the root directory
cd refAnalysisv0.1
PYTHONPATH=$PYTHONPATH:. streamlit run application/view/analysis_UI/streamlit_app.py
```

**OpenAI API Errors**
- Verify your API key is correct in `.env`
- Check your OpenAI account has sufficient credits
- Ensure the API key has the correct permissions

**File Not Found Errors**
- Verify CSV files are in the correct directory structure
- Check file permissions and paths
- Ensure files are properly formatted CSV

## 🚀 Deployment

### Local Development
```bash
# Development mode with auto-reload
streamlit run application/view/analysis_UI/streamlit_app.py --server.runOnSave true
```

### Production Deployment
1. Ensure all dependencies are installed
2. Set environment variables securely
3. Use a production WSGI server if needed
4. Consider using Streamlit Cloud for easy deployment

## 🧾 Summarization Tab

The Summarization tab adds three instructor-focused tools without changing existing workflows:

- Complete Summary: Executive overview across reflections, topics, and grades with action items
- Topic Summaries: Per-topic briefs using results in `results/{course}_{ref}_exploded.csv`
- Student Summaries: Per-student briefs filtered by grade range, unresolved-only, and urgency

Notes:
- Uses existing analysis outputs when available; otherwise falls back to reflection CSVs
- Uses your configured OpenAI key; if unavailable, provides non-LLM summaries
