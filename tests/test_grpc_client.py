"""
Unit tests for grpc_client.py

Teste le client gRPC Tetragon sans connexion réseau réelle (mocks).
"""

import pytest
from unittest.mock import MagicMock, patch, call


# ============================================================================
# Helpers / fixtures
# ============================================================================

def _make_response(event_dict):
    """
    Crée un mock de GetEventsResponse dont MessageToDict renvoie event_dict.
    """
    response = MagicMock()
    return response, event_dict


# ============================================================================
# Initialisation
# ============================================================================

class TestTetragonGRPCClientInit:

    def test_default_address(self):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient()
        assert client.address == "localhost:54321"

    def test_custom_address(self):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient("myhost:1234")
        assert client.address == "myhost:1234"

    def test_not_connected_by_default(self):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient()
        assert client._channel is None
        assert client._stub is None

    def test_custom_event_types(self):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient(event_types=[1, 5])
        assert client.event_types == [1, 5]

    def test_default_event_types_empty(self):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient()
        assert client.event_types == []


# ============================================================================
# connect / close
# ============================================================================

class TestTetragonGRPCClientConnect:

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    def test_connect_opens_channel(self, mock_stub_cls, mock_channel):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient("localhost:54321")
        client.connect()
        mock_channel.assert_called_once_with("localhost:54321")
        assert client._channel is not None

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    def test_connect_creates_stub(self, mock_stub_cls, mock_channel):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient()
        client.connect()
        assert client._stub is not None

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    def test_close_resets_channel_and_stub(self, mock_stub_cls, mock_channel):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient()
        client.connect()
        client.close()
        assert client._channel is None
        assert client._stub is None

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    def test_close_calls_channel_close(self, mock_stub_cls, mock_channel_fn):
        from ingestion.grpc_client import TetragonGRPCClient
        mock_ch = MagicMock()
        mock_channel_fn.return_value = mock_ch
        client = TetragonGRPCClient()
        client.connect()
        client.close()
        mock_ch.close.assert_called_once()

    def test_close_without_connect_does_not_crash(self):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient()
        client.close()  # ne doit pas lever d'exception


# ============================================================================
# stream_events
# ============================================================================

class TestTetragonGRPCClientStreamEvents:

    def test_stream_without_connect_raises(self):
        from ingestion.grpc_client import TetragonGRPCClient
        client = TetragonGRPCClient()
        with pytest.raises(RuntimeError, match="connect()"):
            list(client.stream_events())

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    @patch("ingestion.grpc_client.MessageToDict")
    @patch("ingestion.grpc_client.normalize")
    def test_stream_yields_normalized_events(
        self, mock_normalize, mock_msg2dict, mock_stub_cls, mock_channel
    ):
        from ingestion.grpc_client import TetragonGRPCClient

        # Deux réponses mockées
        resp1, resp2 = MagicMock(), MagicMock()
        mock_stub = MagicMock()
        mock_stub.GetEvents.return_value = iter([resp1, resp2])
        mock_stub_cls.return_value = mock_stub

        mock_msg2dict.side_effect = [{"processExec": {}}, {"processExit": {}}]
        mock_normalize.side_effect = [
            {"event_type": "process_exec", "pid": 1},
            {"event_type": "process_exit", "pid": 1},
        ]

        client = TetragonGRPCClient()
        client.connect()
        results = list(client.stream_events())

        assert len(results) == 2
        assert results[0]["event_type"] == "process_exec"
        assert results[1]["event_type"] == "process_exit"

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    @patch("ingestion.grpc_client.MessageToDict")
    @patch("ingestion.grpc_client.normalize")
    def test_stream_skips_none_events(
        self, mock_normalize, mock_msg2dict, mock_stub_cls, mock_channel
    ):
        from ingestion.grpc_client import TetragonGRPCClient

        mock_stub = MagicMock()
        mock_stub.GetEvents.return_value = iter([MagicMock(), MagicMock()])
        mock_stub_cls.return_value = mock_stub

        mock_msg2dict.return_value = {}
        # normalize renvoie None pour les deux → rien ne doit être yielded
        mock_normalize.return_value = None

        client = TetragonGRPCClient()
        client.connect()
        results = list(client.stream_events())
        assert results == []

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    @patch("ingestion.grpc_client.MessageToDict")
    @patch("ingestion.grpc_client.normalize")
    def test_stream_skips_on_processing_error(
        self, mock_normalize, mock_msg2dict, mock_stub_cls, mock_channel
    ):
        from ingestion.grpc_client import TetragonGRPCClient

        mock_stub = MagicMock()
        mock_stub.GetEvents.return_value = iter([MagicMock()])
        mock_stub_cls.return_value = mock_stub

        # MessageToDict lève une exception
        mock_msg2dict.side_effect = Exception("protobuf error")

        client = TetragonGRPCClient()
        client.connect()
        # Ne doit pas lever, doit juste produire 0 résultats
        results = list(client.stream_events())
        assert results == []


