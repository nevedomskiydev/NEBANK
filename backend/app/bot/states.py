from aiogram.fsm.state import State, StatesGroup


class Capture(StatesGroup):
    await_crypto_amount = State()  # data: coin, network, txid, day
