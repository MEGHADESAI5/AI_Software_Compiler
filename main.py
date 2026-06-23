from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import time
from typing import Optional

from stage1_intent import extract_intent
from stage2_design import design_system
from stage3_generate import generate_all_schemas
from repair_engine import validate_and_repair
from runtime import validate_config

app = FastAPI(title="AI Software Compiler", version="1.0.0")

class PromptRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    success: bool
    config: Optional[dict] = None
    repairs: Optional[list] = None
    runtime_result: Optional[dict] = None
    error: Optional[str] = None
    latency: Optional[float] = None

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Software Compiler</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #333;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            textarea {
                width: 100%;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 10px;
                font-size: 1em;
                font-family: inherit;
                resize: vertical;
                min-height: 100px;
                transition: border-color 0.3s;
            }
            textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                border-radius: 10px;
                font-size: 1.1em;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                margin-top: 15px;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .loading {
                display: none;
                color: #667eea;
                margin-top: 15px;
            }
            .loading.active {
                display: block;
            }
            .result-container {
                margin-top: 30px;
                border-top: 2px solid #eee;
                padding-top: 30px;
            }
            .result-container h2 {
                color: #333;
                margin-bottom: 15px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-card .value {
                font-size: 1.5em;
                font-weight: bold;
                color: #667eea;
            }
            .stat-card .label {
                color: #666;
                font-size: 0.9em;
            }
            .stat-card.success .value { color: #28a745; }
            .stat-card.fail .value { color: #dc3545; }
            pre {
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
                border-radius: 10px;
                overflow-x: auto;
                font-size: 0.9em;
                max-height: 500px;
                overflow-y: auto;
            }
            .repairs-list {
                background: #e8f5e9;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
            }
            .repairs-list li {
                color: #2e7d32;
                list-style: none;
                padding: 5px 0;
            }
            .error {
                background: #ffebee;
                color: #c62828;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
            }
            .examples {
                margin-bottom: 15px;
            }
            .example-btn {
                background: #e9ecef;
                color: #333;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
                margin: 5px;
                cursor: pointer;
                font-size: 0.9em;
                transition: background 0.2s;
            }
            .example-btn:hover {
                background: #dee2e6;
                transform: none;
                box-shadow: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Software Compiler</h1>
            <p class="subtitle">Enter a natural language description of the app you want to build</p>
            
            <div class="examples">
                <button class="example-btn" onclick="loadExample('Build a CRM with login, contacts, dashboard, and role-based access')">CRM</button>
                <button class="example-btn" onclick="loadExample('Build an e-commerce store with products, cart, and checkout')">E-Commerce</button>
                <button class="example-btn" onclick="loadExample('Build a task management app with teams and deadlines')">Task Manager</button>
                <button class="example-btn" onclick="loadExample('Build a blog with posts, comments, and categories')">Blog</button>
            </div>
            
            <textarea id="prompt" placeholder="e.g., Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments">Build a CRM with login, contacts, dashboard, and role-based access</textarea>
            
            <button id="generateBtn" onclick="generate()">🚀 Generate Application</button>
            <div class="loading" id="loading">⏳ Generating... This may take 30-60 seconds.</div>
            
            <div class="result-container" id="resultContainer" style="display:none;">
                <h2>📊 Generation Results</h2>
                
                <div class="stats" id="stats"></div>
                
                <div id="repairsContainer"></div>
                <div id="errorContainer"></div>
                
                <h3>📄 Generated Configuration (JSON)</h3>
                <pre id="output">Loading...</pre>
            </div>
        </div>

        <script>
            async function generate() {
                const prompt = document.getElementById('prompt').value;
                if (!prompt.trim()) {
                    alert('Please enter a prompt!');
                    return;
                }
                
                const btn = document.getElementById('generateBtn');
                const loading = document.getElementById('loading');
                const resultContainer = document.getElementById('resultContainer');
                
                btn.disabled = true;
                loading.classList.add('active');
                resultContainer.style.display = 'none';
                
                try {
                    const response = await fetch('/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    
                    const data = await response.json();
                    
                    // Show results
                    resultContainer.style.display = 'block';
                    displayResults(data);
                    
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    btn.disabled = false;
                    loading.classList.remove('active');
                }
            }
            
            function displayResults(data) {
                const statsDiv = document.getElementById('stats');
                const repairsDiv = document.getElementById('repairsContainer');
                const errorDiv = document.getElementById('errorContainer');
                const outputPre = document.getElementById('output');
                
                // Stats
                const success = data.success;
                statsDiv.innerHTML = `
                    <div class="stat-card ${success ? 'success' : 'fail'}">
                        <div class="value">${success ? '✅' : '❌'}</div>
                        <div class="label">Status</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${data.latency ? data.latency.toFixed(2) : 'N/A'}s</div>
                        <div class="label">Latency</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${data.repairs ? data.repairs.length : 0}</div>
                        <div class="label">Repairs Made</div>
                    </div>
                    <div class="stat-card ${data.runtime_result && data.runtime_result.passed ? 'success' : 'fail'}">
                        <div class="value">${data.runtime_result && data.runtime_result.passed ? '✅' : '❌'}</div>
                        <div class="label">Runtime Validation</div>
                    </div>
                `;
                
                // Repairs
                if (data.repairs && data.repairs.length > 0) {
                    repairsDiv.innerHTML = `
                        <h4>🔧 Repairs Made (${data.repairs.length})</h4>
                        <ul class="repairs-list">
                            ${data.repairs.map(r => `<li>🔧 ${r}</li>`).join('')}
                        </ul>
                    `;
                } else {
                    repairsDiv.innerHTML = `<div class="repairs-list">✅ No repairs needed</div>`;
                }
                
                // Error
                if (data.error) {
                    errorDiv.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                } else {
                    errorDiv.innerHTML = '';
                }
                
                // JSON Output
                const config = data.config;
                if (config) {
                    outputPre.textContent = JSON.stringify(config, null, 2);
                } else {
                    outputPre.textContent = 'No configuration generated.';
                }
            }
            
            function loadExample(text) {
                document.getElementById('prompt').value = text;
                document.getElementById('resultContainer').style.display = 'none';
            }
        </script>
    </body>
    </html>
    """

@app.post("/generate")
async def generate(request: PromptRequest):
    start_time = time.time()
    try:
        # Stage 1: Intent
        intent = extract_intent(request.prompt)
        
        # Stage 2: Design
        design = design_system(intent)
        
        # Stage 3: Generate schemas
        schemas = generate_all_schemas(design)
        
        db = schemas['db']
        api = schemas['api']
        ui = schemas['ui']
        auth = schemas['auth']
        
        # Stage 4: Repair
        repaired_db, repaired_api, repaired_ui, repaired_auth, repairs = validate_and_repair(
            db, api, ui, auth
        )
        
        # Stage 5: Runtime validation
        runtime_result = validate_config(repaired_db, repaired_api, repaired_ui, repaired_auth)
        
        # Build final config
        config = {
            "db": repaired_db,
            "api": repaired_api,
            "ui": repaired_ui,
            "auth": repaired_auth
        }
        
        latency = time.time() - start_time
        
        return {
            "success": runtime_result['passed'],
            "config": config,
            "repairs": repairs,
            "runtime_result": runtime_result,
            "latency": latency,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "config": None,
            "repairs": [],
            "runtime_result": None,
            "latency": time.time() - start_time,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)