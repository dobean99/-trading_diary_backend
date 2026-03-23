"""create users table

Revision ID: 202603200001
Revises: 202603190001
Create Date: 2026-03-20 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202603200001"
down_revision: Union[str, Sequence[str], None] = "202603190001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.execute(
        """
        INSERT INTO users (id, username, password_hash, is_active, created_at, updated_at)
        VALUES (
          '00000000-0000-0000-0000-000000000001',
          'admin',
          'pbkdf2_sha256$390000$ZEu-af3zQd2zFEACBifvjg==$NIye_0CuGJ5agGNkrGK2lHVxc5nV9V9KIHxgokFEcZs=',
          true,
          NOW(),
          NOW()
        )
        ON CONFLICT (username) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
