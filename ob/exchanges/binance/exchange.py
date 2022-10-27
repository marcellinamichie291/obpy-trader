import asyncio

import aiohttp
from asyncio import Task, Queue
from urllib.parse import urlencode, urljoin

from ob.models import Symbol

from ..base import BaseExchange
from ..models import ExchangeName
from .factories import OrderBookFactory, SymbolFactory, TradeFactory
from .stream import BinanceStream


class BinanceExchange(BaseExchange):
    slug = ExchangeName.BINANCE

    def __init__(
        self,
        symbol_factory: SymbolFactory,
        order_book_factory: OrderBookFactory,
        trade_factory: TradeFactory,
        base_url: str,
        stream: BinanceStream,
    ):
        self.symbol_factory = symbol_factory
        self.order_book_factory = order_book_factory
        self.trade_factory = trade_factory
        self.base_url = base_url
        self.stream = stream

    async def pull_symbol(self, symbol_slug) -> Symbol:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                urljoin(
                    self.base_url,
                    f"/api/v3/exchangeInfo?" + urlencode({"symbol": symbol_slug}),
                )
            ) as response:
                exchange_info = await response.json()

        return self.symbol_factory.from_exchange_info(exchange_info, symbol=symbol_slug)

    async def _pull_order_book(self, symbol: Symbol):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                urljoin(
                    self.base_url,
                    f"/api/v3/depth?"
                    + urlencode({"symbol": symbol.slug, "limit": 5000}),
                )
            ) as response:
                depth = await response.json()

        return self.order_book_factory.from_depth(depth, symbol=symbol)

    async def _stream_listener(self, symbol: Symbol, queue: Queue):
        async for row in self.stream.listen(
            subscriptions=[
                f"{symbol.slug.lower()}@depth@100ms",
                f"{symbol.slug.lower()}@aggTrade",
            ]
        ):
            data = row.get("data")
            if not data:
                continue

            if data["e"] == "aggTrade":
                await queue.put(self.trade_factory.from_agg_trade(row))
            elif data["e"] == "depthUpdate":
                pass

    async def init_listener(self, symbol: Symbol, queue: Queue) -> Task:
        task = asyncio.ensure_future(self._stream_listener(symbol=symbol, queue=queue))
        await asyncio.sleep(0)

        return task
