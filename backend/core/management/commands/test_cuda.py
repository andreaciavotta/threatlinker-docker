import torch

def check_cuda():
    print("🔥 Verifica CUDA in corso...")
    if torch.cuda.is_available():
        print(f"✅ CUDA è disponibile! GPU: {torch.cuda.get_device_name(0)}")
        print(f"✅ Numero di GPU disponibili: {torch.cuda.device_count()}")
    else:
        print("❌ CUDA NON è disponibile. Si sta usando solo la CPU.")

if __name__ == "__main__":
    check_cuda()
