import importlib

modules = [
    "config",
    "crew",
    "engine.data_layer",
    "engine.regime",
    "agents.analyst",
    "agents.risk_manager",
    "agents.auditor",
    "zkml.proof_generator",
    "zkml.merkle_chain",
    "dashboard.gateway",
]

for name in modules:
    try:
        importlib.import_module(name)
        print(f"OK {name}")
    except Exception as exc:
        print(f"FAIL {name}: {type(exc).__name__}: {exc}")
