import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import sqlite3
import requests

MODEL = "qwen2.5:7b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
ollama = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"
)
print("Using Ollama:", MODEL)

def genome_db_query(intent, tf, assay=None, matrix_type=None):
    print(f"Tool called for {intent},transciption factor {tf}")
    conn = sqlite3.connect("Genomic_chatbot/genome.db")
    cur = conn.cursor()

    if intent == "TF_INFO":
        result = cur.execute(
            "SELECT * FROM tf_metadata WHERE tf=?", (tf,)
        ).fetchall()

    elif intent == "MOTIF_INFO":
        result = cur.execute(
            "SELECT consensus, gc_content, ic_total FROM motifs WHERE tf=?", (tf,)
        ).fetchall()

    elif intent == "MATRIX":
        result = cur.execute(
            "SELECT matrix_type, matrix_json FROM matrices WHERE motif_id LIKE ? AND matrix_type=?",
            (f"{tf}%", matrix_type)
        ).fetchall()

    elif intent == "METRICS":
        result = cur.execute(
            "SELECT assay, context, metric_json FROM metrics WHERE motif_id LIKE ? AND assay=?",
            (f"{tf}%", assay)
        ).fetchall()

    elif intent == "THRESHOLD":
        result = cur.execute(
            "SELECT threshold_json FROM thresholds WHERE motif_id LIKE ?",
            (f"{tf}%",)
        ).fetchall()

    conn.close()
    return json.dumps(result)

tools = [
    {
        "type": "function",
        "function": {
            "name": "genome_db_query",
            "description": "Query the genomics database for information about transcription factors, motifs, matrices, metrics, and thresholds. Use this tool for ANY question about specific TFs like CTCF, TP53, MYC, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": ["TF_INFO", "MOTIF_INFO", "MATRIX", "METRICS", "THRESHOLD"],
                        "description": "TF_INFO: Get transcription factor metadata. MOTIF_INFO: Get motif details (consensus, GC content). MATRIX: Get position matrices (PCM/PWM/PFM). METRICS: Get assay metrics. THRESHOLD: Get threshold data."
                    },
                    "tf": {
                        "type": "string",
                        "description": "The transcription factor name (e.g., 'CTCF', 'TP53', 'MYC')"
                    },
                    "assay": {
                        "type": "string",
                        "description": "Assay type for METRICS intent (e.g., 'ChIP-seq', 'SELEX')"
                    },
                    "matrix_type": {
                        "type": "string",
                        "enum": ["PCM", "PWM", "PFM"],
                        "description": "Matrix type for MATRIX intent: PCM (Position Count Matrix), PWM (Position Weight Matrix), or PFM (Position Frequency Matrix)"
                    }
                },
                "required": ["intent", "tf"]
            }
        }
    }
]


system_message = """
You are a genome assistant with access to a specialized genomics database.

YOUR DUAL ROLE:
1. Database queries for specific data
2. Biology education and concept explanation

WHEN TO USE THE DATABASE (genome_db_query tool):
CRITICAL - You MUST use the tool for questions about SPECIFIC:
- Transcription factors (TF) - e.g., "Tell me about CTCF", "What is TP53's motif?"
- Motifs - e.g., "Show me MYC motif consensus sequence"
- Matrices (PCM, PWM, PFM) - e.g., "Get the PWM for SOX2"
- Metrics and assays - e.g., "What are the ChIP-seq metrics for STAT3?"
- Thresholds - e.g., "What's the threshold for FOXP2?"

NEVER answer questions about specific TFs or their data from general knowledge - ALWAYS use the tool first.

WHEN TO USE YOUR KNOWLEDGE (no tool needed):
Answer directly using your biological knowledge for:
- General concepts - e.g., "What is a transcription factor?", "Explain what PWM means"
- Terminology definitions - e.g., "What does GC content mean?", "Define consensus sequence"
- Biological processes - e.g., "How does transcription work?", "What is chromatin?"
- Comparisons - e.g., "Difference between PCM and PWM?", "ChIP-seq vs SELEX?"
- General advice - e.g., "How to analyze motifs?", "Best practices for TF analysis?"

RESPONSE GUIDELINES:
- For specific TF queries: Use tool first, then explain in simple terms
- For concept questions: Explain clearly without jargon, use analogies when helpful
- For mixed questions: Use tool for specific data, your knowledge for concepts
- Always be educational and clear - assume user may not know all terminology

EXAMPLES:
❌ "Tell me about CTCF" → Use tool (specific TF data)
✓ "What is a transcription factor?" → Use your knowledge (general concept)
❌ "What's the motif for TP53?" → Use tool (specific data)
✓ "What does motif consensus sequence mean?" → Use your knowledge (definition)
✓ "Explain what GC content tells us" → Use your knowledge (concept)
❌ "Show me STAT3 metrics" → Use tool (specific data)

Do not make up or guess specific genomic data - always use the tool for factual database queries.
"""

