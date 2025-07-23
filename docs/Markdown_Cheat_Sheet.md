# Markdown Cheat Sheet

Markdown is a lightweight markup language that lets you format text using plain text syntax. Perfect for writing documentation, notes, and articles with simple formatting that converts to beautiful HTML.

## Text Formatting

### Basic Emphasis
```markdown
*italic text* or _italic text_
**bold text** or __bold text__
***bold and italic*** or ___bold and italic___
~~strikethrough text~~
```

### Headings
```markdown
# Heading 1 (Main Title)
## Heading 2 (Section)
### Heading 3 (Subsection)
#### Heading 4 (Sub-subsection)
##### Heading 5 (Minor heading)
###### Heading 6 (Smallest heading)
```

**Tip:** Use only one H1 per document. Structure your content hierarchically.

## Lists and Organization

### Unordered Lists
```markdown
- First item
- Second item
  - Nested item
  - Another nested item
    - Deeply nested item
- Back to main level

* You can also use asterisks
+ Or plus signs
```

### Ordered Lists
```markdown
1. First step
2. Second step
   1. Sub-step A
   2. Sub-step B
3. Third step

Note: Numbers don't have to be sequential - Markdown will renumber them.
```

### Task Lists (GitHub-flavored)
```markdown
- [x] Completed task
- [ ] Incomplete task
- [x] ~~Cancelled task~~ (crossed out)
```

## Links and References

### Basic Links
```markdown
[Link text](https://example.com)
[Link with title](https://example.com "Hover title")
```

### Reference Links
```markdown
Check out [Google][1] and [GitHub][github-link].

[1]: https://google.com
[github-link]: https://github.com "GitHub Homepage"
```

### Automatic Links
```markdown
<https://example.com>
<email@example.com>
```

## Images and Media

### Basic Images
```markdown
![Alt text](image.jpg)
![Alt text with title](image.jpg "Image title")
```

### Reference Images
```markdown
![Alt text][image-ref]

[image-ref]: path/to/image.jpg "Optional title"
```

## Code and Syntax

### Inline Code
```markdown
Use `backticks` for inline code or `variable names`.
```

### Code Blocks
````markdown
```
Basic code block
```

```python
# Syntax highlighted code block
def hello_world():
    print("Hello, World!")
```

```javascript
// JavaScript example
function greet(name) {
    return `Hello, ${name}!`;
}
```
````

## Quotes and Callouts

### Blockquotes
```markdown
> This is a blockquote.
> It can span multiple lines.
>
> > Nested blockquotes are possible.
>
> Back to single level.
```

### Multi-line Quotes
```markdown
> "The best way to get started is to quit talking
> and begin doing."
>
> — Walt Disney
```

## Tables

### Basic Table
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data     | More     |
| Row 2    | Data     | More     |
```

### Aligned Tables
```markdown
| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Left         | Center         | Right         |
| Text         | Text           | Text          |
```

## Separators and Structure

### Horizontal Rules
```markdown
---
***
___
```

### Line Breaks
```markdown
Two spaces at end of line  
creates a line break.

Or use a blank line for paragraph breaks.
```

## Advanced Features

### Escape Characters
```markdown
Use backslash to escape special characters:
\*Not italic\* \[Not a link\]
```

### HTML in Markdown
```markdown
You can use <em>HTML tags</em> when needed.
<br>
<details>
<summary>Collapsible section</summary>
Hidden content here.
</details>
```

### Footnotes (some flavors)
```markdown
Here's a sentence with a footnote[^1].

[^1]: This is the footnote content.
```

## Writing Tips

- **Keep it simple**: Markdown shines with clean, readable formatting
- **Use consistent spacing**: Be consistent with your list spacing and indentation
- **Preview often**: Check how your markdown renders, especially tables and code blocks
- **Structure matters**: Use headings to create a clear document hierarchy
- **Less is more**: Don't over-format; let content speak for itself

## Quick Reference Summary

| Element | Syntax |
|---------|--------|
| Heading | `# H1` `## H2` `### H3` |
| Bold | `**bold**` |
| Italic | `*italic*` |
| Link | `[text](URL)` |
| Image | `![alt](image.jpg)` |
| Code | `` `code` `` |
| List | `- item` or `1. item` |
| Quote | `> quote` |
| Rule | `---` |

Happy writing with Markdown! 🚀
