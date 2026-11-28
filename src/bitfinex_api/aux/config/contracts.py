"""Pydantic contracts for Bitfinex config payloads."""
from pydantic import BaseModel, ConfigDict, Field


class PairSymbolsContract(BaseModel):
    """Contract for pair symbols."""

    model_config = ConfigDict(str_strip_whitespace=True)

    instrument: str = Field(
      description=(
         "The instrument used to identify the pair on Bitfinex "
         "trading endpoints."))
    """The instrument used to identify the pair on Bitfinex trading
       endpoints."""
    trading_prefix: str | None = Field(
      description=(
         "The trading prefix of the pair. Either ``t`` or ``f``."))
    """The trading prefix of the pair. Either ``t`` or ``f``."""
    pair: str = Field(
      description=(
         "The pair symbol of the pair."))
    """The pair symbol of the pair."""
    base: str = Field(
      description=(
         "The base asset of the pair."))
    """The base asset of the pair."""
    quote: str = Field(
      description=(
         "The quote asset of the pair."))
    """The quote asset of the pair."""
