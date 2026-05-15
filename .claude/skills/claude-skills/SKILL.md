```markdown
# claude-skills Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill provides guidance on contributing to the `claude-skills` TypeScript codebase. It covers coding conventions, file organization, commit patterns, and common workflows such as adding and integrating image assets into HTML files. The repository favors clarity, consistency, and maintainability, making it easy for contributors to follow established patterns.

## Coding Conventions

### File Naming
- **Style:** kebab-case
- **Example:**  
  ```
  user-profile.ts
  image-handler.test.ts
  ```

### Import Style
- **Relative imports** are used for referencing local modules.
- **Example:**
  ```typescript
  import { processImage } from './image-utils';
  ```

### Export Style
- **Named exports** are preferred.
- **Example:**
  ```typescript
  // image-utils.ts
  export function processImage(img: HTMLImageElement): void { ... }
  ```

### Commit Messages
- **Conventional Commits** are used, with the `feat` prefix for new features.
- **Example:**
  ```
  feat: add support for local image asset integration in HTML
  ```

## Workflows

### Add and Integrate Image Assets
**Trigger:** When someone wants to introduce new image assets and ensure they are used in the website's HTML.  
**Command:** `/add-asset-and-update-html`

1. **Add new image files**  
   Place your new `.jpg` images into the `temp-assets/ymk-backgrounds/` directory.
   ```
   temp-assets/ymk-backgrounds/my-new-background.jpg
   ```
2. **Update HTML references**  
   Open the relevant HTML files (e.g., `ymkfinal1.html`) and update `<img>` or CSS `background-image` references to use the new local image paths:
   ```html
   <!-- Before -->
   <img src="https://external.site/background.jpg" alt="Background">

   <!-- After -->
   <img src="temp-assets/ymk-backgrounds/my-new-background.jpg" alt="Background">
   ```
3. **Save and commit your changes**  
   Use a conventional commit message:
   ```
   feat: add my-new-background.jpg and update HTML references
   ```
4. **Test**  
   Open the HTML file in your browser to confirm the new image displays correctly.

## Testing Patterns

- **Test File Naming:**  
  Test files follow the `*.test.*` pattern, e.g., `image-utils.test.ts`.
- **Testing Framework:**  
  Not explicitly specified in the repository.  
- **Example Test File:**
  ```typescript
  // image-utils.test.ts
  import { processImage } from './image-utils';

  test('processImage applies correct filter', () => {
    // ...test implementation
  });
  ```

## Commands

| Command                     | Purpose                                                        |
|-----------------------------|----------------------------------------------------------------|
| /add-asset-and-update-html  | Add new image assets and update HTML files to use local images |
```
