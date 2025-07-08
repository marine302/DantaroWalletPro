"""merge_sweep_and_doc27_heads

Revision ID: ca0829d8a731
Revises: doc27_002, sweep_001
Create Date: 2025-07-08 19:36:57.502724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca0829d8a731'
down_revision: Union[str, None] = ('doc27_002', 'sweep_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
