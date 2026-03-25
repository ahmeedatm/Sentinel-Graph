"""
Tetragon gRPC Client
====================

Client gRPC qui se connecte au serveur Tetragon et retourne un flux
d'événements normalisés au format interne du collector.

Architecture :
    Tetragon gRPC (port 54321)
        → GetEventsResponse (protobuf)
        → MessageToDict (protobuf → dict camelCase)
        → tetragon_adapter.normalize (camelCase → snake_case)
        → Dict interne → EventCollector.dispatch_event()

Usage :
    client = TetragonGRPCClient("localhost:54321")
    client.connect()
    for event in client.stream_events():
        collector.dispatch_event(event)
    client.close()

Pré-requis :
    Les stubs protobuf doivent être générés :
    python -m grpc_tools.protoc \\
        -I src/ingestion/proto \\
        --python_out=src/ingestion/proto \\
        --grpc_python_out=src/ingestion/proto \\
        src/ingestion/proto/tetragon.proto

En Kubernetes :
    kubectl port-forward -n kube-system svc/tetragon 54321:54321
"""

import logging
from typing import Iterator, Dict, Any, Optional

import grpc
from google.protobuf.json_format import MessageToDict

try:
    from .proto import tetragon_pb2, tetragon_pb2_grpc
    from .tetragon_adapter import normalize
except ImportError:
    from proto import tetragon_pb2, tetragon_pb2_grpc  # type: ignore[no-redef]
    from tetragon_adapter import normalize              # type: ignore[no-redef]

logger = logging.getLogger(__name__)

# Timeout de reconnexion en secondes
_RECONNECT_DELAY_S = 5


class TetragonGRPCClient:
    """
    Client gRPC pour le serveur Tetragon.

    Attributes:
        address: Adresse gRPC du serveur Tetragon (host:port)
        event_types: Filtre optionnel sur les types d'événements à recevoir.
                     None = tous les événements.
    """

    def __init__(
        self,
        address: str = "localhost:54321",
        event_types: Optional[list] = None,
    ):
        """
        Args:
            address: Adresse du serveur gRPC Tetragon, ex: "localhost:54321"
            event_types: Liste de constantes EventType du proto à filtrer.
                         Ex: [tetragon_pb2.PROCESS_EXEC, tetragon_pb2.PROCESS_EXIT]
                         Si None, tous les événements sont reçus.
        """
        self.address = address
        self.event_types = event_types or []
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[tetragon_pb2_grpc.FineGuidanceSensorsStub] = None

    def connect(self) -> None:
        """Ouvre le canal gRPC vers Tetragon."""
        logger.info("Connexion gRPC à Tetragon: %s", self.address)
        self._channel = grpc.insecure_channel(self.address)
        self._stub = tetragon_pb2_grpc.FineGuidanceSensorsStub(self._channel)
        logger.info("Canal gRPC ouvert")

    def close(self) -> None:
        """Ferme le canal gRPC proprement."""
        if self._channel is not None:
            self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("Canal gRPC fermé")

    def stream_events(self) -> Iterator[Dict[str, Any]]:
        """
        Ouvre le flux gRPC GetEvents et yield les événements normalisés.

        Chaque élément yielded est un dict au format interne :
            {"event_type": "process_exec", "pid": 123, ...}

        Les événements non supportés (type inconnu, champs manquants)
        sont silencieusement ignorés.

        Yields:
            Dict au format interne attendu par EventCollector.dispatch_event()

        Raises:
            grpc.RpcError: Si la connexion au serveur échoue.
            RuntimeError: Si connect() n'a pas été appelé.
        """
        if self._stub is None:
            raise RuntimeError(
                "Client non connecté. Appeler connect() avant stream_events()."
            )

        request = self._build_request()
        logger.info(
            "Début du streaming gRPC depuis %s (filtres: %s)",
            self.address,
            self.event_types or "tous",
        )

        for response in self._stub.GetEvents(request):
            normalized = self._process_response(response)
            if normalized is not None:
                yield normalized

    def __enter__(self) -> "TetragonGRPCClient":
        """Support du context manager : with TetragonGRPCClient(...) as c:"""
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ========================================================================
    # Méthodes internes
    # ========================================================================

    def _build_request(self) -> tetragon_pb2.GetEventsRequest:
        """Construit la requête GetEvents avec le filtre de types."""
        request = tetragon_pb2.GetEventsRequest()
        for event_type in self.event_types:
            request.allow_list.append(event_type)
        return request

    def _process_response(
        self, response: tetragon_pb2.GetEventsResponse
    ) -> Optional[Dict[str, Any]]:
        """
        Convertit une GetEventsResponse protobuf en dict interne.

        Étapes :
          1. MessageToDict → dict camelCase (format Tetragon)
          2. tetragon_adapter.normalize → dict snake_case (format interne)
        """
        try:
            event_dict = MessageToDict(
                response,
                preserving_proto_field_name=False,  # camelCase (défaut MessageToDict)
                including_default_value_fields=False,
            )
            return normalize(event_dict)
        except Exception as exc:
            logger.error("Erreur lors du traitement d'un événement gRPC: %s", exc)
            return None
