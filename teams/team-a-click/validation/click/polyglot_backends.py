"""Native Lighteval/lm-eval adapters and an independent forward check."""

from collections import Counter

from polyglot_core import (
    MODELS,
    SETTINGS,
    digest,
    harness_payload,
    require,
    token_contract,
)


def harness_query(row):
    return harness_payload(row)["query"]


def harness_choices(row):
    return harness_payload(row)["choices"]


def harness_gold(row):
    return harness_payload(row)["gold_index"]


def make_harness_task(category, files):
    from lm_eval.api.task import ConfigurableTask
    from polyglot_core import DATA_REVISION

    return ConfigurableTask(
        config={
            "task": f"click_aligned_{category}",
            "dataset_path": "EunsuKim/CLIcK",
            "dataset_name": "default",
            "dataset_kwargs": {
                "revision": DATA_REVISION,
                "data_files": {"train": list(files)},
            },
            "test_split": "train",
            "num_fewshot": 0,
            "output_type": "multiple_choice",
            "doc_to_text": harness_query,
            "doc_to_choice": harness_choices,
            "doc_to_target": harness_gold,
            "target_delimiter": "",
            "metric_list": [
                {"metric": "acc", "aggregation": "mean", "higher_is_better": True}
            ],
            "metadata": {
                "version": 1,
                "purpose": "team parity reference, not the upstream CLIcK task",
            },
        }
    )


def lighteval_tasks():
    from lighteval.tasks.registry import Registry

    tasks = Registry(tasks="click|0").load_tasks()
    require(len(tasks) == 11, "Expected eleven registered tasks")
    return {name.split(":")[1].split("|")[0]: task for name, task in tasks.items()}


def native_inputs(records):
    """Load through both actual task APIs, verifying all rows without using IDs as keys."""
    from lighteval.tasks.tasks.click import CATEGORY_FILES
    from polyglot_core import RAW_FIELDS

    expected = {(r["category"], r["raw_row_sha256"]): r for r in records}
    require(
        len(expected) == len(records),
        "Ambiguous content hash; file-position loader needed",
    )
    result, counts = {}, Counter()
    for category, task in lighteval_tasks().items():
        for doc in task.get_docs():
            key = (category, doc.specific["raw_row_sha256"])
            require(key in expected, "Unexpected Lighteval document")
            record = expected[key]
            payload = harness_payload(record["raw"])
            require(
                doc.query == payload["query"]
                and doc.choices == payload["choices"]
                and doc.gold_index == payload["gold_index"],
                "Lighteval/reference payload mismatch",
            )
            require(
                not doc.fewshot_samples and not doc.instruction,
                "Unexpected prompt additions",
            )
            result[record["source_key"]] = payload
            counts[record["source_key"]] += 1
    require(
        counts == Counter({r["source_key"]: 1 for r in records}),
        "Lighteval row multiplicity mismatch",
    )
    counts.clear()
    for category, files in CATEGORY_FILES.items():
        task = make_harness_task(category, files)
        for raw in task.test_docs():
            raw_hash = digest({k: raw[k] for k in RAW_FIELDS})
            require((category, raw_hash) in expected, "Unexpected harness document")
            record = expected[category, raw_hash]
            payload = result[record["source_key"]]
            context = task.fewshot_context(raw, num_fewshot=0)
            requests = task.construct_requests(
                raw, context, metadata=(task.config.task, 0, 1)
            )
            require(context == payload["query"], "Harness context mismatch")
            require(
                [request.args for request in requests]
                == [(context, c) for c in payload["choices"]],
                "Harness continuation delimiter mismatch",
            )
            require(
                task.doc_to_target(raw) == payload["gold_index"],
                "Harness gold mismatch",
            )
            counts[record["source_key"]] += 1
    require(
        counts == Counter({r["source_key"]: 1 for r in records}),
        "Harness row multiplicity mismatch",
    )
    return result


class InputAudit:
    """Check every actual model input, allowing only native right-padding.

    The harness/reference omit the final input token (it is a target); Lighteval
    includes it. Both score the same continuation tokens at the same positions.
    """

    def __init__(self, tokens, pad_token_id, omit_last):
        self.expected = [tokens["context"] + c for c in tokens["continuations"]]
        if omit_last:
            self.expected = [row[:-1] for row in self.expected]
        self.pad = pad_token_id
        self.seen = set()

    def __call__(self, module, args, kwargs):
        value = kwargs.get("input_ids")
        if value is None:
            require(bool(args), "Model input_ids missing")
            value = args[0]
        for actual in value.detach().cpu().tolist():
            matches = [
                i
                for i, expected in enumerate(self.expected)
                if actual[: len(expected)] == expected
                and all(t == self.pad for t in actual[len(expected) :])
            ]
            require(
                matches, "Actual model input differs (BOS, truncation, or tokenization)"
            )
            self.seen.update(matches)

    def complete(self):
        require(
            self.seen == set(range(len(self.expected))),
            "Not every continuation reached the model",
        )


