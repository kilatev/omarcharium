from __future__ import annotations

import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from scripts.ecosystem_checkpoint import CheckpointStore
from scripts.ecosystem_model import Model, initial_model, model_from_json, model_to_json
from scripts.ecosystem_service import EcosystemService, ServiceProtocolError, ServiceRuntime


class FakeStore:
    def __init__(self, model: Model) -> None:
        self.model = model
        self.loads = 0
        self.writes: list[Model] = []

    def load(self) -> Model:
        self.loads += 1
        return self.model

    def checkpoint(self, model: Model) -> None:
        self.writes.append(model)


class EcosystemServiceTests(unittest.TestCase):
    def test_elapsed_time_advances_fixed_ticks_and_coalesces_checkpoints(self) -> None:
        store = FakeStore(initial_model(3))
        service = EcosystemService(store, tick_interval=1.0, clock=lambda: 0.0)
        service.start(0)
        self.assertEqual(service.advance(0.9), 0)
        self.assertEqual(service.advance(2.9), 2)
        self.assertEqual(service.model.tick, 2)
        self.assertEqual(store.loads, 1)
        self.assertEqual(store.writes, [])
        self.assertEqual(service.snapshot(), model_to_json(service.model))
        self.assertEqual(store.loads, 1)

    def test_public_operations_are_safe_and_force_durable_events(self) -> None:
        store = FakeStore(initial_model(3))
        service = EcosystemService(store, clock=lambda: 10.0)
        reset_response = service.handle_request({"operation": "reset", "seed": 42})
        self.assertTrue(reset_response["ok"])
        self.assertEqual(service.model.seed, 42)
        self.assertEqual(len(store.writes), 1)
        service.handle_request({"operation": "settings", "settings": {"food_abundance": 1.5}})
        self.assertEqual(service.model.settings["food_abundance"], 1.5)
        self.assertEqual(len(store.writes), 2)
        service.handle_request({"operation": "settings", "settings": {
            "enabled": False, "simulation_speed": 4.0, "mutation_rate": 0.25,
            "diagnostic_accelerated": True,
        }})
        self.assertFalse(service.simulation_enabled)
        self.assertEqual(service.simulation_speed, 4.0)
        self.assertTrue(service.diagnostic_accelerated)
        self.assertEqual(service.model.settings["mutation_rate"], 0.25)
        self.assertTrue(service.handle_request({"operation": "save"})["saved"])
        self.assertEqual(len(store.writes), 4)

        for request in (None, {"operation": "unknown"}, {"operation": "reset", "seed": True}):
            with self.assertRaises(ServiceProtocolError):
                service.handle_request(request)

    def test_snapshot_protocol_reads_model_memory_and_sets_private_socket(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "ecosystem.json"
            store = CheckpointStore(path, model_to_json, model_from_json, lambda: initial_model(7))
            service = EcosystemService(store, clock=lambda: 0.0)
            socket_path = root / "run" / "ecosystem.sock"
            lock_path = root / "run" / "ecosystem.lock"
            with ServiceRuntime(service, socket_path, lock_path) as runtime:
                handler = threading.Thread(target=runtime.handle_once)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    handler.start()
                    client.connect(str(socket_path))
                    client.sendall(b'{"operation":"snapshot"}\n')
                    response = json.loads(client.makefile("rb").readline())
                handler.join(timeout=2)
                self.assertFalse(handler.is_alive())
            self.assertTrue(response["ok"])
            self.assertEqual(response["snapshot"], model_to_json(service.model))

    def test_restart_recovers_checkpoint_and_runtime_enforces_one_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "state" / "ecosystem.json"
            store = CheckpointStore(path, model_to_json, model_from_json, lambda: initial_model(7))
            service = EcosystemService(store, clock=lambda: 1.0)
            service.reset(99)
            recovered = EcosystemService(store, clock=lambda: 1.0)
            self.assertEqual(recovered.model, service.model)
            socket_path = root / "run" / "ecosystem.sock"
            lock_path = root / "run" / "ecosystem.lock"
            with ServiceRuntime(recovered, socket_path, lock_path):
                with self.assertRaises(RuntimeError):
                    with ServiceRuntime(EcosystemService(store), socket_path, lock_path):
                        pass


if __name__ == "__main__":
    unittest.main()
