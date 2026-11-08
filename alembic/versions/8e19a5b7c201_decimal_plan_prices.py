"""Store catalog prices as exact monetary amounts."""
from alembic import op
import sqlalchemy as sa

revision = "8e19a5b7c201"
down_revision = "37212ae7fe48"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("plans", "price", existing_type=sa.Float(), type_=sa.Numeric(8, 2),
                    existing_nullable=False, postgresql_using="round(price::numeric, 2)")


def downgrade():
    op.alter_column("plans", "price", existing_type=sa.Numeric(8, 2), type_=sa.Float(),
                    existing_nullable=False, postgresql_using="price::double precision")
