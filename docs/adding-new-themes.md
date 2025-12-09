# Adding New Themes (PDFs) for Embeddings

This document outlines the steps required to add a new theme (based on a PDF/Text content) to the application. This allows the backend to generate questions based on specific industry knowledge.

## Overview

The process involves:
1.  **Backend**: Adding the content file and updating the code to recognize the new theme.
2.  **Frontend**: Updating the code to allow users to select the new theme in the UI.

## Step 1: Prepare Content (Backend)

The backend uses text files (`.txt`) to generate embeddings. If you have a PDF, you must first convert its content to a plain text file.

1.  **Convert PDF to Text**: Extract the text from your PDF and save it as a `.txt` file (e.g., `my_new_theme.txt`).
2.  **Add File**: Place the file in the following directory:
    `src/Backend/src/api/adapters/google/themes/`

## Step 2: Update Backend Code

You need to register the new theme in the backend.

### 2.1. Update Enum

Open `src/Backend/src/api/models/exams.py` and add the new theme to the `QuestionTheme` class.

```python
class QuestionTheme(enum.StrEnum):
    # ... existing themes
    MY_NEW_THEME = "MY_NEW_THEME"  # Add this line (use UPPERCASE for the value)
```

> **Important**: The enum value must be in UPPERCASE to match the enum member name. This ensures proper serialization with SQLAlchemy.

### 2.2. Map File

Open `src/Backend/src/api/adapters/google/generative_ai.py` and update the `THEMES_DICT` to map the enum to your text file.

```python
THEMES_DICT = {
    # ... existing mappings
    models.QuestionTheme.MY_NEW_THEME: "my_new_theme.txt", # Add this line
}
```

### 2.3. Create Database Migration

After updating the enum, you need to create a database migration to add the new value to the PostgreSQL enum type.

1. **Generate migration file**:
   ```bash
   cd src/Backend
   alembic revision -m "add_my_new_theme_to_questiontheme_enum"
   ```

2. **Edit the migration file** (located in `src/Backend/migrations/versions/`):

   ```python
   def upgrade() -> None:
       # Add new value to the questiontheme enum
       op.execute("ALTER TYPE questiontheme ADD VALUE 'MY_NEW_THEME'")

   def downgrade() -> None:
       # Note: PostgreSQL does not support removing enum values directly
       # You would need to recreate the enum type without the value
       pass
   ```

> **Important**: PostgreSQL does not allow removing enum values easily. The downgrade function is typically left empty or requires recreating the entire enum type.

## Step 3: Update Frontend Code

You need to expose the new theme in the frontend so users can select it.

### 3.1. Update Enum

Open `src/Frontend/src/constants/enums.ts` and add the new theme to the `QuestionTheme` enum.

```typescript
export enum QuestionTheme {
    // ... existing themes
    MyNewTheme = "MY_NEW_THEME", // Add this line (value must match Backend enum in UPPERCASE)
}
```

### 3.2. Update Translations

Update the translation files to provide a user-friendly name for the new theme. You need to update `form.json` for all supported languages (e.g., `pt-BR`, `en-US`, `es-ES`).

**File**: `src/Frontend/src/libs/i18n/languages/pt-BR/form.json` (and others)

```json
{
    "form": {
        "exam": {
            // ...
            "my_new_theme": "Nome do Meu Novo Tema", // Add this line
            // ...
        }
    }
}
```

## Summary Checklist

- [ ] **Backend**: `.txt` file added to `themes/` folder.
- [ ] **Backend**: `QuestionTheme` enum updated in `models/exams.py`.
- [ ] **Backend**: `THEMES_DICT` updated in `generative_ai.py`.
- [ ] **Backend**: Database migration created to add new enum value.
- [ ] **Frontend**: `QuestionTheme` enum updated in `enums.ts`.
- [ ] **Frontend**: Translation files (`form.json`) updated with the new key.
