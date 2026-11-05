"""initial schema"""
from alembic import op

from carradar.db.models import Base

revision = "0001"
down_revision = None


def upgrade():
    # ponytail: baseline migration builds from models; later changes are explicit alembic ops.
    Base.metadata.create_all(op.get_bind())


def downgrade():
    Base.metadata.drop_all(op.get_bind())
