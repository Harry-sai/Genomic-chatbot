# 🧬 Genomic-Chatbot

A domain-specific AI assistant for querying **genomic transcription factor data** using an **agentic AI tool-calling mechanism**.
Instead of just generating generic biology answers, this bot can perform live database lookups for detailed genomic properties like motifs, binding matrices, metrics, and thresholds — then explain them in simple terms.

---

## 🧠 What This Project Is

**Genomic-Chatbot (GenoMind)** is:

* A biology-aware AI chat interface
* Connected to a structured **genomics database**
* Designed to provide factual answers about *transcription factors*
* Capable of retrieving and explaining experimental and sequence data

The AI is powered by an LLM (hosted locally via Ollama) and can call a custom Python function to run SQL queries on a structured database. The result is grounded answers, not hallucinations.

---

## 📦 What Data Is Present

The core dataset is a **collection of genomic annotations** focused on **transcription factors and motifs**. The database schema includes:

### 🔹 `motifs`

* Motif identifiers
* Associated TF name
* Motif consensus sequence
* Information content, GC content
* Quality and counts

### 🔹 `tf_metadata`

* Transcription factor identifiers
* Taxonomy and family classification
* Structural classifications

### 🔹 `gene_info`

* Per-species gene details
* Gene symbols and protein identifiers (e.g. UniProt IDs)

### 🔹 `matrices`

* Motif position matrices (PCM, PWM, PFM)

### 🔹 `metrics`

* Assay results (e.g., ChIP-seq, SELEX)

### 🔹 `thresholds`

* Numerical threshold values for motifs

This gives the chatbot deep access to structured genomic attributes such as sequence matrices, experimental metrics, and biological classifications.

---

## 🚀 How It Actually Works

### ⭐ Two Parts

1. **Database (SQLite)**

   * Built via `create_db.py`
   * Ingests JSONL annotation files using `ingest.py`

2. **AI Chat Interface (`main.py`)**

   * Uses **Ollama LLM** with a tool calling mechanism
   * When a biologically specific query is asked (e.g., “Motif for CTCF?”), the bot:

     1. Detects the intent (TF_INFO, MATRIX, METRICS, etc.)
     2. Calls `genome_db_query(...)`
     3. Runs SQL against the local database
     4. Returns structured JSON results
     5. The LLM then combines that with explanation

The system decouples **factual lookup** from **biological reasoning**, giving you real data + clear explanation.

---

## 🧠 What the Bot Can Do

The chatbot is capable of domain-specific lookup such as:

✔ Transcription factor metadata
✔ Motif consensus sequences
✔ Position matrices (PCM / PWM / PFM)
✔ Assay metrics for binding experiments
✔ Threshold values for motif detection

And also general biology explanations such as:

✔ What is a transcription factor
✔ What is GC content
✔ What is a PWM/PCM

It will *always use the database* for specific requests about known entities — no guessing.

---

## 📌 Requirements

This project runs:

* Python (3.10+, ideally)
* SQLite (built-in)
* Gradio UI for web chat
* OpenAI / Ollama LLM backend

  * The repo is configured to talk to an LLM API (`OLLAMA_BASE_URL`) locally

---

## 📥 Setup

1. Clone the repository:

```bash
git clone https://github.com/Harry-sai/Genomic-chatbot.git
cd Genomic-chatbot
```

2. Create and populate the database:

```bash
# Creates the schema
python create_db.py

# Loads annotation JSONL into the SQLite database
python ingest.py
```

> Make sure your JSONL annotation file exists in `Genomic_chatbot/data/H14CORE_annotation.jsonl`.

---

## 🎯 Running the Chatbot

Make sure you have an LLM server running (e.g., **Ollama** with your desired model):

```bash
ollama serve
```

Then start the interface:

```bash
python main.py
```

This will open a Gradio chat UI titled **GenoMind** in your browser.

---

## 💬 Typical Usage

Example questions:

```text
What is the motif consensus sequence for CTCF?
Tell me uniProt ID for TP53
Give me the PWM for SOX2
Explain what GC content means
Show me ChIP-seq metrics for STAT3
```

The AI will either:

✔ Query the database using tools and return real data
✔ Answer general biology questions with explanations

---

## 🧩 Architecture Summary

```
User Query
    ↓
LLM (Ollama) interprets intent
    ↓
Tool Call? → Yes → run SQL on SQLite via genome_db_query()
                           ↓
                  JSON result from DB
                           ↓
                 LLM generates grounded answer
                           ↓
                Explained output in Gradio UI
```

---

## 💡 Design Principles

* **Structured knowledge first:** Database answers are always real and exact
* **No guessing TF properties:** The bot *must* call the DB for specific TF requests
* **General biology knowledge is delivered by the LLM itself**
* **Clear separation between data retrieval and explanation**

---

## 📎 Notes

* You must populate the database before using the chatbot in earnest.
* The LLM model is set in code (`qwen2.5:7b`) and connects via a local API — adjust this to your setup.
* The project is ideal for educational or research exploration of transcription factor properties.


✔ A **diagram** of the database relationships
✔ Example data schemas from the JSONL file
✔ A list of supported query examples and expected outputs

Just say so!
