"""rename token_hash to otp_code in password_reset_tokens

Revision ID: b20a6b8089d4
Revises: 2da9689fd84b
Create Date: 2026-05-04 20:57:57.651731

"""

from typing import Sequence, Union

from alembic import op

revision: str = "b20a6b8089d4"
down_revision: Union[str, Sequence[str], None] = "2da9689fd84b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM password_reset_tokens")
    op.alter_column("password_reset_tokens", "token_hash", new_column_name="otp_code")


def downgrade() -> None:
    op.execute("DELETE FROM password_reset_tokens")
    op.alter_column("password_reset_tokens", "otp_code", new_column_name="token_hash")
