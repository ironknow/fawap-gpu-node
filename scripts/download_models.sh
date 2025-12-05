#!/bin/bash
# download_models.sh - Downloads InsightFace models if not present
# This script checks for required models and downloads them if missing
# Note: If download fails, InsightFace will attempt to download models automatically

# Get model directory from environment or use default
MODEL_DIR="${MODEL_PATH:-/workspace/models}"
BUFFALO_DIR="$MODEL_DIR/.insightface/models/buffalo_l"

echo "=========================================="
echo "Checking and downloading InsightFace models"
echo "=========================================="
echo "Model directory: $MODEL_DIR"
echo ""

# Create model directories
mkdir -p "$MODEL_DIR"
mkdir -p "$BUFFALO_DIR"

# Function to check if file exists and has content
check_file() {
    if [ -f "$1" ] && [ -s "$1" ]; then
        return 0  # File exists and has content
    else
        return 1  # File doesn't exist or is empty
    fi
}

# Download inswapper_128.onnx if not exists
INSWAPPER_FILE="$MODEL_DIR/inswapper_128.onnx"
if check_file "$INSWAPPER_FILE"; then
    echo "✓ inswapper_128.onnx already exists ($(du -h "$INSWAPPER_FILE" | cut -f1))"
else
    echo "Downloading inswapper_128.onnx..."
    
    # Try multiple download sources
    DOWNLOADED=false
    
    if command -v wget &> /dev/null; then
        echo "  Trying source 1: GitHub releases..."
        if wget -q --show-progress \
            https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx \
            -O "$INSWAPPER_FILE" 2>&1; then
            DOWNLOADED=true
        else
            echo "  Trying source 2: HuggingFace..."
            if wget -q --show-progress \
                https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx \
                -O "$INSWAPPER_FILE" 2>&1; then
                DOWNLOADED=true
            fi
        fi
    elif command -v curl &> /dev/null; then
        echo "  Trying source 1: GitHub releases..."
        if curl -L --progress-bar \
            https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx \
            -o "$INSWAPPER_FILE" 2>&1; then
            DOWNLOADED=true
        else
            echo "  Trying source 2: HuggingFace..."
            if curl -L --progress-bar \
                https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx \
                -o "$INSWAPPER_FILE" 2>&1; then
                DOWNLOADED=true
            fi
        fi
    else
        echo "⚠ Warning: Neither wget nor curl is available"
        echo "  InsightFace will attempt to download models automatically"
        DOWNLOADED=false
    fi
    
    if [ "$DOWNLOADED" = true ] && check_file "$INSWAPPER_FILE"; then
        echo "✓ inswapper_128.onnx downloaded successfully ($(du -h "$INSWAPPER_FILE" | cut -f1))"
    else
        echo "⚠ Warning: Failed to download inswapper_128.onnx"
        echo "  InsightFace will attempt to download it automatically on first run"
        # Don't exit - let the app try to handle it
    fi
fi

# Check for buffalo_l models
BUFFALO_FILES=(
    "det_10g.onnx"
    "genderage.onnx"
    "w600k_r50.onnx"
)

BUFFALO_COMPLETE=true
for file in "${BUFFALO_FILES[@]}"; do
    if ! check_file "$BUFFALO_DIR/$file"; then
        BUFFALO_COMPLETE=false
        break
    fi
done

if [ "$BUFFALO_COMPLETE" = true ]; then
    echo "✓ Buffalo_L models already exist"
else
    echo "ℹ Note: Buffalo_L models will be auto-downloaded by InsightFace on first run"
    echo "  Expected location: $BUFFALO_DIR"
    echo "  (InsightFace handles this automatically, no manual download needed)"
fi

# Display summary
echo ""
echo "=========================================="
echo "Model Check Summary"
echo "=========================================="
echo "Model directory: $MODEL_DIR"
echo ""
echo "Files in model directory:"
if [ "$(ls -A $MODEL_DIR 2>/dev/null)" ]; then
    ls -lh "$MODEL_DIR" | grep -v "^total" || true
else
    echo "  (directory empty)"
fi

echo ""
echo "Buffalo_L directory:"
if [ -d "$BUFFALO_DIR" ] && [ "$(ls -A $BUFFALO_DIR 2>/dev/null)" ]; then
    ls -lh "$BUFFALO_DIR" | grep -v "^total" || true
else
    echo "  (will be created by InsightFace on first run)"
fi
echo "=========================================="
echo ""

