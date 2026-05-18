"""initial schema

Revision ID: 2da9689fd84b
Revises: 767028e21fbb
Create Date: 2026-05-04 00:00:00.000000

"""

from typing import Sequence, Union

revision: str = "2da9689fd84b"
down_revision: Union[str, None] = "767028e21fbb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
