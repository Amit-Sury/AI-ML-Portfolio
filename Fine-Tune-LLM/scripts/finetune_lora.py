
#Import required packages
import argparse
import os
import torch
from trl import SFTConfig, SFTTrainer
from peft import LoraConfig, AutoPeftModelForCausalLM
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_from_disk
import pandas as pd
from torch.utils.data import DataLoader          # Utility to batch and iterate over the dataset

############### Functions block BEGIN ########################

#### Get parameter function BEGIN ####
def get_parameters():
    """Get arguments passed to script"""
    
    parser = argparse.ArgumentParser()

    #model names passed as arguments
    parser.add_argument('--model-name', type=str, default='meta-llama/Llama-2-7b-hf')    

    #hyperparameters passed as arguments
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--learning-rate', type=float, default=5e-5)
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--max-steps', type=int, default=230)
    parser.add_argument('--eval-range', type=int, default=100)
    
    
    #Get directories provided by SageMaker
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--train-dir', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    parser.add_argument('--eval-dir', type=str, default=os.environ['SM_CHANNEL_VALIDATION'])

    args, _ = parser.parse_known_args()

    model_name  = args.model_name
    model_output_dir  = args.model_dir 
    training_dir   = args.train_dir
    validation_dir = args.eval_dir
    eval_range = args.eval_range

    sft_config = {
        # Model and data
        "output_dir"                    : "/opt/ml/tmp/model",
        "dataset_text_field"            : None,
        "max_length"                    : 384,

        # Training hyperparameters
        "per_device_train_batch_size"   : args.batch_size,
        "per_device_eval_batch_size"    : args.batch_size,
        "gradient_accumulation_steps"   : 8,
        "learning_rate"                 : args.learning_rate,
        "num_train_epochs"              : args.epochs,  
        "max_steps"                     : args.max_steps,  # Limit steps. Training stops after this.
        #"packing"                       : True,

        # Optimization
        "warmup_steps"                  : 50,
        "weight_decay"                  : 0.01,
        "optim"                         : "paged_adamw_8bit",

        # Evaluation
        "eval_strategy"                 : "steps",
        "eval_steps"                    : 10, #after every 10 steps, trainer evaluates the model with evaluation dataset
        "do_eval"                       : True,
        
        # Logging and saving
        "logging_steps"                 : 10, #after every 10 steps the logging will be done. 
        "save_steps"                    : 50, #after every 50 steps, model's weights will be store. 
        "save_total_limit"              : 5, #how many checkpoints shall be saved on the disc in output directory

        # Memory optimization
        "dataloader_num_workers"        : 0,
        "group_by_length"               : False,  # Group similar length sequences
        "bf16"                          : False,
        "fp16"                          : True,

        #logs are reported to
        "report_to"                     : "none",
    }

    return model_name, model_output_dir, training_dir, validation_dir, sft_config, eval_range 
#### Get parameter function END ####

#### Load model function BEGIN ####
def load_model(model_name):
    """This function loads the model weights"""
    #Load the model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    return model
#### Load model function END ####

#### Set training parameters function BEGIN ####
def set_training_hyperparameters(model, sft_config):
    """This function sets training hyperparameters"""

    #set SFTConfig
    model.gradient_checkpointing_enable()
    model.config.use_cache = False
    training_config = SFTConfig(**sft_config) 

    #set LoRAconfig
    peft_config = LoraConfig(
        r=4,                    #reduced from earlier 8 to reduce memorization, keep adaptation
        lora_alpha=8,           #reduced from earlier 16 to reduce memorization, keep adaptation
        lora_dropout=0.1,       #increased regularization from earlier 0.05 for best fit
        bias="none",
        task_type="CAUSAL_LM",
    )

    return training_config, peft_config
#### Set training parameters function END ####    

#### Model train function BEGIN ####
def model_train(model, training_dir, validation_dir, training_config, peft_config):
    """Train the model"""

    train_dataset = load_from_disk(training_dir)
    eval_dataset = load_from_disk(validation_dir)
    eval_dataset = eval_dataset.select(range(10))

    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=training_config,
        peft_config=peft_config,  # << enable LoRA
    )

    trainer.train()    
    return trainer
#### Model train function END ####

