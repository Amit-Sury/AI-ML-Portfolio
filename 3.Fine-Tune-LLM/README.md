# Fine-Tune LLaMA-2 (7B) on Amazon SageMaker

## Overview
This project demonstrates **Supervised Fine-Tuning (SFT)** of a **base LLM** (`meta/llama2-7b-hf`) using **parameter-efficient techniques (LoRA)** on **Amazon SageMaker AI**. 

The objective is to adapt the model to **telecom domain language and reasoning patterns** using instruction-style supervision.

---

## Fine-Tuning Approach
- **Model**: meta/llama2-7b-hf (7B/text generation)
- **Method**: Supervised Fine-Tuning (SFT)
- **Trainer**: Hugging Face TRL `SFTTrainer`
- **Optimization**: PEFT with LoRA adapters to reduce GPU memory and training cost
- **Training Infrastructure**: Amazon Sagemaker
> 💡**Note**: `meta/llama2-7b-hf` is a **gated model** on HuggingFace. Access must be requested and approved, and a valid HuggingFace access token is required to download and fine-tune the model. 

---

## Dataset 
- **Source**: Hugging Face [`netop/TeleQnA`](https://huggingface.co/datasets/netop/TeleQnA)
- **Domain**: 5G domain Q&A
> 💡**Note**: `netop/TeleQnA` is a **gated dataset** on HuggingFace. Access must be requested from original authors and approved to download the dataset. 
---
## Steps to Train on SageMaker
- **Step 1:** Create a HuggingFace access token which is required to download the model and dataset. Token must have atleast read permission. 
- **Step 2:** Update `HF_TOKEN` field in [finetune_Llama2_aws.ipynb](./Fine-Tune-LLM/notebook/finetune_Llama2_aws.ipynb) notebook with huggingface access token and sagemaker IAM `role` field with the correct sagemaker role name. 
- **Step 3:** Login to AWS, go to **Amazon SageMaker AI** and start a notebook instance. Once instance is started, open the jupyter notebook.  
- **Step 4:** In the notebook instance, upload [finetune_Llama2_aws.ipynb](./Fine-Tune-LLM/notebook/finetune_Llama2_aws.ipynb). Use `conda-python3` as kernel.
- **Step 5:** Create a folder `scripts` in the notebook instance and upload scripts [finetune_lora.py](./Fine-Tune-LLM/scripts/finetune_lora.py) & [requirements.txt](./Fine-Tune-LLM/scripts/requirements.txt).  
- **Step 6:** Execute finetune_Llama2_aws.ipynb notebook. 
- **Step 7:** Once done remember to **delete the endpoint** and **stop/delete the notebook instance** to avoid unnecessary charges.
  (Double-check the Endpoints, Model & Notebook page in **Sagemaker** to confirm deletion.)

---

## Training Results
<img width="1536" height="754" alt="graphs" src="https://github.com/user-attachments/assets/24d9e7a9-49d4-4ae0-bebb-a3d95049b946" />

---
## Citation
If you use the TeleQnA dataset, please cite the original authors:

```bibtex
@article{maatouk2025teleqna,
  title={TeleQnA: A Benchmark Dataset to Assess Large Language Models Telecommunications Knowledge},
  author={Maatouk, Ali and Ayed, Fadhel and Piovesan, Nicola and De Domenico, Antonio and Debbah, Merouane and Luo, Zhi-Quan},
  journal={IEEE Network},
  year={2025},
  publisher={IEEE}
}


