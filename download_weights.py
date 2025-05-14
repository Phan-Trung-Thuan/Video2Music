# Kang weights
import gdown

# Download AMT
id_trans = "1mJ4M1UoFm-KKdn2QAmfsXOCKAR18KVe-"
url = f"https://drive.google.com/uc?id={id_trans}"
output_pickle = "C:\Windows\System32\Video2Music\saved_models\AMT/best_loss_weights.pickle"

print("Downloading best_loss_weights.pickle...")
gdown.download(url, output_pickle, quiet=False)

# Download BiGRU
id_trans = "1RmylX6aJQiWtyY_9GxfYT6tcUtm-_fvJ"
url = f"https://drive.google.com/uc?id={id_trans}"
output_pickle = "C:\Windows\System32\Video2Music\saved_models\AMT/best_rmse_weights.pickle"

print("Downloading best_rmse_weights.pickle...")
gdown.download(url, output_pickle, quiet=False)
