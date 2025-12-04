
# 📘 **GPU Node – README**

## 🚀 Overview
The **GPU Node** is the real-time face-swapping engine that runs inside a GPU-enabled Docker container.  
Each node receives video frames from the frontend (via WebRTC), performs face swapping on GPU, and streams processed frames back with minimal latency.

This service is **not** exposed directly to the public.  
The **Orchestrator API** decides when nodes start, stop, and which user connects to which node.

---

## 🧩 Responsibilities

The GPU Node handles:

### **1. Real-Time Frame Processing**
- Receives video stream from the frontend (WebRTC)  
- Performs face detection, embedding, alignment  
- Applies real-time face swapping  
- Sends back processed frames  

### **2. WebRTC Server**
- Accepts incoming video tracks  
- Sends back processed video tracks  
- Manages ICE, SDP, and network transport  
- Works on both LAN and WAN networks  

### **3. GPU-Accelerated Swap Engine**
- Runs InsightFace / DeepFaceLive models  
- Utilizes CUDA cores for fast processing  
- Converts frames to GPU tensors  
- Holds models in GPU memory for multiple frames  

### **4. Health & Status Reporting**
- Provides a small HTTP API for health checks  
- Reports GPU usage, memory load, and model info  
- Communicates availability to the Orchestrator  

---

## 🏗 Project Structure

```
gpu-node/
│
├── src/
│   ├── webrtc_server.py     → WebRTC handling (aiortc)
│   ├── swap_engine.py       → core face-swapping logic
│   ├── frame_processor.py   → pre/post-processing pipeline
│   ├── signaling_client.py  → receives signaling from orchestrator
│   └── config.py            → environment variables & settings
│
├── models/                  → InsightFace/DeepFaceLive models
│
├── Dockerfile               → builds GPU-enabled container
└── README.md
```

---

## ⚙️ How It Works (High-Level)

### **1. Node starts inside Docker**
The orchestrator launches this container on demand, usually with:
- NVIDIA runtime  
- Model paths mounted  
- Ports exposed for WebRTC + health  

---

### **2. Node boots the WebRTC server**
The server waits for a signaling message from the orchestrator:
- SDP offer arrives  
- Node creates SDP answer  
- ICE candidates exchanged  

After signaling completes, a direct WebRTC connection forms.

---

### **3. Frontend streams raw frames**
Browser → WebRTC → GPU Node  
The node receives each frame:
- converts to ndarray  
- sends to GPU  
- processes through swap engine  
- returns swapped frame  

All within **30–60 ms latency** per frame (GPU dependent).

---

### **4. Node reports health**
The node exposes `/health` for the orchestrator:
- GPU memory  
- GPU temperature  
- model loaded  
- active session count  
- node status  

If health degrades, the orchestrator can:
- restart node  
- migrate sessions  
- shut node down  

---

## 🔌 API Endpoints (Internal Use)

### **GET /health**
Returns basic status:
```
{
  "status": "ok",
  "gpu": "NVIDIA A40",
  "memory_used": 2143,
  "model": "insightface"
}
```

---

### **POST /configure**
Allows orchestrator to set model or swap settings.

---

### **POST /signaling/offer**
Receives SDP offer from the orchestrator → returns SDP answer.

WebRTC handshake:
- Orchestrator forwards browser offer → GPU node  
- GPU node returns answer → Orchestrator → browser  

After that, video flows directly between browser ↔ node.

---

## 🔧 Requirements

This service requires **GPU**.

### Local Requirements:
- NVIDIA GPU  
- CUDA + cuDNN installed  
- Docker with NVIDIA container runtime  
- Python 3.10+ (inside container)

### Python libs used inside the container:
- aiortc  
- insightface or DeepFaceLive modules  
- OpenCV  
- numpy  
- fastapi (for health)  

---

## 🐳 Running the GPU Node (Development)

### 1. Install NVIDIA Docker runtime
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

### 2. Build the container
```
docker build -t gpu-node .
```

### 3. Run the container
```
docker run --gpus all -p 8080:8080 gpu-node
```

---

## 📦 Publishing to Docker Hub

### Prerequisites

1. **Login to Docker Hub**
   ```bash
   docker login
   ```
   Enter your Docker Hub username and password when prompted.

2. **Set Docker Hub Username**
   ```bash
   export DOCKERHUB_USERNAME=your-username
   ```

### Building and Pushing (Automated)

Use the provided script for easy building and pushing:

```bash
# Make script executable (if not already)
chmod +x build-and-push.sh

# Build and push with version
./build-and-push.sh 1.0.0
```

The script will:
1. Validate the version format
2. Build the Docker image with all tags
3. Prompt for confirmation before pushing
4. Push all tags to Docker Hub

**Interactive mode** (if version not provided):
```bash
./build-and-push.sh
# Script will prompt for version number
```

## 🚀 Deployment

The GPU Node is usually deployed on:
- RunPod GPU instances  
- Vast.ai  
- AWS EC2 GPU  
- Lambda GPU Cloud  
- Local bare-metal GPU servers  

Nodes are expected to:
- Start quickly  
- Load models once  
- Serve one user session  
- Shut down after idle timeout  

---

## 🎯 Future Enhancements

- TensorRT optimization  
- Multi-face swapping  
- Automatic load balancing with orchestrator  
- Adaptive FPS & resolution  
- Metrics export (Prometheus)  

---

## 📄 License
This project is for educational and personal use.  
Commercial deployment requires ensuring compliance with model and GPU vendor licenses.
