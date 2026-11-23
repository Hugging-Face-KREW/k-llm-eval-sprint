"""Make a copy of the installed lm-evaluation-harness kormedmcqa task whose answer filter first
cuts the response at the task's own stop strings (Q:, </s>, <|im_end|>, ., blank line) and then
runs the ORIGINAL extraction. Needed because API servers may ignore stop strings.

Run once from the folder where you run lm_eval:   python make_stop_task.py
Creates:  custom_tasks\\kormedmcqa_stop\\   (tasks named kormedmcqa_stop_doctor/nurse/pharm/dentist)
"""
import importlib.util
import pathlib
import shutil

spec = importlib.util.find_spec("lm_eval")
src = pathlib.Path(list(spec.submodule_search_locations)[0]) / "tasks" / "kormedmcqa"
dst = pathlib.Path("custom_tasks") / "kormedmcqa_stop"
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
    new = text.replace("task: kormedmcqa_" + subj, "task: kormedmcqa_stop_" + subj)
    if new == text:
        raise SystemExit("could not rename task in %s" % f)
    f.write_text(new, encoding="utf-8")

utils = dst / "utils.py"
extra = '''

# ---- added: cut at the task's stop strings before extraction ----
STOP_STRINGS = ["Q:", "</s>", "<|im_end|>", ".", "\\n\\n"]


def _cut_at_stop(text):
    for s in STOP_STRINGS:
        text = text.split(s)[0]
    return text


class ExtractChoiceFilter(ExtractChoiceFilter):  # same name, so the yaml needs no change
    def apply(self, resps, docs):
        return [[extract_choice(_cut_at_stop(resp)) for resp in r] for r in resps]
'''
utils.write_text(utils.read_text(encoding="utf-8") + extra, encoding="utf-8")
print("done:", dst.resolve())
for p in sorted(dst.iterdir()):
    print("  ", p.name)
