from src.database.models import WordleAttempt, WordleDay


def apply(db):
    db.create_tables([WordleDay, WordleAttempt], safe=True)


