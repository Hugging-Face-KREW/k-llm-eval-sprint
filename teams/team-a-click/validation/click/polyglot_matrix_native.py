"""Native task snapshots, transport-only override and audited model execution."""

import copy
import functools
import inspect
import subprocess
import sys
from collections import Counter
from pathlib import Path

from polyglot_core import (
    MODELS,
    RAW_FIELDS,
    digest,
    file_digest,
    require,
    token_contract,
)
from polyglot_matrix_core import (
    BASE_REVISION,
    CONDITIONS,
    PR_REVISION,
    candidate_diagnostics,
    native_gold,
)


def task_snapshots(harness_root, directory, revision_repository=None):
    from polyglot_compare import git, source_state

    state = source_state(harness_root, PR_REVISION, "lm_eval")
    revision_repository = revision_repository or harness_root
    changed = git(
        revision_repository, "diff", "--name-only", BASE_REVISION, PR_REVISION
    ).splitlines()
    require(
        len(changed) == 8
        and all(p.startswith("lm_eval/tasks/click/") for p in changed),
        "Harness core differs between revisions",
    )
    roots, fingerprints = {}, {}
    for version, revision in (("base", BASE_REVISION), ("pr4420", PR_REVISION)):
        root = directory / version / "click"
        files = git(
            revision_repository,
            "ls-tree",
            "-r",
            "--name-only",
            revision,
            "lm_eval/tasks/click",
        ).splitlines()
        hashes = {}
        for name in files:
            relative = Path(name).relative_to("lm_eval/tasks/click")
            target = root / relative
            content = subprocess.check_output(
                ["git", "-C", str(revision_repository), "show", f"{revision}:{name}"]
            )
            if target.exists():
                require(
                    target.read_bytes() == content, "Immutable task snapshot changed"
                )
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                target.chmod(0o444)
            hashes[relative.as_posix()] = file_digest(target)
        require(
            {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
            == set(hashes),
            "Unexpected snapshot files",
        )
        roots[version] = root
        fingerprints[version] = {
            "revision": revision,
            "files": hashes,
            "tree_sha256": digest(hashes),
        }
    sys.path.insert(0, str(harness_root.resolve()))
    sys.dont_write_bytecode = True
    import lm_eval

    require(
        Path(lm_eval.__file__).resolve().is_relative_to(harness_root.resolve()),
        "Wrong harness imported",
    )
    return roots, {
        "runtime_harness": state,
        "changed_files": changed,
        "core_identical": True,
        "tasks": fingerprints,
    }


def config_identity(value):
    if isinstance(value, functools.partial):
        return {
            "function": config_identity(value.func),
            "arguments": [config_identity(x) for x in value.args],
        }
    if callable(value):
        return {
            "name": value.__name__,
            "source_sha256": file_digest(inspect.getsourcefile(value)),
        }
    if isinstance(value, dict):
        return {k: config_identity(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [config_identity(v) for v in value]
    return value


def full_choices(original_choices, raw):
    labels = original_choices(raw)
    require(
        len(labels) == len(raw["choices"]),
        "Native/raw candidate mismatch; cannot silently adapt",
    )
    return [f"{label}. {raw['choices'][i]}" for i, label in enumerate(labels)]


def full_target(original_choices, original_target, raw):
    return native_gold(original_choices(raw), original_target(raw))


def requests_payload(task, raw, row_number=0):
    context = task.fewshot_context(raw, num_fewshot=0)
    requests = task.construct_requests(
        raw, context, metadata=(task.config.task, row_number, 1)
    )
    require(
        context == task.config.doc_to_text(raw),
        "Native fewshot context adds unexpected content",
    )
    choices = task.doc_to_choice(raw)
    target = task.doc_to_target(raw)
    gold = native_gold(choices, target) if isinstance(target, str) else target
    require(
        [r.args for r in requests]
        == [(context, task.config.target_delimiter + c) for c in choices],
        "Native requests mismatch",
    )
    require(
        all(r.request_type == "loglikelihood" for r in requests),
        "Wrong native request type",
    )
    return requests, {
        "query": context,
        "choices": [r.args[1] for r in requests],
        "gold_index": gold,
    }


class NativeTasks:
    def __init__(self, roots, records, transport):
        from lm_eval.api.task import ConfigurableTask
        from lm_eval.tasks._yaml_loader import load_yaml

        self.tasks, self.rows, self.configs = {}, {}, {}
        expected = {r["raw_row_sha256"]: r for r in records}
        require(len(expected) == len(records), "Ambiguous raw provenance")
        diagnostics = []
        for condition in CONDITIONS:
            version, mode = condition.split("_")
            self.tasks[condition], self.rows[condition], self.configs[condition] = (
                {},
                {},
                {},
            )
            counts = Counter()
            paths = sorted(
                p
                for p in roots[version].rglob("*.yaml")
                if p.name.startswith(("click_cul_", "click_lang_"))
            )
            require(len(paths) == 11, "Expected eleven native task YAMLs")
            for path in paths:
                original = load_yaml(path, resolve_func=True)
                cfg = copy.deepcopy(original)
                # Transport only: same pinned raw records/fields, native process_docs is untouched.
                cfg.update(
                    dataset_path="json",
                    dataset_kwargs={"data_files": {"train": str(transport)}},
                    num_fewshot=0,
                )
                label_fn, target_fn = cfg["doc_to_choice"], cfg["doc_to_target"]
                if mode == "full":
                    cfg["doc_to_choice"] = functools.partial(full_choices, label_fn)
                    cfg["doc_to_target"] = functools.partial(
                        full_target, label_fn, target_fn
                    )
                task = ConfigurableTask(config=cfg)
                name = task.config.task
                category = name.split("_")[-1]
                category = {
                    "kpop": "popular",
                    "function": "functional",
                    "text": "textual",
                }.get(category, category)
                self.tasks[condition][category] = task
                identity = {
                    "native_yaml": config_identity(original),
                    "overrides": {
                        "dataset_path": "json",
                        "dataset_kwargs": "private verified transport.jsonl, train split",
                        "num_fewshot": 0,
                    },
                    "full_adapter": mode == "full",
                }
                self.configs[condition][category] = identity
                require(
                    task.config.target_delimiter == " "
                    and task.config.filter_list is None
                    and task.config.repeats == 1,
                    "Unexpected native delimiter/filter/repeats",
                )
                require(
                    set(task._metric_fn_list) == {"acc", "acc_norm"},
                    "Native metrics changed",
                )
                for raw in task.test_docs():
                    raw_hash = digest({k: raw[k] for k in RAW_FIELDS})
                    require(raw_hash in expected, "Unexpected native loader row")
                    record = expected[raw_hash]
                    require(
                        raw == record["raw"], "Transport changed raw content/schema"
                    )
                    labels, target = label_fn(raw), target_fn(raw)
                    diagnostics.extend(candidate_diagnostics(raw, labels, version))
                    gold = native_gold(labels, target)
                    require(
                        gold == raw["choices"].index(raw["answer"]),
                        "Native gold differs from original answer",
                    )
                    _requests, payload = requests_payload(
                        task, raw, record["row_number"]
                    )
                    require(
                        payload["gold_index"] == gold, "Target adapter changed answer"
                    )
                    counts[record["source_key"]] += 1
                    self.rows[condition][record["source_key"]] = {
                        "payload": payload,
                        "native_category": category,
                        "native_task": name,
                        "source_category": record["category"],
                        "native_labels": labels,
                        "native_target": target,
                        "choice_char_lengths": [
                            len(c) for c in task.doc_to_choice(raw)
                        ],
                        "config_sha256": digest(identity),
                    }
            require(
                counts == Counter({r["source_key"]: 1 for r in records}),
                "Native loader missing/duplicate rows",
            )
        self.diagnostics = diagnostics
        require(not diagnostics, f"Native/raw candidate mismatch: {diagnostics}")
        for key in self.rows["base_letter"]:
            for version in ("base", "pr4420"):
                letter, full = (
                    self.rows[version + "_letter"][key],
                    self.rows[version + "_full"][key],
                )
                require(
                    letter["payload"]["query"] == full["payload"]["query"]
                    and letter["payload"]["gold_index"] == full["payload"]["gold_index"]
                    and letter["native_category"] == full["native_category"],
                    "Full overlay changed native prompt/gold/filter",
                )
            if len(self.rows["base_letter"][key]["native_labels"]) == 4:
                for mode in ("letter", "full"):
                    require(
                        self.rows["base_" + mode][key]["payload"]
                        == self.rows["pr4420_" + mode][key]["payload"],
                        "Four-choice version payload differs",
                    )


class MatrixBackend:
    def __init__(self, size, tasks, *, model=None, tokenizer=None, device="cuda"):
        import torch
        from lm_eval.models.huggingface import HFLM
        from polyglot_backends import configure_torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        configure_torch()
        self.device, self.tasks = device, tasks
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
            all(p.dtype == torch.float32 for p in self.model.parameters()),
            "Non-FP32 parameter",
        )
        require(self.model.config._attn_implementation == "eager", "Attention changed")
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

    def score(self, row, condition, reference=False):
        import torch
        from polyglot_backends import InputAudit

        variant = row["variants"][condition]
        task = self.tasks.tasks[condition][variant["native_category"]]
        requests, payload = requests_payload(task, row["raw"], row["row_number"])
        require(payload == variant["payload"], "Runtime native payload differs")
        tokens = token_contract(self.tokenizer, payload)
        audit = InputAudit(tokens, self.tokenizer.pad_token_id, omit_last=True)
        hook = self.model.register_forward_pre_hook(audit, with_kwargs=True)
        try:
            with torch.inference_mode():
                if reference:
                    responses = []
                    for continuation in tokens["continuations"]:
                        whole = tokens["context"] + continuation
                        logits = (
                            self.model(
                                input_ids=torch.tensor(
                                    [whole[:-1]], device=self.device
                                ),
                                use_cache=False,
                            )
                            .logits[0]
                            .float()
                        )
                        start = len(tokens["context"]) - 1
                        selected = logits[start : start + len(continuation)]
                        targets = torch.tensor(continuation, device=self.device)
                        score = (
                            torch.log_softmax(selected, dim=-1)
                            .gather(1, targets[:, None])
                            .sum()
                            .item()
                        )
                        responses.append(
                            (score, bool((selected.argmax(-1) == targets).all().item()))
                        )
                else:
                    responses = self.adapter.loglikelihood(requests, disable_tqdm=True)
        finally:
            hook.remove()
        audit.complete()
        # Apply the original native take_first ensemble, then native metric calculation.
        for request, response in zip(requests, responses, strict=True):
            request.resps = [response]
        task._instances = requests
        task.apply_filters()
        filtered = [r.filtered_resps["none"] for r in requests]
        require(filtered == responses, "Unexpected native filter output")
        metrics = task.process_results(row["raw"], filtered)
        task._instances = []
        scores = [float(x[0]) for x in filtered]
        pred = max(range(len(scores)), key=lambda i: scores[i])
        pred_norm = max(
            range(len(scores)),
            key=lambda i: scores[i] / variant["choice_char_lengths"][i],
        )
        require(
            metrics
            == {
                "acc": int(pred == payload["gold_index"]),
                "acc_norm": int(pred_norm == payload["gold_index"]),
            },
            "Native metric mismatch",
        )
        return scores, metrics, tokens
