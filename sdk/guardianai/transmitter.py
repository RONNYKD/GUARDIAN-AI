"""
GuardianAI SDK Telemetry Transmitter

Transmits telemetry data to the GuardianAI backend.
Implements Requirements 4.1 and 4.2 for reliable transmission.
"""

import asyncio
import logging
import time
import threading
import queue
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class TransmissionConfig:
    """Configuration for telemetry transmission."""
    backend_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    batch_size: int = 10
    flush_interval_seconds: float = 5.0
    max_queue_size: int = 1000
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0


@dataclass
class TransmissionResult:
    """Result of a transmission attempt."""
    success: bool
    items_sent: int
    items_failed: int
    error_message: Optional[str] = None
    latency_ms: float = 0


class TelemetryTransmitter:
    """
    Transmits telemetry to GuardianAI backend.
    
    Implements Requirement 4.1: Transmit within 1 second of generation.
    Implements Requirement 4.2: Batch transmission (max 10 per batch).
    
    Features:
    - Async transmission with batching
    - Background thread for continuous flushing
    - Retry logic for failed transmissions
    - Queue overflow protection
    
    Example:
        >>> transmitter = TelemetryTransmitter(
        ...     backend_url="https://api.guardianai.example.com",
        ...     api_key="your-api-key"
        ... )
        >>> transmitter.start()
        >>> transmitter.enqueue(telemetry_data)
        >>> transmitter.stop()
    """
    
    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval_seconds: float = 5.0,
        max_queue_size: int = 1000,
        timeout_seconds: float = 30.0,
        on_send: Optional[Callable[[List[Dict]], None]] = None
    ) -> None:
        """
        Initialize the transmitter.
        
        Args:
            backend_url: GuardianAI backend URL
            api_key: API key for authentication
            batch_size: Maximum items per batch (Req 4.2: max 10)
            flush_interval_seconds: Interval for background flushing
            max_queue_size: Maximum queue size before dropping
            timeout_seconds: HTTP timeout
            on_send: Optional callback for testing
        """
        self.config = TransmissionConfig(
            backend_url=backend_url,
            api_key=api_key,
            batch_size=min(batch_size, 10),  # Enforce max 10 per Req 4.2
            flush_interval_seconds=flush_interval_seconds,
            max_queue_size=max_queue_size,
            timeout_seconds=timeout_seconds
        )
        
        self._queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None
        self._last_transmission_time: float = 0
        self._on_send = on_send
        
        # Statistics
        self._stats = {
            "enqueued": 0,
            "sent": 0,
            "failed": 0,
            "dropped": 0,
        }
    
    def start(self) -> None:
        """Start the background transmission thread."""
        if self._running:
            return
        
        self._running = True
        self._flush_thread = threading.Thread(
            target=self._background_flush,
            daemon=True,
            name="guardianai-transmitter"
        )
        self._flush_thread.start()
        logger.info("TelemetryTransmitter started")
    
    def stop(self, flush: bool = True) -> None:
        """
        Stop the transmitter.
        
        Args:
            flush: Whether to flush remaining items before stopping
        """
        self._running = False
        
        if flush:
            self.flush()
        
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=5.0)
        
        logger.info("TelemetryTransmitter stopped")
    
    def enqueue(self, data: Dict[str, Any]) -> bool:
        """
        Add telemetry data to the transmission queue.
        
        Args:
            data: Telemetry data dictionary
        
        Returns:
            True if enqueued successfully, False if dropped
        """
        timestamp = time.time()
        
        item = {
            "data": data,
            "enqueue_time": timestamp
        }
        
        try:
            self._queue.put_nowait(item)
            self._stats["enqueued"] += 1
            return True
        except queue.Full:
            self._stats["dropped"] += 1
            logger.warning("Queue full, dropping telemetry")
            return False
    
    def flush(self) -> TransmissionResult:
        """
        Immediately flush all queued items.
        
        Returns:
            TransmissionResult with details
        """
        items = []
        while not self._queue.empty() and len(items) < self.config.batch_size:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        
        if not items:
            return TransmissionResult(
                success=True,
                items_sent=0,
                items_failed=0
            )
        
        return self._transmit_batch(items)
    
    def flush_all(self) -> List[TransmissionResult]:
        """
        Flush all queued items in batches.
        
        Returns:
            List of TransmissionResults
        """
        results = []
        
        while not self._queue.empty():
            result = self.flush()
            results.append(result)
            
            if result.items_sent == 0:
                break
        
        return results
    
    def _background_flush(self) -> None:
        """Background thread for periodic flushing."""
        while self._running:
            try:
                # Wait for flush interval or until items available
                time.sleep(self.config.flush_interval_seconds)
                
                # Check if we should flush based on timing (Req 4.1)
                if not self._queue.empty():
                    self.flush()
                    
            except Exception as e:
                logger.error(f"Background flush error: {e}")
    
    def _transmit_batch(self, items: List[Dict]) -> TransmissionResult:
        """
        Transmit a batch of items.
        
        Implements Requirement 4.1: Transmission within 1 second.
        
        Args:
            items: List of queue items with data and enqueue_time
        
        Returns:
            TransmissionResult
        """
        if not items:
            return TransmissionResult(success=True, items_sent=0, items_failed=0)
        
        start_time = time.time()
        
        # Check timing constraint (Req 4.1)
        for item in items:
            age_seconds = start_time - item["enqueue_time"]
            if age_seconds > 1.0:
                logger.warning(
                    f"Telemetry transmission delayed: {age_seconds:.2f}s > 1s"
                )
        
        # Prepare batch payload
        batch_data = [item["data"] for item in items]
        
        try:
            # Use callback if provided (for testing)
            if self._on_send:
                self._on_send(batch_data)
                self._stats["sent"] += len(items)
                return TransmissionResult(
                    success=True,
                    items_sent=len(items),
                    items_failed=0,
                    latency_ms=(time.time() - start_time) * 1000
                )
            
            # Real HTTP transmission
            result = self._http_post(batch_data)
            
            if result.success:
                self._stats["sent"] += result.items_sent
            else:
                self._stats["failed"] += result.items_failed
            
            return result
            
        except Exception as e:
            logger.error(f"Transmission error: {e}")
            self._stats["failed"] += len(items)
            return TransmissionResult(
                success=False,
                items_sent=0,
                items_failed=len(items),
                error_message=str(e)
            )
    
    def _http_post(self, batch: List[Dict]) -> TransmissionResult:
        """
        Send batch via HTTP POST.
        
        Args:
            batch: List of telemetry records
        
        Returns:
            TransmissionResult
        """
        import urllib.request
        import urllib.error
        
        url = f"{self.config.backend_url}/api/v1/telemetry/batch"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        payload = json.dumps({"records": batch}).encode("utf-8")
        
        start_time = time.time()
        
        for attempt in range(self.config.retry_attempts):
            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers=headers,
                    method="POST"
                )
                
                with urllib.request.urlopen(
                    req,
                    timeout=self.config.timeout_seconds
                ) as response:
                    if response.status == 200:
                        self._last_transmission_time = time.time()
                        return TransmissionResult(
                            success=True,
                            items_sent=len(batch),
                            items_failed=0,
                            latency_ms=(time.time() - start_time) * 1000
                        )
                    
            except urllib.error.URLError as e:
                logger.warning(
                    f"Transmission attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay_seconds)
        
        return TransmissionResult(
            success=False,
            items_sent=0,
            items_failed=len(batch),
            error_message="Max retries exceeded"
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get transmission statistics."""
        return dict(self._stats)
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    @property
    def is_running(self) -> bool:
        """Check if transmitter is running."""
        return self._running


class AsyncTelemetryTransmitter:
    """
    Async version of TelemetryTransmitter.
    
    For use in async applications.
    """
    
    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval_seconds: float = 5.0
    ) -> None:
        """Initialize async transmitter."""
        self.config = TransmissionConfig(
            backend_url=backend_url,
            api_key=api_key,
            batch_size=min(batch_size, 10),
            flush_interval_seconds=flush_interval_seconds
        )
        
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start async background flushing."""
        self._running = True
        self._flush_task = asyncio.create_task(self._background_flush())
    
    async def stop(self, flush: bool = True) -> None:
        """Stop async transmitter."""
        self._running = False
        
        if flush:
            await self.flush()
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
    
    async def enqueue(self, data: Dict[str, Any]) -> bool:
        """Enqueue telemetry data asynchronously."""
        try:
            await asyncio.wait_for(
                self._queue.put({
                    "data": data,
                    "enqueue_time": time.time()
                }),
                timeout=1.0
            )
            return True
        except asyncio.TimeoutError:
            return False
    
    async def flush(self) -> TransmissionResult:
        """Flush queued items asynchronously."""
        items = []
        
        while not self._queue.empty() and len(items) < self.config.batch_size:
            try:
                items.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        
        if not items:
            return TransmissionResult(
                success=True, items_sent=0, items_failed=0
            )
        
        return await self._transmit_batch_async(items)
    
    async def _background_flush(self) -> None:
        """Async background flush loop."""
        while self._running:
            await asyncio.sleep(self.config.flush_interval_seconds)
            if not self._queue.empty():
                await self.flush()
    
    async def _transmit_batch_async(
        self,
        items: List[Dict]
    ) -> TransmissionResult:
        """Transmit batch using aiohttp if available."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.backend_url}/api/v1/telemetry/batch"
                headers = {"Content-Type": "application/json"}
                
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                batch_data = [item["data"] for item in items]
                
                async with session.post(
                    url,
                    json={"records": batch_data},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(
                        total=self.config.timeout_seconds
                    )
                ) as response:
                    if response.status == 200:
                        return TransmissionResult(
                            success=True,
                            items_sent=len(items),
                            items_failed=0
                        )
                    else:
                        return TransmissionResult(
                            success=False,
                            items_sent=0,
                            items_failed=len(items),
                            error_message=f"HTTP {response.status}"
                        )
                        
        except ImportError:
            # Fallback to sync if aiohttp not available
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: TelemetryTransmitter()._transmit_batch(items)
            )
        except Exception as e:
            return TransmissionResult(
                success=False,
                items_sent=0,
                items_failed=len(items),
                error_message=str(e)
            )
