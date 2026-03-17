"""
Analysis Module (L'Analyste)
==============================

Behavioral anomaly detection engine for Sentinel-Graph.

Modules:
  - baseline.py:  BaselineLearner — builds behavioral profiles from snapshots
  - detector.py:  AnomalyDetector — compares live snapshots against baseline

Workflow:
  1. Feed SystemGraph snapshots to BaselineLearner.learn() during normal ops
  2. Save the profile with BaselineLearner.save()
  3. Reload with BaselineLearner.load() and pass to AnomalyDetector
  4. Call AnomalyDetector.detect(snapshot) to get a list of Alert objects

Example::

    from analysis import BaselineLearner, AnomalyDetector

    learner = BaselineLearner()
    learner.learn(snapshot)
    learner.save()

    detector = AnomalyDetector(learner)
    alerts = detector.detect(live_snapshot)
"""

from .baseline import BaselineLearner
from .detector import AnomalyDetector, Alert

__all__ = ["BaselineLearner", "AnomalyDetector", "Alert"]
