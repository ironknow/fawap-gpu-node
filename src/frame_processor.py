"""
Frame processing pipeline for pre and post-processing.
Handles frame conversion, normalization, and format transformations.
"""
import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FrameProcessor:
    """Handles frame preprocessing and postprocessing."""
    
    def __init__(self, target_size: Optional[Tuple[int, int]] = None):
        """
        Initialize frame processor.
        
        Args:
            target_size: Optional target size for frames (width, height)
        """
        self.target_size = target_size
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame before face swapping.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Preprocessed frame
        """
        # Resize if target size is specified
        if self.target_size:
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_LINEAR)
        
        # Ensure frame is in BGR format
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        return frame
    
    def postprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Postprocess frame after face swapping.
        
        Args:
            frame: Processed frame (BGR format)
            
        Returns:
            Postprocessed frame
        """
        # Ensure frame is valid
        if frame is None or frame.size == 0:
            logger.warning("Empty frame received in postprocess")
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Clip values to valid range
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
    def rgb_to_bgr(self, frame: np.ndarray) -> np.ndarray:
        """Convert RGB frame to BGR."""
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame
    
    def bgr_to_rgb(self, frame: np.ndarray) -> np.ndarray:
        """Convert BGR frame to RGB."""
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
    
    def resize_frame(
        self,
        frame: np.ndarray,
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: Optional[float] = None
    ) -> np.ndarray:
        """
        Resize frame maintaining aspect ratio.
        
        Args:
            frame: Input frame
            width: Target width
            height: Target height
            scale: Scale factor
            
        Returns:
            Resized frame
        """
        h, w = frame.shape[:2]
        
        if scale:
            new_w = int(w * scale)
            new_h = int(h * scale)
        elif width and height:
            new_w, new_h = width, height
        elif width:
            new_h = int(h * (width / w))
            new_w = width
        elif height:
            new_w = int(w * (height / h))
            new_h = height
        else:
            return frame
        
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    def normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Normalize frame to [0, 1] range.
        
        Args:
            frame: Input frame
            
        Returns:
            Normalized frame
        """
        return frame.astype(np.float32) / 255.0
    
    def denormalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Denormalize frame from [0, 1] to [0, 255].
        
        Args:
            frame: Normalized frame
            
        Returns:
            Denormalized frame
        """
        return (frame * 255.0).astype(np.uint8)
    
    def frame_to_tensor(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert frame to tensor format (HWC -> CHW).
        
        Args:
            frame: Input frame (H, W, C)
            
        Returns:
            Tensor format (C, H, W)
        """
        if len(frame.shape) == 3:
            return np.transpose(frame, (2, 0, 1))
        return frame
    
    def tensor_to_frame(self, tensor: np.ndarray) -> np.ndarray:
        """
        Convert tensor to frame format (CHW -> HWC).
        
        Args:
            tensor: Input tensor (C, H, W)
            
        Returns:
            Frame format (H, W, C)
        """
        if len(tensor.shape) == 3:
            return np.transpose(tensor, (1, 2, 0))
        return tensor

