import kagglehub

# Download latest version
path = kagglehub.dataset_download("omnamahshivai/dataset-system-resources-cpu-ram-disk-network")

print("Path to dataset files:", path)