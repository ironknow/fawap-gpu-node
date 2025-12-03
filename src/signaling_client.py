"""
Signaling client for communicating with the orchestrator.
Receives signaling messages and manages WebRTC handshake.
"""
import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any
from .config import config

logger = logging.getLogger(__name__)


class SignalingClient:
    """Client for orchestrator signaling communication."""
    
    def __init__(self, orchestrator_url: Optional[str] = None, node_id: Optional[str] = None):
        """
        Initialize signaling client.
        
        Args:
            orchestrator_url: URL of the orchestrator API
            node_id: Unique node identifier
        """
        self.orchestrator_url = orchestrator_url or config.orchestrator_url
        self.node_id = node_id or config.node_id
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """Start the signaling client."""
        if self.orchestrator_url:
            self.session = aiohttp.ClientSession()
            logger.info(f"Signaling client started, orchestrator: {self.orchestrator_url}")
        else:
            logger.warning("No orchestrator URL configured, signaling disabled")
    
    async def stop(self):
        """Stop the signaling client."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Signaling client stopped")
    
    async def register_node(self, node_info: Dict[str, Any]) -> bool:
        """
        Register this node with the orchestrator.
        
        Args:
            node_info: Node information (GPU, status, etc.)
            
        Returns:
            True if registration successful
        """
        if not self.session or not self.orchestrator_url:
            return False
        
        try:
            url = f"{self.orchestrator_url}/nodes/register"
            async with self.session.post(url, json={
                "node_id": self.node_id,
                **node_info
            }) as response:
                if response.status == 200:
                    logger.info("Node registered with orchestrator")
                    return True
                else:
                    logger.error(f"Registration failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Failed to register node: {e}")
            return False
    
    async def send_health_update(self, health_data: Dict[str, Any]) -> bool:
        """
        Send health update to orchestrator.
        
        Args:
            health_data: Health information
            
        Returns:
            True if update successful
        """
        if not self.session or not self.orchestrator_url:
            return False
        
        try:
            url = f"{self.orchestrator_url}/nodes/{self.node_id}/health"
            async with self.session.post(url, json=health_data) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send health update: {e}")
            return False
    
    async def receive_offer(self) -> Optional[Dict[str, Any]]:
        """
        Poll for incoming SDP offer from orchestrator.
        
        Returns:
            Offer data or None
        """
        if not self.session or not self.orchestrator_url:
            return None
        
        try:
            url = f"{self.orchestrator_url}/nodes/{self.node_id}/offers"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data if data else None
                return None
        except Exception as e:
            logger.error(f"Failed to receive offer: {e}")
            return None
    
    async def send_answer(self, answer_sdp: str, session_id: str) -> bool:
        """
        Send SDP answer to orchestrator.
        
        Args:
            answer_sdp: SDP answer string
            session_id: Session identifier
            
        Returns:
            True if send successful
        """
        if not self.session or not self.orchestrator_url:
            return False
        
        try:
            url = f"{self.orchestrator_url}/nodes/{self.node_id}/answers"
            async with self.session.post(url, json={
                "session_id": session_id,
                "answer": answer_sdp
            }) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send answer: {e}")
            return False

