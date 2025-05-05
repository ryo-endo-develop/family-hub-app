```mermaid
erDiagram
erDiagram
    families {
        BIGINT id PK
        VARCHAR family_name NOT NULL
        TIMESTAMP created_at NOT NULL
        TIMESTAMP updated_at NOT NULL
    }

    users {
        BIGINT id PK
        VARCHAR oidc_subject NOT NULL UK
        VARCHAR email UK
        VARCHAR name
        VARCHAR avatar_url
        TIMESTAMP created_at NOT NULL
        TIMESTAMP updated_at NOT NULL
    }

    family_memberships {
        BIGINT id PK
        BIGINT user_id FK
        BIGINT family_id FK
        ENUM role NOT NULL
        TIMESTAMP joined_at NOT NULL
    }

    labels {
        BIGINT id PK
        BIGINT family_id FK
        VARCHAR name NOT NULL
        VARCHAR color
        BIGINT created_by_id FK
        BIGINT updated_by_id FK
        TIMESTAMP created_at NOT NULL
        TIMESTAMP updated_at NOT NULL
    }

    tasks {
        BIGINT id PK
        BIGINT family_id FK
        VARCHAR title NOT NULL
        BOOLEAN is_done NOT NULL DEFAULT FALSE
        ENUM task_type NOT NULL
        DATE due_date
        DATE next_occurrence_date
        JSON routine_settings
        BIGINT assignee_id FK
        TEXT notes
        TINYINT priority
        BIGINT parent_task_id FK
        BIGINT created_by_id FK
        BIGINT updated_by_id FK
        TIMESTAMP created_at NOT NULL
        TIMESTAMP updated_at NOT NULL
    }

    task_labels {
        BIGINT task_id PK
        BIGINT label_id PK
    }

    families           ||--o{ family_memberships : "FK: family_id"
    users              ||--o{ family_memberships : "FK: user_id"
    families           ||--o{ labels           : "FK: family_id"
    families           ||--o{ tasks            : "FK: family_id"
    users              ||--o{ labels           : "FK: created_by_id (nullable)"
    users              ||--o{ labels           : "FK: updated_by_id (nullable)"
    users              ||--o{ tasks            : "FK: assignee_id (nullable)"
    users              ||--o{ tasks            : "FK: created_by_id (nullable)"
    users              ||--o{ tasks            : "FK: updated_by_id (nullable)"
    tasks              ||--o{ tasks            : "FK: parent_task_id (nullable)"
    tasks              }o--o{ labels           : "via task_labels"

```
