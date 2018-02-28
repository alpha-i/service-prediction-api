"""empty message

Revision ID: 9198ce653b2f
Revises: d96d514f79e1
Create Date: 2018-02-28 18:39:37.133701

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9198ce653b2f'
down_revision = 'd96d514f79e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('data_source', sa.Column('is_original', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('data_source', 'is_original')
    # ### end Alembic commands ###