#### Model evaluation function BEGIN ####
def run_eval(model, validation_dir, eval_range):
    """This function does manual evaluation."""

    eval_dataset = load_from_disk(validation_dir)

    eval_dataset.set_format(                        # Convert dataset columns to PyTorch tensors
        type="torch",
        columns=["input_ids", "attention_mask", "labels"]
    )

    eval_dataset = eval_dataset.select(range(eval_range))   # Limit evaluation to range 

    eval_dataloader = DataLoader(                   # Create dataloader for evaluation
        eval_dataset,
        batch_size=1,                               # One sample per forward pass to save memory
        shuffle=False                               # Keep deterministic order
    )

    device = next(model.parameters()).device        # Get the device (CPU/GPU) where the model lives
    model.eval()                                    # Set model to evaluation mode 
    model.config.use_cache = False                  # Disable KV-cache to reduce memory usage
    losses = []                                     # Store per-step loss values

    with torch.no_grad(), torch.autocast("cuda", torch.float16):  # Disables gradients and enables mixed-precision for faster, lower-memory eval.
        for batch in eval_dataloader:                            # Iterate on batch
            batch = {k: v.to(device) for k, v in batch.items()}  # Move batch tensors to model device
            outputs = model(**batch)                             # Runs a forward pass and computes loss.
            losses.append(outputs.loss.item())                   # Extracts and stores the scalar loss value.
            
    return sum(losses) / len(losses)
#### Model evaluation function END ####

#### Model save function BEGIN ####
def model_save(trainer, model_output_dir):
    """This function saves the model to output directory"""

    #save training logs
    log_directory = "/opt/ml/output/data"        
    os.makedirs(log_directory, exist_ok=True)
    df = pd.DataFrame(trainer.state.log_history) 
    df.to_csv(os.path.join(log_directory, "training_logs.csv"), index=False)


    #temp directory for model
    tmp_save_dir = "/opt/ml/tmp/model/final"
    os.makedirs(tmp_save_dir, exist_ok=True)

    #save adapter (temporary)
    print(f"finetune_lora.py: saving adapter to temporary directory {tmp_save_dir}...")
    trainer.model.save_pretrained(tmp_save_dir)
    print("finetune_lora.py: saving adapter to temporary directory completed.")

    #free the memory
    print("finetune_lora.py: deleting trainer and clearing memory...")
    del trainer
    torch.cuda.empty_cache()
    print("finetune_lora.py: deleting trainer and clearing memory completed.")

    #reload PEFT model in FP16
    print("finetune_lora.py: reload PEFT model in FP16...")
    model = AutoPeftModelForCausalLM.from_pretrained(
        tmp_save_dir,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    print("finetune_lora.py: reload PEFT model in FP16 completed.")

    #merge LoRA adapters to base
    print(f"finetune_lora.py: merging and saving model to output directory {model_output_dir}...")
    model = model.merge_and_unload()    
    model.save_pretrained(model_output_dir, safe_serialization=True)
    print("finetune_lora.py: merging and saving model completed.")

    #IMPORTANT: load BASE tokenizer, not trainer tokenizer
    print("finetune_lora.py: loading base tokenizer...")
    base_tokenizer = AutoTokenizer.from_pretrained(
        "meta-llama/Llama-2-7b-hf",
        use_fast=False
    )
    print("finetune_lora.py: saving base tokenizer...")
    base_tokenizer.save_pretrained(model_output_dir)
    print("finetune_lora.py: saving base tokenizer completed.")
#### Model save function END ####

############### Functions block END ##########################

############### Execution block BEGIN ########################
if __name__ == '__main__':

    print(f"finetune_lora.py: script execution is started...")
    
    #Get parameters
    (
        model_name,
        model_output_dir,
        training_dir,
        validation_dir,
        sft_config,
        eval_range
    ) = get_parameters()
    print("finetune_lora.py: Getting training configurations completed.")
    
    #load the model
    print("finetune_lora.py: Loading the model...")
    model = load_model(model_name)
    print("finetune_lora.py: Model loaded successfully.")

    #Set SFT and LoRA Config
    training_config, peft_config = set_training_hyperparameters(model, sft_config)
    print("finetune_lora.py: Training hyperparameters are set.")

    #Train the model
    print("finetune_lora.py: Starting LoRA training...")    
    trainer = model_train(
        model,
        training_dir,
        validation_dir,
        training_config,
        peft_config
        )
    
    #evaluate the model
    #print("finetune_lora.py: Evaluating the model with evaluation dataset")
    #commenting this to leverage on SFTTrainer's evaluation.
    #eval_loss = run_eval(model, validation_dir, eval_range)
    #print(f"finetune_lora.py: EVAL_LOSS={eval_loss}")

    #Save the model
    print("finetune_lora.py: Training completed")
    print("finetune_lora.py: Saving the model...")
    model_save(trainer, model_output_dir)
    print("finetune_lora.py: Saving Completed.")
############### Execution block END ##########################    