# LLM Runbook for PyTug CLI

This document guides an LLM on how to use the `pytug` CLI tool for various Python code refactoring tasks. `pytug` leverages advanced code analysis to perform safe and precise modifications.

## Introduction to PyTug

`pytug` is a command-line interface (CLI) tool designed to perform automated refactorings on Python codebases. It uses either the `rope` library or `LibCST` internally to understand and transform code, ensuring that changes are semantically correct and maintain code quality.

## General Usage for LLMs

When instructed to perform a refactoring task, you should use the `run_shell_command` tool to execute `pytug` commands. Always ensure you are in the correct project directory.

The general command structure is:
`pytug refactor <command> [arguments]`

Before executing any refactoring command, it is crucial to:
1.  **Understand the Request:** Clearly identify the refactoring type, target file, symbol names, line/column numbers, and any other relevant parameters.
2.  **Read Relevant Code:** Use `read_file` to inspect the target file and surrounding code to confirm the context and exact details (e.g., current function signature, variable names, indentation).
3.  **Formulate the Command:** Construct the `pytug` command with the correct subcommand and arguments.
4.  **Verify (Optional but Recommended):** After executing a refactoring, you can use `read_file` again to verify that the changes were applied as expected.

## Refactoring Commands and Prompts

Here are specific instructions and example prompts for each `pytug` refactoring command.

### 1. Rename Symbol

**Description:** Renames a Python symbol (variable, function, class, etc.) at a specific location.

**`pytug` Command:**
`pytug refactor rename-symbol <file_path> <old_name> <new_name> --line <line> --column <column>`

**LLM Prompt Example:**
"Rename the variable `old_var` to `new_var` in `src/my_module.py` at line 10, column 5."

**LLM Action:**
1.  Read `src/my_module.py` to confirm `old_var` at the specified location.
2.  Execute:
    ```bash
    pytug refactor rename-symbol src/my_module.py old_var new_var --line 10 --column 5
    ```

### 2. Extract Method

**Description:** Extracts a block of code into a new method or function.

**`pytug` Command:**
pytug refactor extract-method <file_path> <new_method_name> --start-line <start_line> --end-line <end_line>`

**LLM Prompt Example:**
"Extract lines 15 to 20 into a new method named `_calculate_total` in `src/calculator.py`."

**LLM Action:**
1.  Read `src/calculator.py` to confirm the code block.
2.  Execute:
    ```bash
    pytug refactor extract-method src/calculator.py _calculate_total --start-line 15 --end-line 20
    ```

### 3. Inline Variable

**Description:** Replaces all occurrences of a variable with its assigned value.

**`pytug` Command:**
`pytug refactor inline-variable <file_path> <variable_name> --line <line> --column <column>`

**LLM Prompt Example:**
"Inline the variable `TAX_RATE` in `src/constants.py` defined at line 5, column 1."

**LLM Action:**
1.  Read `src/constants.py` to confirm `TAX_RATE` and its value.
2.  Execute:
    ```bash
    pytug refactor inline-variable src/constants.py TAX_RATE --line 5 --column 1
    ```

### 4. Change Signature

**Description:** Changes the signature of a function or method, including renaming, adding, removing, or reordering parameters, and modifying default values.

**`pytug` Command:**
`pytug refactor change-signature <file_path> <function_name> <old_signature> <new_signature>`

**LLM Prompt Example:**
"Change the signature of the `process_data` function in `src/data_processor.py`. The current signature is `(self, data, config=None)`, and the new signature should be `(self, new_data, options, timeout=10)`."

**LLM Action:**
1.  Read `src/data_processor.py` to confirm the function and its current signature.
2.  Execute:
    ```bash
    pytug refactor change-signature src/data_processor.py process_data "self, data, config=None" "self, new_data, options, timeout=10"
    ```
    *Note: Be careful with escaping quotes in `old_signature` and `new_signature` if they contain default values with strings.*

### 5. Remove Function or Class

**Description:** Removes a function or class definition from a file.

**`pytug` Command:**
`pytug refactor remove-function-or-class <file_path> <name>`

**LLM Prompt Example:**
"Remove the `cleanup_old_logs` function from `src/utils.py`."

**LLM Action:**
1.  Read `src/utils.py` to confirm the function's existence.
2.  Execute:
    ```bash
    pytug refactor remove-function-or-class src/utils.py cleanup_old_logs
    ```

### 6. Apply Formatting

**Description:** Applies standard Python formatting to an entire file using `ruff format`.

**`pytug` Command:**
pytug refactor apply-formatting <file_path>`

**LLM Prompt Example:**
"Format the file `src/unformatted_script.py`."

**LLM Action:**
1.  Execute:
    ```bash
    pytug refactor apply-formatting src/unformatted_script.py
    ```
