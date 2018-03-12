"""empty message

Revision ID: 81774f4046f5
Revises: 9198ce653b2f
Create Date: 2018-03-07 11:03:34.128049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '81774f4046f5'
down_revision = '9198ce653b2f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('data_source', sa.Column('features', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('data_source', 'features')
    # ### end Alembic commands ###