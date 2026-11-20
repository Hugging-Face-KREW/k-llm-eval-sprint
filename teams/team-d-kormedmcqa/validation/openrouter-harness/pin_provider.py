"""Pin the OpenRouter provider (DeepInfra) in the custom task yaml. Run AFTER the gpt-4o-mini run and BEFORE the Llama runs."""
import pathlib

p = pathlib.Path("custom_tasks") / "kormedmcqa_stop" / "_template_yaml"
t = p.read_text(encoding="utf-8")
if "provider:" in t:
    raise SystemExit("already pinned")
old = "  max_gen_toks: 1024\n"
if old not in t:
    raise SystemExit("max_gen_toks line not found")
new = old + "  provider:\n    order:\n      - DeepInfra\n    allow_fallbacks: false\n"
p.write_text(t.replace(old, new), encoding="utf-8")
print("pinned to DeepInfra:", p)
