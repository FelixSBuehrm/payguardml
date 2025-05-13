---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- generated_from_trainer
- dataset_size:576
- loss:ContrastiveLoss
base_model: sentence-transformers/all-MiniLM-L6-v2
widget:
- source_sentence: 'Invoice from Acme Ltd. (90542) dated 2023-01-29 for 4411.48 CHF.
    PO: PO4241. Cost centre 242162. Tax NP. Terms NET45. Description: IT onboarding.'
  sentences:
  - 'Invoice from Acme Ltd. (90542) dated 2022-08-21 for 33354.61 GBP. PO: PO4644.
    Cost centre 232923. Tax NP. Terms NET30. Description: Data migration.'
  - 'Invoice from Soylent S.A. (24168) dated 2023-03-30 for 27672.63 USD. PO: PO4114.
    Cost centre 296834. Tax TX. Terms NET60. Description: Business strategy.'
  - 'Invoice from Acme Ltd. (90542) dated 2023-12-22 for 10619.10 GBP. PO: PO7658.
    Cost centre 224054. Tax TX. Terms NET30. Description: Business strategy.'
- source_sentence: 'Invoice from Cyberdyne Co. (97017) dated 2022-05-01 for 39592.48
    USD. PO: PO5295. Cost centre 270450. Tax TX. Terms NET30. Description: Consulting
    services.'
  sentences:
  - 'Invoice from Globex S.A. (97875) dated 2024-01-14 for 11186.96 CHF. PO: PO5193.
    Cost centre 224674. Tax VA. Terms NET30. Description: Marketing campaign.'
  - 'Invoice from Cyberdyne Corp (44304) dated 2023-03-30 for 15384.61 CHF. PO: PO4866.
    Cost centre 225934. Tax NP. Terms NET30. Description: IT onboarding.'
  - 'Invoice from Umbrella Co. (20738) dated 2022-12-25 for 41323.59 USD. PO: PO7118.
    Cost centre 294003. Tax VA. Terms NET60. Description: Network maintenance.'
- source_sentence: 'Invoice from Stark Ltd. (66739) dated 2024-01-31 for 33136.76
    EUR. PO: PO4853. Cost centre 235261. Tax TX. Terms NET30. Description: Cloud hosting.'
  sentences:
  - 'Invoice from LexCorp Ltd. (60778) dated 2023-08-24 for 40119.75 EUR. PO: PO8048.
    Cost centre 211241. Tax NP. Terms NET60. Description: Network maintenance.'
  - 'Invoice from Aperture GmbH (79896) dated 2023-01-17 for 35350.38 EUR. PO: PO1344.
    Cost centre 293060. Tax NP. Terms NET60. Description: Cloud hosting.'
  - 'Invoice from Wayne Corporation (63562) dated 2022-04-10 for 48243.63 EUR. PO:
    PO5634. Cost centre 296484. Tax VA. Terms NET45. Description: Software license.'
- source_sentence: 'Invoice from MomCorp Ltd. (78245) dated 2023-11-15 for 24527.19
    GBP. PO: PO3712. Cost centre 213095. Tax NP. Terms NET60. Description: Consulting
    services.'
  sentences:
  - 'Invoice from Black Mesa Co. (24872) dated 2022-08-30 for 17339.44 USD. PO: PO2129.
    Cost centre 235348. Tax VA. Terms NET30. Description: campaign Marketing.'
  - 'Invoice from Gringotts Corporation (94797) dated 2023-04-26 for 4163.14 USD.
    PO: PO5526. Cost centre 277619. Tax TX. Terms NET60. Description: Respond want
    already cut..'
  - 'Invoice from MomCorp LLC (66071) dated 2022-08-18 for 31277.39 GBP. PO: PO5161.
    Cost centre 289099. Tax TX. Terms NET30. Description: Software license.'
- source_sentence: 'Invoice from Initech Corporation (68232) dated 2023-07-11 for
    57089.42 GBP. PO: PO6793. Cost centre 296846. Tax NP. Terms NET45. Description:
    Marketing campaign.'
  sentences:
  - 'Invoice from Acme Ltd. (90542) dated 2023-02-18 for 748.89 EUR. PO: PO1410. Cost
    centre 210598. Tax NP. Terms NET45. Description: Network maintenance.'
  - 'Invoice from Stark LLC (32710) dated 2022-05-25 for 35984.87 GBP. PO: PO3147.
    Cost centre 244748. Tax VA. Terms NET45. Description: Marketing campaign.'
  - 'Invoice from Acme Ltd. (90542) dated 2023-06-16 for 30000.57 USD. PO: PO9317.
    Cost centre 282434. Tax VA. Terms NET60. Description: Marketing campaign.'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
