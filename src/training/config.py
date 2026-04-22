"""
config.py
Configuración central del fine-tuning QLoRA para el chatbot GM.
Todos los hiperparámetros en un solo lugar para fácil experimentación.
"""

from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    # Modelo base — empezar con 8B para pruebas, escalar a 70B para producción
    model_name: str = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
    # model_name: str = "unsloth/Meta-Llama-3.1-70B-Instruct-bnb-4bit"  # Producción

    max_seq_length: int = 4096   # Contexto máximo — los BPs pueden ser largos
    load_in_4bit: bool = True    # QLoRA: cuantización 4-bit para ahorrar VRAM
    dtype = None                 # Autodetectar (float16 en T4, bfloat16 en A100)


@dataclass
class LoRAConfig:
    r: int = 32                  # Rank de LoRA — 16/32 para dominio específico
    lora_alpha: int = 32         # Alpha = r para ratio 1:1 (estable)
    lora_dropout: float = 0.05   # Pequeño dropout para evitar overfitting
    bias: str = "none"
    use_gradient_checkpointing: str = "unsloth"
    random_state: int = 42
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])


@dataclass
class TrainingConfig:
    # Dataset
    dataset_path: str = "data/qa_pairs/gm_qa_dataset.jsonl"
    chat_template: str = "llama-3"

    # Entrenamiento
    num_train_epochs: int = 3        # 3 epochs para dominio específico
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 8   # Batch efectivo = 2 * 8 = 16
    warmup_ratio: float = 0.05
    learning_rate: float = 2e-4
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    seed: int = 42
    fp16: bool = False             # False si la GPU soporta bfloat16
    bf16: bool = True              # True para A100/H100, False para T4

    # Logging y guardado
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    output_dir: str = "models/checkpoints"
    report_to: str = "wandb"       # Cambiar a "none" si no tienen W&B

    # Optimizador
    optim: str = "adamw_8bit"      # 8-bit Adam ahorra VRAM adicional


@dataclass
class ExportConfig:
    # Rutas de exportación
    lora_output: str = "models/gm-llama3-lora"
    merged_output: str = "models/gm-llama3-merged"
    gguf_output: str = "models/gm-llama3-gguf"

    # Cuantización GGUF para despliegue
    gguf_quantization: list = field(default_factory=lambda: ["q4_k_m", "q8_0"])

    # HuggingFace Hub (opcional)
    push_to_hub: bool = False
    hub_model_id: str = "tu-usuario/gm-llama3-chatbot"   # Cambiar antes de usar


# Instancias listas para importar
model_config = ModelConfig()
lora_config = LoRAConfig()
training_config = TrainingConfig()
export_config = ExportConfig()
