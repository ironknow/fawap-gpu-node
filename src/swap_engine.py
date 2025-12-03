"""
GPU-accelerated face swapping engine.
Uses InsightFace or DeepFaceLive models for real-time face swapping.
"""
import cv2
import numpy as np
import torch
from typing import Optional, Tuple, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SwapEngine:
    """Core face-swapping engine using GPU acceleration."""
    
    def __init__(self, model_path: str, model_type: str = "insightface", gpu_id: int = 0):
        """
        Initialize the swap engine.
        
        Args:
            model_path: Path to model directory
            model_type: Type of model ('insightface' or 'deepfacelive')
            gpu_id: GPU device ID
        """
        self.model_path = Path(model_path)
        self.model_type = model_type
        self.device = torch.device(f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.face_analyzer = None
        self.swapper = None
        
        logger.info(f"Initializing SwapEngine on device: {self.device}")
        self._load_model()
    
    def _load_model(self):
        """Load the face swapping model."""
        try:
            if self.model_type == "insightface":
                self._load_insightface()
            elif self.model_type == "deepfacelive":
                self._load_deepfacelive()
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
            
            logger.info(f"Model loaded successfully: {self.model_type}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _load_insightface(self):
        """Load InsightFace model."""
        try:
            import insightface
            
            # Load face analyzer for detection and alignment
            self.face_analyzer = insightface.app.FaceAnalysis(
                name='buffalo_l',
                root=str(self.model_path),
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            self.face_analyzer.prepare(ctx_id=0 if self.device.type == 'cuda' else -1, det_size=(640, 640))
            
            # Load face swapper
            self.swapper = insightface.model_zoo.get_model(
                str(self.model_path / "inswapper_128.onnx"),
                download=False,
                download_zip=False
            )
            
            if self.device.type == 'cuda':
                # Move to GPU if available
                self.swapper.prepare(ctx_id=0)
            
            logger.info("InsightFace model loaded")
        except ImportError:
            logger.warning("InsightFace not available, using fallback")
            self._load_fallback()
    
    def _load_deepfacelive(self):
        """Load DeepFaceLive model."""
        try:
            # DeepFaceLive typically uses ONNX models
            # This is a placeholder - actual implementation depends on DeepFaceLive structure
            logger.warning("DeepFaceLive loading not fully implemented, using fallback")
            self._load_fallback()
        except Exception as e:
            logger.error(f"Failed to load DeepFaceLive: {e}")
            self._load_fallback()
    
    def _load_fallback(self):
        """Fallback model loader for basic face detection."""
        logger.info("Using fallback face detection (OpenCV DNN)")
        # Load OpenCV DNN face detector as fallback
        prototxt_path = self.model_path / "deploy.prototxt"
        model_path = self.model_path / "res10_300x300_ssd_iter_140000.caffemodel"
        
        if prototxt_path.exists() and model_path.exists():
            self.face_detector = cv2.dnn.readNetFromCaffe(
                str(prototxt_path),
                str(model_path)
            )
            if self.device.type == 'cuda':
                self.face_detector.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.face_detector.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        else:
            logger.warning("Fallback model files not found, face detection may be limited")
            self.face_detector = None
    
    def detect_faces(self, frame: np.ndarray) -> List[dict]:
        """
        Detect faces in a frame.
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            List of face dictionaries with bounding boxes and landmarks
        """
        if self.face_analyzer is not None:
            # Use InsightFace analyzer
            faces = self.face_analyzer.get(frame)
            return [
                {
                    'bbox': face.bbox.astype(int),
                    'landmark': face.landmark_2d_106,
                    'embedding': face.embedding,
                    'det_score': face.det_score
                }
                for face in faces
            ]
        elif self.face_detector is not None:
            # Use OpenCV DNN fallback
            h, w = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)), 1.0,
                (300, 300), [104, 117, 123]
            )
            self.face_detector.setInput(blob)
            detections = self.face_detector.forward()
            
            faces = []
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    faces.append({
                        'bbox': box.astype(int),
                        'det_score': confidence
                    })
            return faces
        else:
            # Basic fallback using OpenCV Haar cascades
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces_detected = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            return [
                {
                    'bbox': np.array([x, y, x+w, y+h]),
                    'det_score': 1.0
                }
                for (x, y, w, h) in faces_detected
            ]
    
    def swap_face(
        self,
        source_frame: np.ndarray,
        target_frame: np.ndarray,
        source_face: Optional[dict] = None,
        target_face: Optional[dict] = None
    ) -> np.ndarray:
        """
        Perform face swap between source and target frames.
        
        Args:
            source_frame: Frame containing the face to swap FROM
            target_frame: Frame containing the face to swap TO
            source_face: Optional pre-detected source face
            target_face: Optional pre-detected target face
            
        Returns:
            Swapped frame
        """
        if self.swapper is None:
            logger.warning("Swapper model not loaded, returning original frame")
            return target_frame
        
        # Detect faces if not provided
        if source_face is None:
            source_faces = self.detect_faces(source_frame)
            if not source_faces:
                return target_frame
            source_face = source_faces[0]
        
        if target_face is None:
            target_faces = self.detect_faces(target_frame)
            if not target_faces:
                return target_frame
            target_face = target_faces[0]
        
        try:
            # Perform swap using InsightFace
            if self.swapper is not None and hasattr(self.swapper, 'get'):
                result = self.swapper.get(target_frame, target_face, source_frame, source_face)
                return result
            else:
                # Fallback: simple overlay (not a real swap, just for testing)
                logger.warning("Using fallback swap method")
                return self._fallback_swap(source_frame, target_frame, source_face, target_face)
        except Exception as e:
            logger.error(f"Face swap failed: {e}")
            return target_frame
    
    def _fallback_swap(
        self,
        source_frame: np.ndarray,
        target_frame: np.ndarray,
        source_face: dict,
        target_face: dict
    ) -> np.ndarray:
        """Fallback swap method (basic implementation)."""
        # This is a placeholder - real implementation would use proper face swapping
        return target_frame
    
    def get_gpu_memory_usage(self) -> dict:
        """Get current GPU memory usage."""
        if torch.cuda.is_available():
            return {
                'allocated': torch.cuda.memory_allocated(self.device) / 1024**3,  # GB
                'reserved': torch.cuda.memory_reserved(self.device) / 1024**3,  # GB
                'max_allocated': torch.cuda.max_memory_allocated(self.device) / 1024**3  # GB
            }
        return {'allocated': 0, 'reserved': 0, 'max_allocated': 0}

