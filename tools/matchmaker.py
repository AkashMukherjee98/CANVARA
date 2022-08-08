from datetime import datetime
import argparse
import time
import uuid

from sqlalchemy import and_, or_

# TODO: (sunil) Clean up the db mappers so we don't need to import these models unnecessarily
from backend.models.db import transaction
from backend.models.application import Application  # noqa: F401
from backend.models.customer import Customer
from backend.models.location import Location  # noqa: F401
from backend.models.match import UserPostMatch
from backend.models.post import Post
from backend.models.product_preference import ProductPreference  # noqa: F401
from backend.models.user import User, UserCurrentSkill


REQUIRED_SKILL_LEVEL_MATCH_WEIGHT = 2
REQUIRED_SKILL_MATCH_WEIGHT = 0.5
DESIRED_SKILL_MATCH_WEIGHT = 1

# Don't record any matches below this threshold
# Set to 0 for now to record all matches, but this may be tweaked in future
MATCH_REPORTING_THRESHOLD = 0

# Time to wait between successive iterations
DEFAULT_SLEEP_INTERVAL_SECONDS = 0.5


def compute_score(post, user):
    score = 0
    for user_skill in user.current_skills:
        for post_skill in post.required_skills:
            if post_skill.id == user_skill.id:
                score += 2 if user_skill.level >= post_skill.level else 0.5
                break

        for post_skill in post.desired_skills:
            if post_skill.id == user_skill.id:
                score += 1
                break
    return score


def record_match(tx, post, user, score_percentage):
    now = datetime.utcnow()
    match = tx.query(UserPostMatch)\
        .where(UserPostMatch.user_id == user.id)\
        .where(UserPostMatch.post_id == post.id)\
        .one_or_none()
    if match is None:
        print(f"Post '{post.id}' - adding match for User '{user.id}' with confidence of {score_percentage}")
        match = UserPostMatch(
            id=str(uuid.uuid4()),
            user_id=user.id,
            post_id=post.id,
            confidence_level=score_percentage,
            created_at=now,
            updated_at=now,
            updated_by='Matchmaker'
        )
        tx.add(match)
    elif match.confidence_level != score_percentage:
        print(f"Post '{post.id}' - updating a match for User '{user.id}' with confidence of {score_percentage}")
        match.confidence_level = score_percentage
        match.updated_at = now
        match.updated_by = 'Matchmaker'


def analyze_customer_posts(customer_id):
    # TODO: (sunil) Connect directly to the database for now. Use API in future.
    with transaction() as tx:
        posts = tx.query(Post).join(Post.owner).where(User.customer_id == customer_id)
        for post in posts:
            # For now, only consider posts that have required and desired skills defined
            if not post.required_skills and not post.desired_skills:
                continue

            # Gather all the skills mentioned in the post
            # Then find all users within the same customer who have at least one of those skills
            required_skill_ids = [skill.id for skill in post.required_skills]
            desired_skill_ids = [skill.id for skill in post.desired_skills]
            candidates = tx.query(User).join(UserCurrentSkill).where(
                and_(
                    or_(
                        UserCurrentSkill.skill_id.in_(required_skill_ids),
                        UserCurrentSkill.skill_id.in_(desired_skill_ids)
                    ),
                    User.customer_id == customer_id
                )
            )

            # Now compare the user's skills with the post's skills and generate a score for the match
            # - Every required skill that's a match including level, is worth two points
            # - Every desired skill that's a match, is worth one point
            # - Every required skill that's a match except for the level, is worth half a point
            max_score = (REQUIRED_SKILL_LEVEL_MATCH_WEIGHT * len(required_skill_ids)) \
                + (DESIRED_SKILL_MATCH_WEIGHT * len(desired_skill_ids))
            for user in candidates:
                score = compute_score(post, user)
                score_percentage = int(score*100/max_score)
                if score_percentage > MATCH_REPORTING_THRESHOLD:
                    record_match(tx, post, user, score_percentage)


def analyze_posts():
    with transaction() as tx:
        customers = tx.query(Customer)
        for customer in customers:
            analyze_customer_posts(customer.id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sleep', type=float, default=DEFAULT_SLEEP_INTERVAL_SECONDS, help='Number of seconds to sleep between iterations')
    args = parser.parse_args()

    # For now, analyze all posts and all users on every iteration
    # If this starts to take too long, or starts generating too much load on the database,
    # this can be optimized to process only the most recent posts on every iteration, and run
    # full analysis on a less frequent interval (e.g. every 6 or 12 hours)
    while True:
        start_time = time.time()
        try:
            analyze_posts()
        except Exception as ex:
            print(f"Error while analyzing posts: {ex!r}")
        else:
            end_time = time.time()
            print(f"Finished analysis in {(end_time - start_time)*1000:.2f} ms")
        time.sleep(args.sleep)


if __name__ == '__main__':
    main()
