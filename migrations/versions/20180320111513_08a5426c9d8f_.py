"""empty message

Revision ID: 08a5426c9d8f
Revises: 4135a184b961
Create Date: 2018-03-20 11:15:13.496342

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08a5426c9d8f'
down_revision = '4135a184b961'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prediction_task', sa.Column('company_id', sa.Integer(), nullable=False))
    op.create_foreign_key('prediction_task_company_id_fkey', 'prediction_task', 'company', ['company_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('prediction_task_company_id_fkey', 'prediction_task', type_='foreignkey')
    op.drop_column('prediction_task', 'company_id')
    # ### end Alembic commands ###
