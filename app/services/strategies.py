from app.strategies import upload


def get_upload_strategy(strategy_class: str):
    strategy = getattr(upload, strategy_class)
    return strategy()
