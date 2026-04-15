import asyncio
from binance import AsyncClient, BinanceSocketManager
from google.cloud import bigquery
from datetime import datetime
import os

# 1. Cấu hình BigQuery
# Đảm bảo bạn đã để file key trong folder dự án
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json" 

client = bigquery.Client()
# Thay project_id bằng id của bạn
TABLE_ID = "snappy-monolith-481115-e5.crypto_dataset.btc_realtime"

async def main():
    binance_client = await AsyncClient.create()
    bsm = BinanceSocketManager(binance_client)
    ts = bsm.trade_socket('BTCUSDT')
    
    async with ts as tscm:
        print(f"🚀 Streaming started. Ingesting to {TABLE_ID}...")
        while True:
            msg = await tscm.recv()
            if msg:
                # 2. Chuẩn bị dữ liệu theo Schema của bảng
                rows_to_insert = [
                    {
                        "event_time": datetime.fromtimestamp(msg['E']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                        "symbol": msg['s'],
                        "price": float(msg['p'])
                    }
                ]
                
                # 3. Thực hiện Streaming Insert
                errors = client.insert_rows_json(TABLE_ID, rows_to_insert)
                
                if errors == []:
                    print(f"✅ New trade: {msg['s']} - {msg['p']} - Streamed to BQ")
                else:
                    print(f"❌ Errors: {errors}")

    await binance_client.close_connection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped streaming.")