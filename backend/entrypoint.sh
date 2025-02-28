#!/bin/bash

if [ -f "/usr/local/cuda/version.txt" ]; then
    echo "✅ CUDA è già installata, salto l'installazione."
    exit 0
fi

echo "🔍 Controllo se CUDA è disponibile..."

# 1️⃣ Trova la versione corretta di CUDA
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
elif [ -f "/usr/local/cuda/version.txt" ]; then
    CUDA_VERSION=$(cat /usr/local/cuda/version.txt | grep -oE '[0-9]+\.[0-9]+')
elif command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
else
    CUDA_VERSION="cpu"
fi

# Estrai solo i primi due numeri della versione (es. 12.2 -> 12.2)
CUDA_VERSION_SHORT=$(echo $CUDA_VERSION | cut -d. -f1,2)

# Mappiamo la versione CUDA con quella supportata da PyTorch
case $CUDA_VERSION_SHORT in
    "12.2") PYTORCH_CUDA_VERSION="cu121" ;;  # Non esiste cu122, quindi usiamo cu121
    "12.3"|"12.4") PYTORCH_CUDA_VERSION="cu123" ;;  # Se maggiore di 12.3, usiamo cu123
    "12.1") PYTORCH_CUDA_VERSION="cu121" ;;  # CUDA 12.1 esiste direttamente
    "11.8") PYTORCH_CUDA_VERSION="cu118" ;;  # CUDA 11.8 esiste direttamente
    "11.7") PYTORCH_CUDA_VERSION="cu117" ;;  # CUDA 11.7 esiste direttamente
    *) PYTORCH_CUDA_VERSION="cpu" ;;  # Se non è una di queste, usa CPU
esac

echo "✅ CUDA trovata: Versione $CUDA_VERSION_SHORT -> Mappata a PyTorch: $PYTORCH_CUDA_VERSION"

# 3️⃣ Installa PyTorch per CUDA corretta o CPU
echo "🖥️ Verifica dell'installazione di PyTorch..."

if python3 -c "import torch" &> /dev/null; then
    echo "✅ PyTorch è già installato, nessuna reinstallazione necessaria."
else
    if [ "$PYTORCH_CUDA_VERSION" != "cpu" ]; then
        echo "🖥️ Installazione PyTorch per CUDA $CUDA_VERSION_SHORT (Indice: $PYTORCH_CUDA_VERSION)..."
        
        # Controlliamo se l'URL della versione esiste prima di installare
        if curl --output /dev/null --silent --head --fail "https://download.pytorch.org/whl/$PYTORCH_CUDA_VERSION/"; then
            if pip install --no-cache-dir torch --index-url "https://download.pytorch.org/whl/$PYTORCH_CUDA_VERSION"; then
                echo "✅ PyTorch installato correttamente con supporto CUDA $CUDA_VERSION_SHORT!"
            else
                echo "❌ ERRORE: Installazione di PyTorch per CUDA fallita!"
                exit 1
            fi
        else
            echo "❌ ERRORE: L'index-url per PyTorch CUDA $PYTORCH_CUDA_VERSION non esiste. Installazione fallback su CPU."
            PYTORCH_CUDA_VERSION="cpu"
        fi
    fi

    # Se CUDA non è disponibile o se l'installazione CUDA è fallita, installiamo PyTorch per CPU
    if [ "$PYTORCH_CUDA_VERSION" = "cpu" ]; then
        echo "⚠️ Nessun supporto CUDA trovato. Installazione PyTorch per CPU..."
        if pip install --no-cache-dir torch --index-url "https://download.pytorch.org/whl/cpu"; then
            echo "✅ PyTorch per CPU installato correttamente!"
        else
            echo "❌ ERRORE: Installazione di PyTorch per CPU fallita!"
            exit 1
        fi
    fi
fi

# 4️⃣ **Crea il file flag per indicare che CUDA è stata installata**
echo "$CUDA_VERSION_SHORT" > /usr/local/cuda/version.txt

# 4️⃣ **Test finale: verifica se PyTorch riconosce CUDA**
echo "🔍 Verifica se PyTorch riconosce CUDA..."
python3 -c "import torch; cuda_available = torch.cuda.is_available(); gpu_name = torch.cuda.get_device_name(0) if cuda_available else 'Nessuna GPU trovata'; print(f'✅ torch.cuda.is_available(): {cuda_available}'); print(f'🖥️ GPU: {gpu_name}')"

if [ $? -ne 0 ]; then
    echo "❌ ERRORE: PyTorch non riconosce CUDA!"
    exit 1
fi

echo "✅ Setup completato con successo!"