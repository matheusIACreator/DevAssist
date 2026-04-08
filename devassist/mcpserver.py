"""
DevAssist MCP Server

Um servidor MCP que expõe ferramentas de developer productivity.
Pode ser conectado a qualquer cliente MCP (Claude Desktop, Cursor, etc.)
"""

from fastmcp import FastMCP

# Cria o server MCP
mcp = FastMCP(
    name="DevAssist Tools",
    instructions="Developer productivity tools: code analysis, snippets, and utilities.",
)


@mcp.tool()
def generate_gitignore(language: str) -> str:
    """
    Generate a .gitignore file for a given programming language or framework.

    Args:
        language: e.g. 'python', 'node', 'rust', 'java'
    """
    templates = {
        "python": """# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.venv/
venv/
env/
.env
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
""",
        "node": """# Node.js
node_modules/
.env
.env.local
dist/
build/
.next/
.cache/
*.log
npm-debug.log*
yarn-error.log*
""",
        "rust": """# Rust
/target/
Cargo.lock
**/*.rs.bk
*.pdb
""",
        "java": """# Java
*.class
*.jar
*.war
*.ear
target/
.gradle/
build/
.idea/
*.iml
""",
    }
    key = language.lower().strip()
    if key in templates:
        return templates[key]
    return f"# No template available for '{language}'. Visit gitignore.io for more."


@mcp.tool()
def explain_http_status(code: int) -> str:
    """
    Explain what an HTTP status code means.

    Args:
        code: HTTP status code, e.g. 404, 200, 500
    """
    codes = {
        200: "OK — Request succeeded.",
        201: "Created — Resource was created successfully.",
        204: "No Content — Request succeeded but no body returned.",
        301: "Moved Permanently — Resource has a new permanent URL.",
        302: "Found — Temporary redirect.",
        400: "Bad Request — Server couldn't understand the request.",
        401: "Unauthorized — Authentication required.",
        403: "Forbidden — Authenticated but not allowed.",
        404: "Not Found — Resource doesn't exist.",
        409: "Conflict — Request conflicts with current state.",
        422: "Unprocessable Entity — Validation error (common in FastAPI).",
        429: "Too Many Requests — Rate limit hit.",
        500: "Internal Server Error — Something crashed on the server.",
        502: "Bad Gateway — Upstream server returned an invalid response.",
        503: "Service Unavailable — Server is down or overloaded.",
    }
    explanation = codes.get(code)
    if explanation:
        return f"HTTP {code}: {explanation}"
    category = code // 100
    categories = {1: "Informational", 2: "Success", 3: "Redirection", 4: "Client Error", 5: "Server Error"}
    return f"HTTP {code}: {categories.get(category, 'Unknown')} response."


@mcp.tool()
def generate_readme_template(project_name: str, description: str, language: str) -> str:
    """
    Generate a basic README.md template for a project.

    Args:
        project_name: Name of the project
        description: Short description of what the project does
        language: Primary programming language
    """
    return f"""# {project_name}

    {description}

    ## Tech Stack

    - **Language:** {language}

    ## Getting Started

    ### Prerequisites

    - {language} installed
    - (Add other requirements here)

    ### Installation

    ```bash
    git clone https://github.com/yourusername/{project_name.lower().replace(" ", "-")}
    cd {project_name.lower().replace(" ", "-")}
    # install dependencies
    ```

    ### Usage

    ```bash
    # add usage example here
    ```

    ## Project Structure

    (Describe your project structure here)
"""
if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run(transport=transport)