# ============================================================================
# Context manager
# ============================================================================

class TestTetragonGRPCClientContextManager:

    @patch("ingestion.grpc_client.grpc.insecure_channel")
    @patch("ingestion.grpc_client.tetragon_pb2_grpc.FineGuidanceSensorsStub")
    def test_context_manager_calls_connect_and_close(
        self, mock_stub_cls, mock_channel_fn
    ):
        from ingestion.grpc_client import TetragonGRPCClient

        mock_ch = MagicMock()
        mock_channel_fn.return_value = mock_ch

        with TetragonGRPCClient() as client:
            assert client._stub is not None

        # close() doit avoir été appelé
        mock_ch.close.assert_called_once()


# ============================================================================
# process_grpc_stream sur EventCollector
# ============================================================================

class TestCollectorProcessGrpcStream:

    @patch("ingestion.collector.TetragonGRPCClient")
    def test_process_grpc_stream_dispatches_events(self, mock_client_cls):
        from ingestion import EventCollector

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream_events.return_value = iter([
            {"event_type": "process_exec", "pid": 100, "parent_pid": 1,
             "comm": "bash", "uid": 0, "gid": 0},
            {"event_type": "process_exit", "pid": 100, "uid": 0},
        ])
        mock_client_cls.return_value = mock_client

        collector = EventCollector()
        count = collector.process_grpc_stream("localhost:54321")

        assert count == 2
        assert collector.error_count == 0

    @patch("ingestion.collector.TetragonGRPCClient")
    def test_process_grpc_stream_uses_env_address(self, mock_client_cls, monkeypatch):
        from ingestion import EventCollector

        monkeypatch.setenv("TETRAGON_GRPC_ADDRESS", "myhost:9999")

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream_events.return_value = iter([])
        mock_client_cls.return_value = mock_client

        EventCollector().process_grpc_stream()
        mock_client_cls.assert_called_once_with("myhost:9999")

    @patch("ingestion.collector.TetragonGRPCClient")
    def test_process_grpc_stream_default_address(self, mock_client_cls, monkeypatch):
        from ingestion import EventCollector

        monkeypatch.delenv("TETRAGON_GRPC_ADDRESS", raising=False)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream_events.return_value = iter([])
        mock_client_cls.return_value = mock_client

        EventCollector().process_grpc_stream()
        mock_client_cls.assert_called_once_with("localhost:54321")

    @patch("ingestion.collector.TetragonGRPCClient")
    def test_process_grpc_stream_handles_grpc_error(self, mock_client_cls):
        from ingestion import EventCollector
        import grpc

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.stream_events.side_effect = Exception("connection refused")
        mock_client_cls.return_value = mock_client

        collector = EventCollector()
        count = collector.process_grpc_stream()
        # Doit retourner 0 sans lever d'exception
        assert count == 0
        assert collector.error_count == 1
