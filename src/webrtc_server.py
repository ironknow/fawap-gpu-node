"""
WebRTC server for handling video streaming.
Receives video from frontend, processes frames, and sends back processed video.
"""
import asyncio
import logging
from typing import Optional
import numpy as np
from av import VideoFrame
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay

from .swap_engine import SwapEngine
from .frame_processor import FrameProcessor
from .config import config

logger = logging.getLogger(__name__)


class ProcessedVideoTrack(VideoStreamTrack):
    """Video track that processes frames through the swap engine."""
    
    def __init__(self, swap_engine: SwapEngine, frame_processor: FrameProcessor, source_track: VideoStreamTrack):
        """
        Initialize processed video track.
        
        Args:
            swap_engine: Swap engine instance
            frame_processor: Frame processor instance
            source_track: Source video track to process
        """
        super().__init__()
        self.swap_engine = swap_engine
        self.frame_processor = frame_processor
        self.source_track = source_track
        self.source_face = None  # Will be set from first frame
        self.frame_count = 0
    
    async def recv(self):
        """Receive and process frame."""
        frame = await self.source_track.recv()
        
        # Convert VideoFrame to numpy array
        img = frame.to_ndarray(format="bgr24")
        
        # Preprocess frame
        img = self.frame_processor.preprocess_frame(img)
        
        # Extract source face on first frame
        if self.source_face is None:
            faces = self.swap_engine.detect_faces(img)
            if faces:
                self.source_face = faces[0]
                logger.info("Source face detected and stored")
        
        # Perform face swap if source face is available
        if self.source_face is not None:
            try:
                img = self.swap_engine.swap_face(
                    source_frame=img,  # Using same frame for now
                    target_frame=img,
                    source_face=self.source_face,
                    target_face=None
                )
            except Exception as e:
                logger.error(f"Face swap error: {e}")
        
        # Postprocess frame
        img = self.frame_processor.postprocess_frame(img)
        
        # Convert back to VideoFrame
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            logger.debug(f"Processed {self.frame_count} frames")
        
        return new_frame


class WebRTCServer:
    """WebRTC server for handling peer connections."""
    
    def __init__(self, swap_engine: SwapEngine, frame_processor: FrameProcessor):
        """
        Initialize WebRTC server.
        
        Args:
            swap_engine: Swap engine instance
            frame_processor: Frame processor instance
        """
        self.swap_engine = swap_engine
        self.frame_processor = frame_processor
        self.pcs = set()  # Set of peer connections
        self.relay = MediaRelay()
    
    async def create_peer_connection(self) -> RTCPeerConnection:
        """Create a new peer connection."""
        pc = RTCPeerConnection()
        self.pcs.add(pc)
        
        @pc.on("track")
        def on_track(track):
            """Handle incoming track."""
            logger.info(f"Received track: {track.kind}")
            
            if track.kind == "video":
                # Create processed video track
                processed_track = ProcessedVideoTrack(
                    self.swap_engine,
                    self.frame_processor,
                    track
                )
                pc.addTrack(processed_track)
                logger.info("Added processed video track")
        
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            """Handle connection state changes."""
            logger.info(f"Connection state: {pc.connectionState}")
            if pc.connectionState in ["failed", "closed"]:
                await pc.close()
                self.pcs.discard(pc)
        
        return pc
    
    async def handle_offer(self, offer_sdp: str) -> str:
        """
        Handle SDP offer and return answer.
        
        Args:
            offer_sdp: SDP offer string
            
        Returns:
            SDP answer string
        """
        pc = await self.create_peer_connection()
        
        # Create offer from SDP
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await pc.setRemoteDescription(offer)
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        logger.info("Created SDP answer")
        return pc.localDescription.sdp
    
    async def close_all(self):
        """Close all peer connections."""
        for pc in self.pcs:
            await pc.close()
        self.pcs.clear()
        logger.info("All peer connections closed")
    
    def get_active_connections(self) -> int:
        """Get number of active connections."""
        return len([pc for pc in self.pcs if pc.connectionState == "connected"])

