"""
Thread-safe checkpoint manager for resumable evaluation runs.
Saves results to JSON after each problem, enabling interrupt/resume.
"""

import json
import os
import threading


class CheckpointManager:
    def __init__(self, checkpoint_path: str):
        self.path = checkpoint_path
        self._lock = threading.Lock()
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"results": {}, "metadata": {}}

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def is_done(self, problem_id: str, stage: str) -> bool:
        with self._lock:
            return self.data["results"].get(problem_id, {}).get(stage) is not None

    def get_result(self, problem_id: str, stage: str):
        with self._lock:
            return self.data["results"].get(problem_id, {}).get(stage)

    def set_result(self, problem_id: str, stage: str, value):
        with self._lock:
            if problem_id not in self.data["results"]:
                self.data["results"][problem_id] = {}
            self.data["results"][problem_id][stage] = value
            self.save()

    def set_metadata(self, key, value):
        with self._lock:
            self.data["metadata"][key] = value
            self.save()

    @property
    def results(self):
        return self.data["results"]

    @property
    def metadata(self):
        return self.data["metadata"]