---

# SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) <!-- at revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/UKPLab/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 256, 'do_lower_case': False}) with Transformer model: BertModel 
  (1): Pooling({'word_embedding_dimension': 384, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
  (2): Normalize()
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'Invoice from Initech Corporation (68232) dated 2023-07-11 for 57089.42 GBP. PO: PO6793. Cost centre 296846. Tax NP. Terms NET45. Description: Marketing campaign.',
    'Invoice from Acme Ltd. (90542) dated 2023-06-16 for 30000.57 USD. PO: PO9317. Cost centre 282434. Tax VA. Terms NET60. Description: Marketing campaign.',
    'Invoice from Stark LLC (32710) dated 2022-05-25 for 35984.87 GBP. PO: PO3147. Cost centre 244748. Tax VA. Terms NET45. Description: Marketing campaign.',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities.shape)
# [3, 3]
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 576 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 576 samples:
  |         | sentence_0                                                                         | sentence_1                                                                         | label                                                          |
  |:--------|:-----------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                             | string                                                                             | float                                                          |
  | details | <ul><li>min: 50 tokens</li><li>mean: 55.47 tokens</li><li>max: 66 tokens</li></ul> | <ul><li>min: 50 tokens</li><li>mean: 55.44 tokens</li><li>max: 66 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.17</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                                                                                                                                                | sentence_1                                                                                                                                                             | label            |
  |:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>Invoice from Initech LLC (58118) dated 2022-04-06 for 6294.54 USD. PO: PO2169. Cost centre 274686. Tax TX. Terms NET60. Description: IT onboarding.</code>          | <code>Invoice from Initech LLC (58118) dated 2022-04-06 for 6118.43 USD. PO: PO2169. Cost centre 274686. Tax TX. Terms NET60. Description: IT onboarding.</code>       | <code>1.0</code> |
  | <code>Invoice from MomCorp LLC (66071) dated 2023-11-03 for 829.37 EUR. PO: PO7658. Cost centre 233795. Tax TX. Terms NET60. Description: Marketing campaign.</code>      | <code>Invoice from Globex S.A. (97875) dated 2024-01-14 for 11186.96 CHF. PO: PO5193. Cost centre 224674. Tax VA. Terms NET30. Description: Marketing campaign.</code> | <code>0.0</code> |
  | <code>Invoice from Black Mesa Co. (24872) dated 2023-10-01 for 14880.41 GBP. PO: PO6598. Cost centre 266488. Tax VA. Terms NET60. Description: Marketing campaign.</code> | <code>Invoice from Oscorp Ltd. (71705) dated 2022-09-26 for 56620.10 USD. PO: PO8668. Cost centre 252863. Tax VA. Terms NET60. Description: Marketing campaign.</code> | <code>0.0</code> |
* Loss: [<code>ContrastiveLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#contrastiveloss) with these parameters:
  ```json
  {
      "distance_metric": "SiameseDistanceMetric.COSINE_DISTANCE",
      "margin": 0.5,
      "size_average": true
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `num_train_epochs`: 4
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: no
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 8
- `per_device_eval_batch_size`: 8
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 4
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `use_ipex`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `tp_size`: 0
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: False
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: False
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin

</details>

### Framework Versions
- Python: 3.11.12
- Sentence Transformers: 4.1.0
- Transformers: 4.51.3
- PyTorch: 2.6.0+cu124
- Accelerate: 1.6.0
- Datasets: 2.14.4
- Tokenizers: 0.21.1

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

#### ContrastiveLoss
```bibtex
@inproceedings{hadsell2006dimensionality,
    author={Hadsell, R. and Chopra, S. and LeCun, Y.},
    booktitle={2006 IEEE Computer Society Conference on Computer Vision and Pattern Recognition (CVPR'06)},
    title={Dimensionality Reduction by Learning an Invariant Mapping},
    year={2006},
    volume={2},
    number={},
    pages={1735-1742},
    doi={10.1109/CVPR.2006.100}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->