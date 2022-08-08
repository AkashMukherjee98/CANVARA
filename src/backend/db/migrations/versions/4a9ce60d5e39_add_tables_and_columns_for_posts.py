"""add tables and additional columns for posts

Revision ID: 4a9ce60d5e39
Revises: 467904656c3a
Create Date: 2021-06-29 15:59:16.300757

"""
import uuid

from alembic import op
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a9ce60d5e39'
down_revision = '467904656c3a'
branch_labels = None
depends_on = None


def add_post_type(post_table):
    post_type_table = op.create_table(
        'post_type',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),

        # The order in which these types should be displayed in the UI
        sa.Column('rank', sa.Integer, nullable=False, unique=True),
    )

    post_types = [
        {'id': str(uuid.uuid4()), 'name': 'Project', 'rank': 1},
        {'id': str(uuid.uuid4()), 'name': 'Volunteering', 'rank': 2},
        {'id': str(uuid.uuid4()), 'name': 'Committee', 'rank': 3},
        {'id': str(uuid.uuid4()), 'name': 'Mentorship', 'rank': 4},
    ]
    op.bulk_insert(post_type_table, post_types)

    # Add post_type_id column and set all current posts to project for now
    op.add_column('post', sa.Column('post_type_id', UUID, sa.ForeignKey('post_type.id')))
    op.execute(
        post_table.update().values(post_type_id=post_types[0]['id'])
    )
    op.alter_column('post', 'post_type_id', nullable=False)


def add_location():
    location_table = op.create_table(
        'location',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('customer_id', UUID, sa.ForeignKey('customer.id'), nullable=False),
        sa.Index(
            'location_name_customer_id_idx',
            sa.func.lower(sa.text('name')), 'customer_id',
            unique=True
        )
    )

    # Add a default "Remote" location for all customers for now
    customer_table = sa.table(
        'customer',
        sa.column('id', UUID)
    )
    connection = op.get_bind()
    customers = connection.execute(customer_table.select())
    locations = []
    for customer_id, in customers:
        locations.append({
            'id': str(uuid.uuid4()),
            'name': 'Remote',
            'customer_id': customer_id
        })
    op.bulk_insert(location_table, locations)

    # Add location_id column and set all current posts to Remote for now
    op.add_column('post', sa.Column('location_id', UUID, sa.ForeignKey('location.id')))
    op.execute(
        "UPDATE post p SET location_id = l.id FROM canvara_user u "
        "JOIN location l ON l.customer_id = u.customer_id "
        "WHERE u.id = p.owner_id AND l.name = 'Remote'"
    )
    op.alter_column('post', 'location_id', nullable=False)


def add_name():
    # Add name column and set current value from details column
    # Assume every post already has a valid 'summary'
    op.add_column('post', sa.Column('name', sa.Text))
    op.execute(
        "UPDATE post SET name = details->>'summary'"
    )

    # And remove summary from details
    op.execute(
        "UPDATE post SET details = details - 'summary'"
    )
    op.alter_column('post', 'name', nullable=False)


def add_size():
    # Add size column and set current value from details column, or default to S
    op.add_column('post', sa.Column('size', sa.String(7)))
    op.execute(
        "UPDATE post SET size = COALESCE(details->>'size', 'S')"
    )

    # And remove size from details
    op.execute(
        "UPDATE post SET details = details - 'size'"
    )
    op.alter_column('post', 'size', nullable=False)


def add_language(post_table):
    # Add language column and set all current posts to English for now
    op.add_column('post', sa.Column('language', sa.String(255)))
    op.execute(
        post_table.update().values(language='English')
    )
    op.alter_column('post', 'language', nullable=False)


def add_people_needed(post_table):
    # Add people_needed column and set all current posts to 1 for now
    op.add_column('post', sa.Column('people_needed', sa.Integer))
    op.execute(
        post_table.update().values(people_needed=1)
    )
    op.alter_column('post', 'people_needed', nullable=False)


def add_target_date():
    # Add target_date column and set current value from details column, or default to 2021-12-31
    op.add_column('post', sa.Column('target_date', sa.Date))
    op.execute(
        "UPDATE post SET target_date = to_date(COALESCE(details->>'target_date', '2021-12-31'), 'YYYY-MM-DD')"
    )

    # And remove target_date from details
    op.execute(
        "UPDATE post SET details = details - 'target_date'"
    )
    op.alter_column('post', 'target_date', nullable=False)


def add_description():
    # Add description column and set current value from details column, or NULL
    op.add_column('post', sa.Column('description', sa.Text))
    op.execute(
        "UPDATE post SET description = details->>'description'"
    )

    # And remove description from details
    op.execute(
        "UPDATE post SET details = details - 'description'"
    )


def upgrade():
    # Declare the post table so we can use it for the update statements
    # Only the columns that we have to touch need to be declared here
    post_table = sa.table(
        'post',
        sa.column('language', sa.String(255)),
        sa.column('people_needed', sa.Integer),
        sa.column('post_type_id', UUID),
    )

    add_post_type(post_table)
    add_location()
    add_name()
    add_size()
    add_language(post_table)
    add_people_needed(post_table)
    add_target_date()
    add_description()


def downgrade():
    # Add description size, summary and target_date back to details
    op.execute(
        "UPDATE post SET details = jsonb_set(details, '{description}', to_jsonb(description)) "
        "WHERE description IS NOT NULL"
    )
    op.execute(
        "UPDATE post SET details = jsonb_set(details, '{target_date}', to_jsonb(target_date))"
    )
    op.execute(
        "UPDATE post SET details = jsonb_set(details, '{size}', to_jsonb(size))"
    )
    op.execute(
        "UPDATE post SET details = jsonb_set(details, '{summary}', to_jsonb(name))"
    )

    with op.batch_alter_table('post') as batch_op:
        batch_op.drop_column('description')
        batch_op.drop_column('target_date')
        batch_op.drop_column('people_needed')
        batch_op.drop_column('language')
        batch_op.drop_column('size')
        batch_op.drop_column('name')
        batch_op.drop_column('location_id')
        batch_op.drop_column('post_type_id')
    op.drop_table('location')
    op.drop_table('post_type')
