"""empty message

Revision ID: 2937c82370e8
Revises: 304e97364954
Create Date: 2018-02-19 11:01:59.599876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2937c82370e8'
down_revision = '304e97364954'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('company',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_update', sa.DateTime(timezone=True), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('logo', sa.String(), nullable=True),
    sa.Column('profile', sa.JSON(), nullable=True),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_created_at'), 'company', ['created_at'], unique=False)
    op.create_index(op.f('ix_company_last_update'), 'company', ['last_update'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_company_last_update'), table_name='company')
    op.drop_index(op.f('ix_company_created_at'), table_name='company')
    op.drop_table('company')
    # ### end Alembic commands ###