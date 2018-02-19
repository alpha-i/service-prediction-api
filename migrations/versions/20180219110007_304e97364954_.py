"""empty message

Revision ID: 304e97364954
Revises: 1d9f34445160
Create Date: 2018-02-19 11:00:07.119632

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '304e97364954'
down_revision = '1d9f34445160'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('customer_profile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_update', sa.DateTime(timezone=True), nullable=True),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_profile_created_at'), 'customer_profile', ['created_at'], unique=False)
    op.create_index(op.f('ix_customer_profile_last_update'), 'customer_profile', ['last_update'], unique=False)
    op.add_column('customer', sa.Column('email', sa.String(length=32), nullable=True))
    op.create_index(op.f('ix_customer_email'), 'customer', ['email'], unique=False)
    op.drop_index('ix_customer_username', table_name='customer')
    op.drop_column('customer', 'username')
    op.alter_column('prediction_task', 'name',
               existing_type=sa.VARCHAR(length=60),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('prediction_task', 'name',
               existing_type=sa.VARCHAR(length=60),
               nullable=True)
    op.add_column('customer', sa.Column('username', sa.VARCHAR(length=32), autoincrement=False, nullable=True))
    op.create_index('ix_customer_username', 'customer', ['username'], unique=False)
    op.drop_index(op.f('ix_customer_email'), table_name='customer')
    op.drop_column('customer', 'email')
    op.drop_index(op.f('ix_customer_profile_last_update'), table_name='customer_profile')
    op.drop_index(op.f('ix_customer_profile_created_at'), table_name='customer_profile')
    op.drop_table('customer_profile')
    # ### end Alembic commands ###