def handle_tool_calls(message):
    tool_responses = []

    for tool_call in message.tool_calls:
        try:
            args = json.loads(tool_call.function.arguments)
            
            print(f"Tool called: {tool_call.function.name}")
            print(f"Arguments: {args}")

            result = genome_db_query(
                intent=args["intent"],
                tf=args["tf"],
                assay=args.get("assay"),
                matrix_type=args.get("matrix_type")
            )

            # Result is already JSON string from genome_db_query
            # Don't double-encode it
            content = result if result else "[]"

            tool_responses.append({
                "role": "tool",
                "content": content,
                "tool_call_id": tool_call.id
            })
            
            print(f"Tool response: {content[:200]}...")  # Print first 200 chars
            
        except Exception as e:
            print(f"Error in tool execution: {str(e)}")
            import traceback
            traceback.print_exc()
            
            tool_responses.append({
                "role": "tool",
                "content": f"Error: {str(e)}",
                "tool_call_id": tool_call.id
            })

    return tool_responses


def chat(message, history):
    try:
        messages = [{"role": "system", "content": system_message}]

        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        print(f"\n=== User query: {message} ===")

        # Get initial response
        response = ollama.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        
        print(f"Has tool_calls API: {bool(msg.tool_calls)}")

        # Standard API tool calls
        if msg.tool_calls:
            print(f"Tool calls via API: {[tc.function.name for tc in msg.tool_calls]}")
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in msg.tool_calls
                ]
            })
            
            tool_responses = handle_tool_calls(msg)
            messages.extend(tool_responses)

            # Get final response WITHOUT tools to prevent loops
            response = ollama.chat.completions.create(
                model=MODEL, 
                messages=messages
                # No tools parameter here - prevents re-calling
            )
            return response.choices[0].message.content or "No data found."
        
        # Fallback: Parse JSON tool calls from text
        elif msg.content and '"genome_db_query"' in msg.content:
            print("Parsing tool call from text response...")
            
            import re
            # Find the FIRST tool call only
            json_match = re.search(r'\{"name":\s*"genome_db_query"[^}]*"arguments":\s*\{[^}]+\}\}', msg.content)
            
            if json_match:
                try:
                    tool_json = json_match.group(0)
                    print(f"Extracted: {tool_json}")
                    
                    tool_data = json.loads(tool_json)
                    args = tool_data["arguments"]
                    
                    # Execute tool
                    print(f"Executing: intent={args.get('intent')}, tf={args.get('tf')}")
                    result = genome_db_query(
                        intent=args["intent"],
                        tf=args["tf"],
                        assay=args.get("assay"),
                        matrix_type=args.get("matrix_type")
                    )
                    
                    print(f"✓ Database returned {len(result)} characters")
                    
                    # Parse the result
                    db_data = json.loads(result)
                    
                    if not db_data or db_data == []:
                        return f"No data found in database for {args['tf']}."
                    
                    # Create a strong directive to prevent tool re-calling
                    follow_up = f"""The database query was successful. Here is the data:{result}
                    Based on this database result, explain the information about {args['tf']} in clear, 
                    simple terms. Focus on what the data means biologically. Do NOT attempt to query the
                    database again - you already have all the data you need above.
                    """
                    
                    messages.append({"role": "assistant", "content": "Let me query the database for that information."})
                    messages.append({"role": "user", "content": follow_up})
                    
                    # Call WITHOUT tools parameter to prevent loops
                    response = ollama.chat.completions.create(
                        model=MODEL, 
                        messages=messages
                        # Intentionally no tools here
                    )
                    
                    final_response = response.choices[0].message.content
                    print(f"✓ Generated final response: {len(final_response)} characters")
                    return final_response
                    
                except Exception as e:
                    print(f"❌ Error in tool execution: {e}")
                    import traceback
                    traceback.print_exc()
                    return f"Error accessing database: {str(e)}"

        # Normal response (no tool needed)
        return msg.content or "No response generated."
    
    except Exception as e:
        print(f"❌ Error in chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"An error occurred: {str(e)}"
    
    
gr.ChatInterface(fn=chat, 
                 type="messages",
                 examples=["What are Transcription Factors","Give me Motif Details of CTCF Transcription factor","Which family does SP1 Belong to","Give me uniprot id for CREB1 TF"],
                 title="GenoMind",
                 description="""GenoMind combines a comprehensive genomics database with AI intelligence. 
Search for transcription factor data, motif sequences, and binding matrices 
while getting clear explanations of biological terminology and concepts.
"""
                 ).launch()