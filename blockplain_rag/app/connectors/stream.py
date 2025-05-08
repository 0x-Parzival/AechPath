import asyncio
import json
import logging
import pathway as pw
from typing import Dict, Any, List, Optional

from connectors.blockplain import BlockPlainConnector

logger = logging.getLogger(__name__)

class BlockchainDataStream:
    """
    Manages streaming data from the BlockPlain blockchain to Pathway
    """
    
    def __init__(self, api_url: str, ws_url: str):
        self.connector = BlockPlainConnector(api_url, ws_url)
        self.queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
    
    async def start(self):
        """Start streaming data from blockchain to queue"""
        # First load initial state
        await self._load_initial_state()
        
        # Then start streaming updates
        asyncio.create_task(self._stream_updates())
    
    async def stop(self):
        """Stop streaming data"""
        self._stop_event.set()
        await self.connector.close()
    
    async def _load_initial_state(self):
        """Load the initial blockchain state"""
        # Get all existing blocks
        try:
            blocks = await self.connector.get_blocks()
            for block in blocks:
                await self._process_block(block)
                
            # Get pending transactions
            txs = await self.connector.get_transactions()
            for tx in txs:
                await self._process_transaction(tx)
                
            logger.info(f"Loaded initial state: {len(blocks)} blocks, {len(txs)} transactions")
        except Exception as e:
            logger.error(f"Error loading initial state: {e}")
    
    async def _stream_updates(self):
        """Stream real-time updates from blockchain"""
        while not self._stop_event.is_set():
            try:
                async for update in self.connector.stream_updates():
                    if update["type"] == "newBlock":
                        await self._process_block(update["data"])
                    elif update["type"] == "newTransaction":
                        await self._process_transaction(update["data"])
            except Exception as e:
                logger.error(f"Error streaming updates: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
    
    async def _process_block(self, block: Dict[str, Any]):
        """Process a block for the queue"""
        # Add metadata for RAG system
        block["_document_type"] = "block"
        
        # Generate searchable text representation
        text = f"Block at [{block.get('X', '?')}, {block.get('Y', '?')}]\n"
        text += f"Hash: {block.get('Hash', '?')}\n"
        text += f"Previous Hashes: X={block.get('PrevHashX', '?')}, Y={block.get('PrevHashY', '?')}\n"
        text += f"Context: {block.get('Context', '?')}\n"
        text += f"Timestamp: {block.get('Timestamp', '?')}\n"
        text += "Transactions:\n"
        
        for i, tx in enumerate(block.get("Data", [])):
            text += f"  {i+1}. {tx}\n"
        
        block["_text"] = text
        block["_id"] = f"block_{block.get('X', 0)}_{block.get('Y', 0)}"
        
        # Add to queue
        await self.queue.put(block)
    
    async def _process_transaction(self, tx: Dict[str, Any]):
        """Process a transaction for the queue"""
        # Add metadata for RAG system
        tx["_document_type"] = "transaction"
        
        # Generate searchable text representation
        text = f"Transaction {tx.get('ID', '?')}\n"
        text += f"Data: {tx.get('Data', '?')}\n"
        
        tx["_text"] = text
        tx["_id"] = f"tx_{tx.get('ID', '')}"
        
        # Add to queue
        await self.queue.put(tx)
    
    def pathway_connector(self, context: pw.io.python.ConnectorContext):
        """Connector function for Pathway to pull data from the queue"""
        async def run():
            while True:
                item = await self.queue.get()
                context.add_data(item)
                self.queue.task_done()
        
        loop = asyncio.get_event_loop()
        loop.create_task(run())
        loop.run_forever()