# ROPE-REQUIREMENTS.md: Plan for Helpful Rope Commands

This document outlines a plan for integrating `rope`-based commands to enhance the agent's ability to refactor and modify Python code, specifically addressing challenges encountered with large files, indentation, and precise string matching.

## Motivation

The current text-based `replace` tool is brittle when dealing with Python code due to its sensitivity to whitespace, indentation, and the need for exact string matches. This often leads to:
- Failed `replace` operations due to minor discrepancies.
- Difficulty in performing semantic code changes (e.g., renaming a variable across its scope).
- Increased cognitive load for the agent to meticulously craft `old_string` and `new_string` with extensive context.
- Risk of introducing `IndentationError`s or other syntax issues.

Leveraging a Python refactoring library like `rope` (or similar AST-aware tools) would allow the agent to operate on the code's Abstract Syntax Tree (AST), enabling more robust, semantic, and reliable code modifications.

## Proposed Helpful Rope Commands (Conceptual)

The following are conceptual commands, outlining the desired functionality rather than exact API specifications.

### 1. `refactor_rename_symbol`

**Description:** Renames a Python symbol (variable, function, class, method, argument) across its defined scope(s). This command would understand the scope of the symbol and apply changes consistently.

**Use Case:**
- Renaming a local variable.
- Renaming a function or method.
- Renaming a class.
- Renaming an argument in a function definition and all its call sites.

**Conceptual API:**
```python
default_api.refactor_rename_symbol(
    file_path: str,            # Path to the file containing the symbol definition
    old_name: str,             # Current name of the symbol
    new_name: str,             # Desired new name for the symbol
    line: int = None,          # Optional: Line number where the symbol is defined (for disambiguation)
    column: int = None,        # Optional: Column number where the symbol is defined (for disambiguation)
    scope: str = "global"      # Optional: Scope of the rename (e.g., "global", "function_name", "class_name")
)
```

### 2. `refactor_extract_method`

**Description:** Extracts a block of selected lines into a new method or function. This command would handle parameter passing, return values, and correct indentation automatically.

**Use Case:**
- Reducing complexity in a large function.
- Creating reusable code blocks.

**Conceptual API:**
```python
default_api.refactor_extract_method(
    file_path: str,            # Path to the file
    start_line: int,           # Starting line of the code block to extract
    end_line: int,             # Ending line of the code block to extract
    new_method_name: str,      # Name for the new method/function
    target_class: str = None,  # Optional: If extracting to a method within a class
    target_function: str = None # Optional: If extracting to a nested function
)
```

### 3. `refactor_inline_variable`

**Description:** Replaces all occurrences of a variable with its assigned value, effectively removing the variable definition.

**Use Case:**
- Simplifying code where a variable is used only once or its value is trivial.

**Conceptual API:**
```python
default_api.refactor_inline_variable(
    file_path: str,            # Path to the file
    variable_name: str,        # Name of the variable to inline
    line: int,                 # Line number where the variable is defined
    column: int                # Column number where the variable is defined
)
```

### 4. `refactor_change_signature`

**Description:** Modifies the signature of a function or method, allowing for adding, removing, reordering, or renaming parameters. This would update all call sites.

**Use Case:**
- Adapting API changes.
- Improving function clarity.

**Conceptual API:**
```python
default_api.refactor_change_signature(
    file_path: str,            # Path to the file
    function_name: str,        # Name of the function/method
    old_signature: str,        # Original signature (e.g., "func(a, b=1)")
    new_signature: str         # Desired new signature (e.g., "func(b, c, a=0)")
)
```

### 5. `refactor_remove_function_or_class`

**Description:** Removes a specified function or class definition, including its docstrings and comments, and optionally removes its call sites or references.

**Use Case:**
- Deleting deprecated or unused code.
- Cleaning up refactored code.

**Conceptual API:**
```python
default_api.refactor_remove_function_or_class(
    file_path: str,            # Path to the file
    name: str,                 # Name of the function or class to remove
    remove_references: bool = False # Optional: Whether to remove all call sites/references
)
```

### 6. `refactor_apply_formatting`

**Description:** Applies standard Python formatting (e.g., Black, Ruff Format) to a specified file or code block.

**Use Case:**
- Ensuring code style consistency.
- Fixing indentation issues.

**Conceptual API:**
```python
default_api.refactor_apply_formatting(
    file_path: str,            # Path to the file
    start_line: int = None,    # Optional: Start line for formatting a block
    end_line: int = None       # Optional: End line for formatting a block
)
```

## Benefits

-   **Increased Reliability:** Operations are performed semantically, reducing the risk of syntax errors or unintended changes.
-   **Higher-Level Abstraction:** The agent can express intent more clearly, rather than focusing on low-level text manipulation.
-   **Improved Efficiency:** Complex refactoring tasks can be accomplished with a single command, rather than multiple brittle `replace` calls.
-   **Better Maintainability:** Code changes are more robust and less likely to break with minor code variations.

This set of `rope`-based commands would significantly improve the agent's ability to interact with and modify Python codebases effectively and safely.
