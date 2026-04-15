import asyncio
from datetime import datetime

from binance import AsyncClient, BinanceSocketManager
from google.cloud import bigquery

from config.api_config import BTC_REALTIME_TABLE_ID


client = bigquery.Client()
TABLE_ID = BTC_REALTIME_TABLE_ID


async def main():
    binance_client = await AsyncClient.create()
    bsm = BinanceSocketManager(binance_client)
    trade_socket = bsm.trade_socket("BTCUSDT")

    async with trade_socket as socket_client:
        print(f"Streaming started. Ingesting to {TABLE_ID}...")
        while True:
            msg = await socket_client.recv()
            if msg:
                rows_to_insert = [
                    {
                        "event_time": datetime.fromtimestamp(msg["E"] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                        "symbol": msg["s"],
                        "price": float(msg["p"]),
                    }
                ]

                errors = client.insert_rows_json(TABLE_ID, rows_to_insert)

                if not errors:
                    print(f"New trade: {msg['s']} - {msg['p']} - streamed to BigQuery")
                else:
                    print(f"Streaming insert errors: {errors}")

    await binance_client.close_connection()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped streaming.")
