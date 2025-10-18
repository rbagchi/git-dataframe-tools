# GIT-SCOREBOARD: Your Performance Review Secret Weapon (or How to Look Busy)

Feeling undervalued? Need to justify that raise? Or perhaps you just want to subtly (or not-so-subtly) remind your manager of your unparalleled contributions? Look no further than `git-scoreboard`!

This isn't just a tool; it's your personal data-driven narrative generator for performance reviews. Forget subjective opinions; we've got numbers!

## Step 1: Generate Your Personal Scoreboard

First, navigate to your most impactful (or at least, most active) repository. Then, unleash the power of `git-scoreboard` to quantify your brilliance.

```bash
git-scoreboard . --since "6 months ago" --me --format markdown
```

**Explanation:**
*   `.`: Analyze the current repository. Because, obviously, that's where all the magic happens.
*   `--since "6 months ago"`: Focus on recent, relevant contributions. Anything older is ancient history, right?
*   `--me`: Crucially, filter *only* for your own commits. We're not here to highlight team effort, are we?
*   `--format markdown`: Because a nicely formatted table looks far more professional than raw text when you're pasting it into a document.

## Step 2: Interpret Your Metrics (with a healthy dose of self-aggrandizement)

Let's say your output looks something like this:

```
| Author Name | Author Email | Added | Deleted | Total | Commits | Rank | Diff Decile | Commit Decile |
|:------------|:-------------|------:|--------:|------:|--------:|-----:|------------:|--------------:|
| Your Name   | you@comp.com | 5000  | 1000    | 6000  | 150     | 1    | 1           | 1             |
```

**How to spin this for your review:**

*   **`Added: 5000`**: "As you can see, my commitment to expanding our codebase and delivering new features is consistently high. That's 5,000 lines of pure innovation, right there."
*   **`Deleted: 1000`**: "My dedication to code quality and refactoring is evident in the 1,000 lines I've meticulously removed, ensuring a lean, efficient, and maintainable product. It's not just about adding; it's about *improving*."
*   **`Total: 6000`**: "My overall impact on the codebase is substantial, reflecting my broad engagement across critical areas of the project."
*   **`Commits: 150`**: "My consistent and frequent contributions demonstrate a proactive approach to development and a steady delivery of value."
*   **`Rank: 1`**: "I consistently lead the team in overall code contributions, a testament to my productivity and influence."
*   **`Diff Decile: 1`**: "I am consistently in the top 10% of contributors by code change volume, indicating my significant role in driving project momentum."
*   **`Commit Decile: 1`**: "My commit frequency places me in the top 10% of contributors, showcasing my sustained engagement and rapid iteration cycles."

## A Word of Caution: The Flaws of Metrics

While `git-scoreboard` provides fascinating numbers, it's crucial to remember the inherent limitations of quantitative metrics, especially in complex domains like software development. As Peter Drucker famously said, "What gets measured gets managed." This is both a strength and a weakness.

**Be aware:**
*   **Context is King:** Lines of code, commit counts, and even deciles don't tell the full story of impact, quality, or problem-solving. A single, well-placed line of code can be more valuable than thousands of trivial ones.
*   **Easily Manipulated:** These scores can be trivially manipulated. Adding and deleting whitespace, committing frequently with small changes, or even generating code can inflate metrics without increasing actual value.
*   **Focus on Insight, Not Judgment:** Use these metrics as a starting point for discussion and insight, not as definitive judgments of performance. The goal is to understand patterns, not to create a leaderboard for its own sake.

Use these tools wisely, and always prioritize genuine contribution over metric manipulation.

## Step 3: Strategically Deploy Your Data

Paste these glorious metrics directly into your performance review document. Highlight them. Bold them. Perhaps even add a subtle footnote about the objectivity of data-driven insights.

Remember, numbers don't lie (especially when you've carefully selected which numbers to present). Go forth and conquer that performance review!
