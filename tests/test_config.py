import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_configs_parse_and_inputs_exist():
    for path in ROOT.rglob("*.yml"):
        list(yaml.safe_load_all(path.read_text()))
    for path in ROOT.rglob("*.yaml"):
        list(yaml.safe_load_all(path.read_text()))
    config = yaml.safe_load((ROOT / "kustomization.yaml").read_text())
    for name in config["resources"]:
        assert (ROOT / name).is_file()
    for generator in config["configMapGenerator"]:
        for name in generator["files"]:
            assert (ROOT / name).is_file()
    dashboard = json.loads((ROOT / "monitoring/dashboard.json").read_text())
    assert dashboard["uid"] == "data-observability"
    assert len(dashboard["panels"]) == 6


def test_secrets_are_explicit_opt_in():
    config = yaml.safe_load((ROOT / "kustomization.yaml").read_text())
    assert "k8s/secret.example.yaml" not in config["resources"]
    deployment = yaml.safe_load((ROOT / "k8s/api.yaml").read_text())
    assert deployment["spec"]["replicas"] == 2
    prom = yaml.safe_load((ROOT / "monitoring/prometheus.yml").read_text())
    assert prom["scrape_configs"][0]["kubernetes_sd_configs"][0]["role"] == "pod"
