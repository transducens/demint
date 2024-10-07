# Run Kind Teacher Server


## Create environment

```bash
conda env create -f environment.yml

conda activate llamafactory_env

bash init.sh
```


## Run server

```bash
{CUDA_VISIBLE_DEVICES=0} llamafactory-cli api run_api_inference_1.yaml
```

Port and address of the server can be modified in "src/api.py"

