"""
Main application entry point for GPU Node.
Sets up WebRTC server, health API, and orchestrator communication.
"""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import torch

from .config import config
from .swap_engine import SwapEngine
from .frame_processor import FrameProcessor
from .webrtc_server import WebRTCServer
from .signaling_client import SignalingClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
swap_engine: Optional[SwapEngine] = None
frame_processor: Optional[FrameProcessor] = None
webrtc_server: Optional[WebRTCServer] = None
signaling_client: Optional[SignalingClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global swap_engine, frame_processor, webrtc_server, signaling_client
    
    # Startup
    logger.info("Starting GPU Node...")
    
    try:
        # Initialize swap engine
        logger.info(f"Loading model: {config.model_type} from {config.model_path}")
        swap_engine = SwapEngine(
            model_path=config.model_path,
            model_type=config.model_type,
            gpu_id=config.gpu_id
        )
        
        # Initialize frame processor
        frame_processor = FrameProcessor()
        
        # Initialize WebRTC server
        webrtc_server = WebRTCServer(swap_engine, frame_processor)
        
        # Initialize signaling client
        signaling_client = SignalingClient()
        await signaling_client.start()
        
        # Register node with orchestrator if configured
        if signaling_client.orchestrator_url:
            node_info = {
                "gpu": torch.cuda.get_device_name(config.gpu_id) if torch.cuda.is_available() else "CPU",
                "status": "ready",
                "port": config.port
            }
            await signaling_client.register_node(node_info)
        
        logger.info("GPU Node started successfully")
        
        # Start background tasks
        asyncio.create_task(health_reporting_task())
        asyncio.create_task(signaling_polling_task())
        
    except Exception as e:
        logger.error(f"Failed to start GPU Node: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down GPU Node...")
    
    if webrtc_server:
        await webrtc_server.close_all()
    
    if signaling_client:
        await signaling_client.stop()
    
    logger.info("GPU Node shut down")


# Create FastAPI app
app = FastAPI(title="GPU Node", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "gpu": torch.cuda.get_device_name(config.gpu_id),
                "memory_used": torch.cuda.memory_allocated(config.gpu_id) / 1024**3,  # GB
                "memory_total": torch.cuda.get_device_properties(config.gpu_id).total_memory / 1024**3,  # GB
            }
            if swap_engine:
                gpu_info.update(swap_engine.get_gpu_memory_usage())
        
        active_connections = webrtc_server.get_active_connections() if webrtc_server else 0
        
        return {
            "status": "ok",
            "model": config.model_type,
            "gpu": gpu_info.get("gpu", "N/A"),
            "memory_used": round(gpu_info.get("memory_used", 0), 2),
            "active_sessions": active_connections,
            "node_id": config.node_id
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/configure")
async def configure_node(config_data: dict):
    """Configure node settings."""
    try:
        # Update configuration if needed
        # This is a placeholder - actual implementation would update config
        logger.info(f"Configuration update requested: {config_data}")
        return {"status": "ok", "message": "Configuration updated"}
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signaling/offer")
async def handle_signaling_offer(offer_data: dict):
    """Handle SDP offer from orchestrator."""
    try:
        if not webrtc_server:
            raise HTTPException(status_code=503, detail="WebRTC server not initialized")
        
        offer_sdp = offer_data.get("offer")
        if not offer_sdp:
            raise HTTPException(status_code=400, detail="Missing offer SDP")
        
        # Create answer
        answer_sdp = await webrtc_server.handle_offer(offer_sdp)
        
        return {
            "answer": answer_sdp,
            "session_id": offer_data.get("session_id", "unknown")
        }
    except Exception as e:
        logger.error(f"Signaling offer handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def health_reporting_task():
    """Background task to report health to orchestrator."""
    while True:
        try:
            await asyncio.sleep(config.health_check_interval)
            
            if signaling_client and signaling_client.orchestrator_url:
                health_data = {
                    "status": "ok",
                    "gpu_memory": swap_engine.get_gpu_memory_usage() if swap_engine else {},
                    "active_sessions": webrtc_server.get_active_connections() if webrtc_server else 0
                }
                await signaling_client.send_health_update(health_data)
        except Exception as e:
            logger.error(f"Health reporting error: {e}")


async def signaling_polling_task():
    """Background task to poll for signaling messages."""
    while True:
        try:
            await asyncio.sleep(1)  # Poll every second
            
            if signaling_client:
                offer = await signaling_client.receive_offer()
                if offer and webrtc_server:
                    offer_sdp = offer.get("offer")
                    session_id = offer.get("session_id")
                    
                    if offer_sdp:
                        answer_sdp = await webrtc_server.handle_offer(offer_sdp)
                        await signaling_client.send_answer(answer_sdp, session_id)
        except Exception as e:
            logger.error(f"Signaling polling error: {e}")


def main():
    """Main entry point."""
    logger.info(f"Starting GPU Node on {config.host}:{config.port}")
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

