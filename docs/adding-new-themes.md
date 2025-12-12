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
    MY_NEW_THEME = "my_new_theme" # Add this line
```

### 2.2. Map File

Open `src/Backend/src/api/adapters/google/generative_ai.py` and update the `THEMES_DICT` to map the enum to your text file.

```python
THEMES_DICT = {
    # ... existing mappings
    models.QuestionTheme.MY_NEW_THEME: "my_new_theme.txt", # Add this line
}
```

## Step 3: Create Database Migration

Since `QuestionTheme` is a database ENUM, you must create a migration to update the database schema.

1.  **Generate Migration**: Run `alembic revision -m "add_my_new_theme"`
2.  **Edit Migration File**: Update the `upgrade` function to recreate the ENUM type.

```python
def upgrade() -> None:
    # 1. Rename the existing type
    op.execute("ALTER TYPE questiontheme RENAME TO questiontheme_old")

    # 2. Create the new type with the added value
    op.execute("""
        CREATE TYPE questiontheme AS ENUM(
            'EXISTING_THEME_1',
            'EXISTING_THEME_2',
            'MY_NEW_THEME' -- Add your new theme here
        )
    """)

    # 3. Update the column to use the new type
    op.execute("""
        ALTER TABLE questions 
        ALTER COLUMN theme TYPE questiontheme 
        USING theme::text::questiontheme
    """)

    # 4. Drop the old type
    op.execute("DROP TYPE questiontheme_old")

def downgrade() -> None:
    # Logic to revert the changes (remove the new theme)
    op.execute("ALTER TYPE questiontheme RENAME TO questiontheme_old")
    
    op.execute("""
        CREATE TYPE questiontheme AS ENUM(
            'EXISTING_THEME_1',
            'EXISTING_THEME_2'
        )
    """)

    op.execute("""
        ALTER TABLE questions 
        ALTER COLUMN theme TYPE questiontheme 
        USING theme::text::questiontheme
    """)

    op.execute("DROP TYPE questiontheme_old")
```

## Step 4: Update Frontend Code

You need to expose the new theme in the frontend so users can select it.

### 4.1. Update Enum

Open `src/Frontend/src/constants/enums.ts` and add the new theme to the `QuestionTheme` enum.

```typescript
export enum QuestionTheme {
    // ... existing themes
    MyNewTheme = "my_new_theme", // Add this line (value must match Backend enum)
}
```

### 4.2. Update Translations

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
- [ ] **Database**: Migration created and applied to update `questiontheme` ENUM.
- [ ] **Frontend**: `QuestionTheme` enum updated in `enums.ts`.
- [ ] **Frontend**: Translation files (`form.json`) updated with the new key.
