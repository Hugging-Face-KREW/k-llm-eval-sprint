"""Make a copy of the installed lm-evaluation-harness kormedmcqa task that is UNCHANGED except for
(1) the task names (kormedmcqa_orig_doctor/nurse/pharm/dentist, so they do not clash with the built-in ones) and
(2) the OpenRouter provider pin (DeepInfra, no fallback) added to generation_kwargs.
The prompt, few-shot, answer filter (extraction) and stop strings stay exactly as in the installed original.

Run once from the folder where you run lm_eval:   python make_original_task.py
Creates:  custom_tasks\\kormedmcqa_orig\\
"""
import importlib.util
import pathlib
import shutil

spec = importlib.util.find_spec("lm_eval")
src = pathlib.Path(list(spec.submodule_search_locations)[0]) / "tasks" / "kormedmcqa"
dst = pathlib.Path("custom_tasks") / "kormedmcqa_orig"
if not src.is_dir():
    raise SystemExit("task folder not found: %s" % src)
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst)

group = dst / "_kormedmcqa.yaml"
if group.exists():
    group.unlink()

for subj in ["doctor", "nurse", "pharm", "dentist"]:
    f = dst / (subj + ".yaml")
    text = f.read_text(encoding="utf-8")
    new = text.replace("task: kormedmcqa_" + subj, "task: kormedmcqa_orig_" + subj)
    if new == text:
        raise SystemExit("could not rename task in %s" % f)
    f.write_text(new, encoding="utf-8")

tpl = dst / "_template_yaml"
t = tpl.read_text(encoding="utf-8")
old = "  max_gen_toks: 1024\n"
if old not in t:
    raise SystemExit("max_gen_toks line not found in _template_yaml")
tpl.write_text(t.replace(old, old + "  provider:\n    order:\n      - DeepInfra\n    allow_fallbacks: false\n"), encoding="utf-8")
print("done:", dst.resolve())
for p in sorted(dst.iterdir()):
    print("  ", p.name)
