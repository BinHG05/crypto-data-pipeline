import asyncio
from datetime import datetime

from binance import AsyncClient, BinanceSocketManager
from google.cloud import bigquery

from config.api_config import BTC_REALTIME_TABLE_ID
from utils.logger import get_logger

logger = get_logger(__name__)

client = bigquery.Client()

TABLE_ID = BTC_REALTIME_TABLE_ID


async def main():

    logger.info(f"Starting Binance streaming ingestion | table={TABLE_ID}")

    binance_client = await AsyncClient.create()

    bsm = BinanceSocketManager(binance_client)

    trade_socket = bsm.trade_socket("BTCUSDT")

    try:

        async with trade_socket as socket_client:

            logger.info("WebSocket connection established")

            while True:

                msg = await socket_client.recv()

                if not msg:

                    logger.warning("Received empty websocket message")

                    continue

                rows_to_insert = [
                    {
                        "event_time": datetime.fromtimestamp(msg["E"] / 1000).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "symbol": msg["s"],
                        "price": float(msg["p"]),
                    }
                ]

                errors = client.insert_rows_json(TABLE_ID, rows_to_insert)

                if not errors:

                    logger.info(
                        "Streamed trade successfully | "
                        f"symbol={msg['s']} | price={msg['p']}"
                    )

                else:

                    logger.error(f"BigQuery streaming insert failed | errors={errors}")

    except Exception as exc:

        logger.error(f"Streaming pipeline failed | error={exc}")

        raise

    finally:

        logger.info("Closing Binance websocket connection")

        await binance_client.close_connection()


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logger.warning("Streaming pipeline stopped manually")
