# Codebase Analysis Rubric

This document outlines the rubric used to assess the `git-dataframe-tools` codebase.

## Scoring Metrics (out of 100)

*   **Modularity:** How well are concerns separated? Are components loosely coupled?
*   **Code Quality:** Is the code readable, consistent, and maintainable? Is it well-documented? Does it follow best practices?
*   **Testability:** How easy is it to write unit and integration tests for the code?
*   **Extensibility:** How easy is it to add new features or modify existing ones?
*   **Robustness:** How well does the code handle errors and edge cases?

## Effort Scale (1-5)

*   **1: Trivial:** A few lines of code, no major logic changes.
*   **2: Low:** A small, self-contained change.
*   **3: Medium:** Requires some refactoring and careful testing.
*   **4: High:** A significant refactoring or a new feature.
*   **5: Major:** A major architectural change or a rewrite of a core component.

## Development Process

For each task, the following iterative development process is used:

1.  **Detailed Steps:** The task is broken down into small, detailed, low-effort steps.
2.  **Test After Each Step:** After each step is completed, all unit tests are run to ensure that no regressions have been introduced.
3.  **Quality Checks:** At the conclusion of the entire task, `ruff` and `mypy` are run to ensure that the code adheres to quality standards.