from netprobe.cli import exit_code, main, render_text
from netprobe.probes import ProbeResult


def test_render_text_includes_status_and_details():
    output = render_text([ProbeResult("dns", "ok", "resolved localhost", {"addresses": ["127.0.0.1"]})])

    assert "[OK] dns: resolved localhost" in output
    assert "addresses: ['127.0.0.1']" in output


def test_exit_code_fails_when_any_probe_fails():
    results = [
        ProbeResult("dns", "ok", "resolved", {}),
        ProbeResult("tcp", "fail", "connection refused", {}),
    ]

    assert exit_code(results) == 1


def test_main_json_output(monkeypatch, capsys):
    def fake_diagnose(target, prometheus_url, samples, timeout_seconds):
        assert target == "http://localhost:8080"
        assert prometheus_url == "http://localhost:9090"
        assert samples == 1
        assert timeout_seconds == 1
        return [ProbeResult("dns", "ok", "resolved", {"addresses": ["127.0.0.1"]})]

    monkeypatch.setattr("netprobe.cli.diagnose", fake_diagnose)

    code = main(["diagnose", "--samples", "1", "--timeout", "1", "--json"])

    assert code == 0
    assert '"name": "dns"' in capsys.readouterr().out
