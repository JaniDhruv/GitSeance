"""
🔮 GitSéance Model Context Protocol (MCP) Server

Exposes GitSéance's multi-agent code necromancy tools to any MCP-compliant
AI client (Cursor, Claude Desktop, Antigravity, GitHub Copilot).

Tools Exposed:
1. tabpfn_predict_mortality: Prior Labs TabPFN-3.5 7D tabular Bayesian mortality prediction
2. reaper_scan_graveyard: AST & blame scan for dead code
3. gemma_channel_ghost: Developer ghost channeling & revival patch generator
4. searcher_modernize_deps: 2026 dependency intelligence via SerpApi
"""

import sys
import json
import asyncio
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.oracle import OracleAgent
from agents.reaper import ReaperAgent
from agents.medium import MediumAgent
from agents.searcher import SearcherAgent
from services.tabpfn_client import TabPFNClient

# Global agent instances
oracle = OracleAgent()
reaper = ReaperAgent()
medium = MediumAgent()
searcher = SearcherAgent()
tabpfn = TabPFNClient()

TOOLS = [
    {
        "name": "tabpfn_predict_mortality",
        "description": "Calculates Bayesian code mortality risk using Prior Labs TabPFN-3.5 foundation model on a 7-dimensional forensic feature vector.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path of the file being evaluated"},
                "days_since_last_commit": {"type": "integer", "description": "Number of days since last commit"},
                "total_commits": {"type": "integer", "description": "Total commits touching this file"},
                "unique_authors": {"type": "integer", "description": "Number of unique authors in git blame"},
                "bug_fix_commit_ratio": {"type": "number", "description": "Ratio of bug-fix commits (0.0 to 1.0)"},
                "lines_ratio": {"type": "number", "description": "Lines added / (lines deleted + 1)"},
                "has_tests": {"type": "boolean", "description": "Whether the file has accompanying unit tests"},
                "churn_velocity": {"type": "number", "description": "Average commits per month"}
            },
            "required": ["days_since_last_commit", "total_commits", "unique_authors"]
        }
    },
    {
        "name": "reaper_scan_graveyard",
        "description": "Scans a GitHub repository for abandoned, dead, orphaned, or cursed code files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "GitHub repository URL (e.g. https://github.com/mitsuhiko/flask-cache)"}
            },
            "required": ["repo_url"]
        }
    },
    {
        "name": "gemma_channel_ghost",
        "description": "Channels the spirit of a file's original developer via Google Gemma to explain bygone architectural decisions and output a modernization blueprint.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "GitHub repository URL"},
                "file_path": {"type": "string", "description": "Path to the file to commune with"}
            },
            "required": ["repo_url", "file_path"]
        }
    },
    {
        "name": "searcher_modernize_deps",
        "description": "Queries live 2026 package registries via SerpApi to find drop-in replacements for abandoned libraries and audit CVE security advisories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "GitHub repository URL"},
                "dead_packages": {"type": "array", "items": {"type": "string"}, "description": "Optional list of package names to replace"}
            },
            "required": ["repo_url"]
        }
    }
]


async def handle_call_tool(name: str, arguments: dict) -> dict:
    """Execute the requested tool and return content."""
    try:
        if name == "tabpfn_predict_mortality":
            feature_vector = [{
                "file_path": arguments.get("file_path", "target_file.py"),
                "days_since_last_commit": int(arguments.get("days_since_last_commit", 365)),
                "total_commits": int(arguments.get("total_commits", 10)),
                "unique_authors": int(arguments.get("unique_authors", 1)),
                "bug_fix_commit_ratio": float(arguments.get("bug_fix_commit_ratio", 0.3)),
                "lines_ratio": float(arguments.get("lines_ratio", 1.2)),
                "has_tests": 1 if arguments.get("has_tests", False) else 0,
                "churn_velocity": float(arguments.get("churn_velocity", 0.05)),
            }]
            predictions = await tabpfn.predict_mortality(feature_vector)
            pred = predictions[0] if predictions else {"mortality_risk": 0.5, "confidence": 0.5}
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "model": "TabPFN-3.5 Bayesian Tabular Foundation Model",
                        "mortality_risk": pred.get("mortality_risk"),
                        "risk_percentage": f"{int(round(pred.get('mortality_risk', 0.5) * 100))}%",
                        "confidence": pred.get("confidence"),
                        "classification": "CRITICAL RISK" if pred.get("mortality_risk", 0) >= 0.75 else "MODERATE RISK"
                    }, indent=2)
                }]
            }

        elif name == "reaper_scan_graveyard":
            repo_url = arguments["repo_url"]
            reports = await reaper.scan_repository(repo_url)
            summary = [
                {
                    "file_path": r.file_path,
                    "status": r.status.value,
                    "ghost_score": r.ghost_score,
                    "days_inactive": r.metrics.days_since_last_commit,
                    "author": r.metrics.last_author,
                    "warnings": r.warnings
                }
                for r in reports[:15]
            ]
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({"total_scanned": len(reports), "graveyard_preview": summary}, indent=2)
                }]
            }

        elif name == "gemma_channel_ghost":
            repo_url = arguments["repo_url"]
            file_path = arguments["file_path"]
            channeling = await medium.channel_file(repo_url, file_path)
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(channeling.model_dump(), indent=2)
                }]
            }

        elif name == "searcher_modernize_deps":
            repo_url = arguments["repo_url"]
            dead_packages = arguments.get("dead_packages")
            replacements = await searcher.find_replacements(repo_url, dead_packages)
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps([r.model_dump() for r in replacements], indent=2)
                }]
            }

        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}]
            }

    except Exception as e:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error executing tool {name}: {str(e)}"}]
        }


def main():
    """Main JSON-RPC stdio event loop."""
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue

        try:
            req = json.loads(line_str)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "gitseance-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS}
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            result = asyncio.run(handle_call_tool(tool_name, tool_args))
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()

        else:
            if req_id is not None:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
