# AI Hedge Fund – Multi-Agent AI Research Framework

AI Hedge Fund is an **open-source research framework for experimenting with multi-agent AI systems applied to financial analysis and investment decision simulation.**

The project explores how **large language models (LLMs)** and specialized AI agents can collaborate to analyze market data, evaluate investment opportunities, and simulate portfolio decisions.

⚠️ **Important:**
This project is a **research and educational prototype** and **does not execute real trades**.

---

# Project Background

This project is inspired by and built upon the original project:

https://github.com/virattt/ai-hedge-fund

This repository includes **modifications, improvements, and additional research tooling** aimed at exploring:

* multi-agent AI collaboration
* LLM reasoning workflows
* financial data analysis with AI
* automated decision aggregation

The goal is to provide a **sandbox environment for developers and researchers** to study how AI agents interact in complex analytical environments.

---

# Project Highlights

• Multi-agent AI framework for financial analysis
• LLM-powered reasoning and decision simulation
• Modular agent architecture for experimentation
• Supports multiple LLM providers (OpenAI, Groq, local models)
• Designed for research, experimentation, and developer exploration

---

# System Architecture

The framework simulates a **virtual hedge fund composed of multiple AI agents**.
Each agent represents a different investment philosophy or analytical perspective.

Agents analyze market data and generate trading signals which are aggregated by the portfolio manager.

---

## Investment Strategy Agents

These agents represent well-known investment styles.

1. **Aswath Damodaran Agent** – valuation-driven analysis
2. **Ben Graham Agent** – deep value investing with margin of safety
3. **Bill Ackman Agent** – activist investing approach
4. **Cathie Wood Agent** – innovation-driven growth investing
5. **Charlie Munger Agent** – long-term business quality evaluation
6. **Michael Burry Agent** – contrarian deep value analysis
7. **Mohnish Pabrai Agent** – asymmetric risk-reward opportunities
8. **Peter Lynch Agent** – identifying scalable growth businesses
9. **Phil Fisher Agent** – qualitative research and business insights
10. **Rakesh Jhunjhunwala Agent** – long-term growth investing
11. **Stanley Druckenmiller Agent** – macro-driven investment strategy
12. **Warren Buffett Agent** – high-quality value investing

---

## Analytical Agents

These agents perform structured financial analysis.

13. **Valuation Agent** – intrinsic value estimation
14. **Sentiment Agent** – market sentiment analysis
15. **Fundamentals Agent** – financial statement analysis
16. **Technicals Agent** – technical indicator analysis

---

## Risk and Portfolio Management

17. **Risk Manager** – evaluates portfolio risk exposure
18. **Portfolio Manager** – aggregates agent signals and generates final decisions

---

# AI / LLM Integration

The framework supports multiple LLM providers:

• OpenAI models
• Groq models
• local models via Ollama

LLMs are used to:

* analyze financial data
* reason about investment opportunities
* generate structured trading signals
* coordinate multi-agent decision making
* explain investment reasoning

---

# Developer & Research Use Cases

This project can be used for:

• studying **multi-agent AI systems**
• experimenting with **LLM reasoning workflows**
• researching **AI-assisted financial analysis**
• prototyping **AI investment decision systems**
• testing **LLM orchestration architectures**

---

# Example Workflow

1. Fetch financial data for selected stocks
2. Each AI agent analyzes the data independently
3. Agents produce structured trading signals
4. Risk manager evaluates exposure and constraints
5. Portfolio manager aggregates signals into final decisions

---

# How to Install

Before running the AI Hedge Fund system you must install dependencies and configure API keys.

## Clone the repository

```bash
git clone https://github.com/QuantJosh/ai-hedge-fund.git
cd ai-hedge-fund
```

---

## Configure API Keys

Create a `.env` file:

```bash
cp .env.example .env
```

Add your API keys:

```
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key
GIGACHAT_API_KEY=your-gigachat-api-key
FINANCIAL_DATASETS_API_KEY=your-financial-data-api-key
```

At least **one LLM provider** must be configured.

---

# Running the Project

## Command Line Interface

Run the hedge fund simulation:

```bash
poetry run python src/main.py --ticker AAPL,MSFT,NVDA
```

Optional flags:

```
--show-reasoning
--ollama
--start-date
--end-date
```

---

## Running with Docker

```bash
cd docker
./run.sh --ticker AAPL,MSFT,NVDA main
```

---

# Backtesting

Run the backtesting module:

```bash
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA
```

---

# Logging and Analysis

The system includes a structured logging framework to analyze AI decision making.

Features include:

• tracking agent reasoning
• monitoring LLM API usage
• analyzing response latency and cost
• visualizing investment decision flows

Example command:

```bash
python view_logs.py
```

---

# Roadmap

Planned improvements include:

• improved multi-agent coordination logic
• AI-generated trading strategy experiments
• enhanced decision explainability
• performance benchmarking between agents
• research tools for analyzing AI decision workflows

---

# Contributing

Contributions are welcome.

To contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a pull request

---

# License

This project is released under the **MIT License**.

---

# Disclaimer

This project is intended **for research and educational purposes only**.

• Not financial advice
• Not intended for real trading
• No guarantee of investment performance

Use the software responsibly and for learning purposes only.
