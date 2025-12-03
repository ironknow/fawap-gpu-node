"""
Configuration management for GPU Node.
Handles environment variables and settings.
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration class for GPU Node."""
    
    # Server settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8080"))
    
    # WebRTC settings
    webrtc_port: int = int(os.getenv("WEBRTC_PORT", "8081"))
    stun_server: str = os.getenv("STUN_SERVER", "stun:stun.l.google.com:19302")
    
    # Model settings
    model_path: str = os.getenv("MODEL_PATH", "/app/models")
    model_type: str = os.getenv("MODEL_TYPE", "insightface")  # insightface or deepfacelive
    
    # GPU settings
    gpu_id: int = int(os.getenv("GPU_ID", "0"))
    batch_size: int = int(os.getenv("BATCH_SIZE", "1"))
    
    # Face swap settings
    swap_threshold: float = float(os.getenv("SWAP_THRESHOLD", "0.5"))
    face_detection_threshold: float = float(os.getenv("FACE_DETECTION_THRESHOLD", "0.5"))
    
    # Orchestrator settings
    orchestrator_url: Optional[str] = os.getenv("ORCHESTRATOR_URL", None)
    node_id: Optional[str] = os.getenv("NODE_ID", None)
    
    # Health check settings
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    # Session settings
    max_sessions: int = int(os.getenv("MAX_SESSIONS", "1"))
    idle_timeout: int = int(os.getenv("IDLE_TIMEOUT", "300"))  # 5 minutes
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls()


# Global config instance
config = Config.from_env()