def configure_torch():
    import torch

    torch.manual_seed(SETTINGS["seed"])
    torch.set_grad_enabled(False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision("highest")


class Backend:
    def __init__(
        self, engine, size, output_dir, *, model=None, tokenizer=None, device="cuda"
    ):
        import torch
        from lighteval.tasks.tasks.click import CATEGORY_FILES
        from transformers import AutoModelForCausalLM, AutoTokenizer

        configure_torch()
        self.engine, self.device = engine, device
        repo, revision = MODELS[size]
        self.tokenizer = tokenizer or AutoTokenizer.from_pretrained(
            repo, revision=revision, trust_remote_code=False
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = (
            model
            if model is not None
            else AutoModelForCausalLM.from_pretrained(
                repo,
                revision=revision,
                torch_dtype=torch.float32,
                attn_implementation="eager",
                trust_remote_code=False,
            )
        )
        self.model.to(device).eval()
        require(
            next(self.model.parameters()).dtype == torch.float32, "Expected FP32 model"
        )
        if engine == "lighteval":
            from lighteval.models.transformers.transformers_model import (
                TransformersModel,
                TransformersModelConfig,
            )

            config = TransformersModelConfig(
                model_name=repo,
                revision=revision,
                dtype="float32",
                device=device,
                model_parallel=False,
                batch_size=1,
                max_length=2048,
                override_chat_template=False,
                add_special_tokens=False,
                pairwise_tokenization=True,
                cache_dir=str(output_dir / "unused-native-cache"),
                model_loading_kwargs={"attn_implementation": "eager"},
            )
            self.adapter = TransformersModel.from_model(self.model, config)
            self.tasks = lighteval_tasks()
            # Real registered loader and get_docs, including the library's shuffle.
            self.documents = {}
            for category, task in self.tasks.items():
                for doc in task.get_docs():
                    key = category, doc.specific["raw_row_sha256"]
                    require(key not in self.documents, "Ambiguous native Lighteval doc")
                    self.documents[key] = doc
        elif engine == "harness":
            from lm_eval.models.huggingface import HFLM

            self.adapter = HFLM(
                pretrained=self.model,
                tokenizer=self.tokenizer,
                backend="causal",
                device=device,
                dtype="float32",
                softmax_dtype="float32",
                batch_size=1,
                max_length=2048,
                add_bos_token=False,
                logits_cache=False,
                truncation=False,
            )
            self.tasks = {
                c: make_harness_task(c, files) for c, files in CATEGORY_FILES.items()
            }
        else:
            require(engine == "reference", "Unknown engine")

    def score(self, record, payload):
        import torch

        tokens = token_contract(self.tokenizer, payload)
        audit = InputAudit(
            tokens, self.tokenizer.pad_token_id, omit_last=self.engine != "lighteval"
        )
        hook = self.model.register_forward_pre_hook(audit, with_kwargs=True)
        try:
            with torch.inference_mode():
                if self.engine == "lighteval":
                    doc = self.documents[record["category"], record["raw_row_sha256"]]
                    require(
                        self.adapter.prompt_manager.prepare_prompt(doc)
                        == payload["query"],
                        "Runtime Lighteval prompt differs",
                    )
                    require(
                        doc.choices == payload["choices"]
                        and doc.gold_index == payload["gold_index"],
                        "Runtime Lighteval choices/gold differ",
                    )
                    # The actual uncached native inference method, not a reimplementation.
                    response = self.adapter._loglikelihood_tokens([doc])[0]
                    scores = response.logprobs
                    correct = (
                        self.tasks[record["category"]]
                        .metrics[0]
                        .sample_level_fn.compute(doc, response)
                    )
                elif self.engine == "harness":
                    task, raw = self.tasks[record["category"]], record["raw"]
                    context = task.fewshot_context(raw, num_fewshot=0)
                    requests = task.construct_requests(
                        raw,
                        context,
                        metadata=(task.config.task, record["row_number"], 1),
                    )
                    require(
                        [r.args for r in requests]
                        == [(payload["query"], c) for c in payload["choices"]],
                        "Runtime harness requests differ",
                    )
                    responses = self.adapter.loglikelihood(requests, disable_tqdm=True)
                    scores = [r[0] for r in responses]
                    correct = task.process_results(raw, responses)["acc"]
                else:
                    scores = []
                    for continuation in tokens["continuations"]:
                        whole = tokens["context"] + continuation
                        inputs = torch.tensor([whole[:-1]], device=self.device)
                        logits = (
                            self.model(input_ids=inputs, use_cache=False)
                            .logits[0]
                            .float()
                        )
                        # Position context_length-1 predicts the first candidate token.
                        start = len(tokens["context"]) - 1
                        selected = logits[start : start + len(continuation)]
                        targets = torch.tensor(continuation, device=self.device)
                        scores.append(
                            torch.log_softmax(selected, dim=-1)
                            .gather(1, targets[:, None])
                            .sum()
                            .item()
                        )
                    correct = int(
                        max(range(len(scores)), key=lambda i: scores[i])
                        == payload["gold_index"]
                    )
        finally:
            hook.remove()
        audit.complete()
        return [float(s) for s in scores], int(correct), tokens
