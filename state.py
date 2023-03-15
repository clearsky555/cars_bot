from aiogram.dispatcher.filters.state import StatesGroup, State


class CarsSearchState(StatesGroup):
    search_by_name = State()
    # search_by_price = State()
    price_start = State()
    price_end = State()
